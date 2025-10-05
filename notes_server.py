"""
Simple Note-Taking MCP Server
==============================
This is a complete, working MCP (Model Context Protocol) server that lets Claude
create, read, update, and delete notes stored in a local JSON file.

What is MCP?
- MCP is a protocol that lets Claude interact with external tools and data
- This server runs on your computer and Claude Desktop connects to it
- Claude can call the "tools" we define here to perform actions

How it works:
1. This server defines "tools" (functions Claude can call)
2. Claude Desktop communicates with this server via stdin/stdout
3. When you ask Claude to work with notes, it calls our tools
4. We execute the action and return results to Claude
"""

import asyncio  # For asynchronous programming (MCP requires this)
import json  # For reading/writing our notes database
import os  # For file system operations
from pathlib import Path  # For easier file path handling
from typing import Any  # For type hints

# Import MCP SDK components
# These are the building blocks for creating an MCP server
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server  # For communication with Claude Desktop
from mcp.types import (
    Tool,  # Represents a tool/function Claude can call
    TextContent,  # For returning text results to Claude
)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

# Where we'll store our notes (in your home directory)
NOTES_FILE = Path.home() / "claude_notes.json"

# ==============================================================================
# NOTES DATABASE FUNCTIONS
# ==============================================================================

def load_notes() -> dict:
    """
    Load notes from the JSON file.
    
    Returns:
        dict: Dictionary of notes where keys are note IDs and values are note content
        
    If the file doesn't exist, we return an empty dictionary.
    """
    if NOTES_FILE.exists():
        with open(NOTES_FILE, 'r') as f:
            return json.load(f)
    return {}  # Return empty dict if file doesn't exist yet


def save_notes(notes: dict) -> None:
    """
    Save notes to the JSON file.
    
    Args:
        notes: Dictionary of notes to save
        
    We write with indent=2 to make the JSON file human-readable.
    """
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2)


# ==============================================================================
# MCP SERVER SETUP
# ==============================================================================

# Create our MCP server instance with a unique name
# This name identifies our server to Claude Desktop
server = Server("simple-notes-server")


