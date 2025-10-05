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

# ==============================================================================
# SETUP INSTRUCTIONS
# ==============================================================================

# TO USE THIS MCP SERVER:

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

## NOTES STORAGE:
- Your notes are saved to: ~/claude_notes.json
- This is a simple JSON file you can also edit manually
- Each note has a title (key) and content (value)
"""