# ==============================================================================
# TOOL DEFINITIONS
# ==============================================================================

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    Tell Claude what tools are available.
    
    This function is called when Claude Desktop starts up and asks:
    "What can this server do?"
    
    Returns:
        list[Tool]: List of available tools with their schemas
        
    Each tool needs:
    - name: What Claude calls to use this tool
    - description: What the tool does (helps Claude decide when to use it)
    - inputSchema: JSON Schema defining what parameters the tool accepts
    """
    return [
        # Tool 1: Create a new note
        Tool(
            name="create_note",
            description="Create a new note with a title and content",
            inputSchema={
                "type": "object",  # We expect an object with properties
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the note (used as the ID)",
                    },
                    "content": {
                        "type": "string",
                        "description": "The note content/body",
                    }
                },
                "required": ["title", "content"],  # Both fields are mandatory
            },
        ),
        
        # Tool 2: Read an existing note
        Tool(
            name="read_note",
            description="Read a note by its title",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the note to read",
                    }
                },
                "required": ["title"],
            },
        ),
        
        # Tool 3: List all note titles
        Tool(
            name="list_notes",
            description="List all available note titles",
            inputSchema={
                "type": "object",
                "properties": {},  # No parameters needed for listing
            },
        ),
        
        # Tool 4: Update an existing note
        Tool(
            name="update_note",
            description="Update the content of an existing note",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the note to update",
                    },
                    "content": {
                        "type": "string",
                        "description": "New content for the note",
                    }
                },
                "required": ["title", "content"],
            },
        ),
        
        # Tool 5: Delete a note
        Tool(
            name="delete_note",
            description="Delete a note by its title",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the note to delete",
                    }
                },
                "required": ["title"],
            },
        ),
    ]


# ==============================================================================
# TOOL EXECUTION
# ==============================================================================

@server.call_tool()
async def handle_call_tool(
    name: str,  # Which tool Claude wants to use
    arguments: dict[str, Any]  # The parameters Claude is passing
) -> list[TextContent]:
    """
    Execute a tool when Claude calls it.
    
    This is the heart of your MCP server. When Claude decides to use one of
    your tools, this function is called with the tool name and arguments.
    
    Args:
        name: The name of the tool to execute (e.g., "create_note")
        arguments: Dictionary of parameters (e.g., {"title": "Shopping", "content": "..."})
        
    Returns:
        list[TextContent]: Results to send back to Claude
        
    We return a list of TextContent objects - usually just one with our result message.
    """
    
    # Load current notes from disk
    notes = load_notes()
    
    # Handle each tool differently based on its name
    if name == "create_note":
        # Extract the parameters Claude sent
        title = arguments["title"]
        content = arguments["content"]
        
        # Check if a note with this title already exists
        if title in notes:
            return [TextContent(
                type="text",
                text=f"Error: A note with title '{title}' already exists. Use update_note to modify it."
            )]
        
        # Create the new note
        notes[title] = content
        save_notes(notes)
        
        return [TextContent(
            type="text",
            text=f"Successfully created note '{title}'"
        )]
    
    elif name == "read_note":
        title = arguments["title"]
        
        # Check if the note exists
        if title not in notes:
            return [TextContent(
                type="text",
                text=f"Error: No note found with title '{title}'"
            )]
        
        # Return the note content
        return [TextContent(
            type="text",
            text=f"Note '{title}':\n\n{notes[title]}"
        )]
    
    elif name == "list_notes":
        # Check if there are any notes
        if not notes:
            return [TextContent(
                type="text",
                text="No notes found. Create your first note!"
            )]
        
        # Create a formatted list of all note titles
        note_list = "\n".join(f"- {title}" for title in notes.keys())
        return [TextContent(
            type="text",
            text=f"Available notes ({len(notes)}):\n{note_list}"
        )]
    
    elif name == "update_note":
        title = arguments["title"]
        content = arguments["content"]
        
        # Check if the note exists
        if title not in notes:
            return [TextContent(
                type="text",
                text=f"Error: No note found with title '{title}'. Use create_note to make a new one."
            )]
        
        # Update the note
        notes[title] = content
        save_notes(notes)
        
        return [TextContent(
            type="text",
            text=f"Successfully updated note '{title}'"
        )]
    
    elif name == "delete_note":
        title = arguments["title"]
        
        # Check if the note exists
        if title not in notes:
            return [TextContent(
                type="text",
                text=f"Error: No note found with title '{title}'"
            )]
        
        # Delete the note
        del notes[title]
        save_notes(notes)
        
        return [TextContent(
            type="text",
            text=f"Successfully deleted note '{title}'"
        )]
    
    else:
        # This shouldn't happen, but handle unknown tools gracefully
        raise ValueError(f"Unknown tool: {name}")


# ==============================================================================
# SERVER STARTUP
# ==============================================================================

async def main():
    """
    Main function that starts the MCP server.
    
    This function:
    1. Sets up stdio communication (how Claude Desktop talks to us)
    2. Initializes the server with its capabilities
    3. Runs the server (waits for requests from Claude)
    
    The server runs forever until Claude Desktop disconnects.
    """
    
    # stdio_server() sets up communication via standard input/output
    # This is how Claude Desktop sends requests and receives responses
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,  # Where we read requests from Claude
            write_stream,  # Where we send responses to Claude
            InitializationOptions(
                server_name="simple-notes-server",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


# ==============================================================================
# ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    """
    This runs when you execute the script directly.
    
    asyncio.run() starts the async event loop and runs our main() function.
    MCP requires async/await because it handles multiple requests concurrently.
    """
    asyncio.run(main())


# ==============================================================================
# SETUP INSTRUCTIONS
# ==============================================================================
"""
TO USE THIS MCP SERVER:

1. Install the MCP Python SDK:
   pip install mcp

2. Save this file as: notes_server.py

3. Edit your Claude Desktop config file:
   - macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
   - Windows: %APPDATA%\\Claude\\claude_desktop_config.json
   - Linux: ~/.config/Claude/claude_desktop_config.json

4. Add this to the config file:
   {
     "mcpServers": {
       "notes": {
         "command": "python",
         "args": ["/full/path/to/notes_server.py"]
       }
     }
   }
   
   Replace /full/path/to/notes_server.py with the actual path where you saved this file.

5. Restart Claude Desktop

6. Try asking Claude:
   - "Create a note called 'Shopping' with some items"
   - "List all my notes"
   - "Read my Shopping note"
   - "Update my Shopping note to add bread"
   - "Delete my Shopping note"

NOTES STORAGE:
- Your notes are saved to: ~/claude_notes.json
- This is a simple JSON file you can also edit manually
- Each note has a title (key) and content (value)
"""