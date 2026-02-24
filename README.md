# Agent Tools

Shared MCP server providing tools for Pluto agents. Can be added as a Git submodule for active development, or just use relative import paths with this repo cloned somewhere on your local machine.

## Setup

```bash
# Add as submodule in your project
git submodule add <repository-url> agent-tools
git submodule update --init --recursive

# Install dependencies (requires Python 3.12+)
cd agent-tools
uv sync
```

Create a `.env` file in the `agent-tools` directory:

```env
MS_CLIENT_ID=5997af4b-e6c7-4a97-8fd9-963df073f60b
LOCAL_STORE_PATH=<absolute-path-to-agent-tools>/.local
```

## MCP Configuration

Add to `.vscode/mcp.json` in your project:

```json
{
    "servers": {
        "pluto-tools": {
            "command": "../agent-tools/.venv/Scripts/python.exe",
            "args": ["../agent-tools/src/mcp_server.py"],
            "type": "stdio"
        }
    }
}
```

### Excluding Tool Groups

Use `--exclude <group>` to disable tool groups you don't need. Multiple excludes can be chained.

```json
{
    "servers": {
        "pluto-tools": {
            "command": "../agent-tools/.venv/Scripts/python.exe",
            "args": ["../agent-tools/src/mcp_server.py", "--exclude", "hubspot"],
            "type": "stdio"
        }
    }
}
```

| Group     | Tools                                                                                 |
| --------- | ------------------------------------------------------------------------------------- |
| `hubspot` | All HubSpot CRM tools (contacts, companies, projects, notes, calls, meetings, emails) |

## Available Tools

**General:**

- `parse_email_file` — Parse `.msg` email files (sender, recipients, subject, body, attachments)
- `fetch_transcript_tool` — Download and clean Microsoft Teams meeting transcripts

**HubSpot CRM** (excludable with `--exclude hubspot`):

- Search, get, create, update contacts and companies
- Search, get, create, update projects (deals)
- Add notes, log calls, log meetings
- Search emails, calls, meetings, notes
- List HubSpot users

## Notes

- First run of transcript tool opens a browser for Microsoft auth; credentials are cached in `.local/`
- HubSpot tools require `HUBSPOT_ACCESS_TOKEN` in `.env`
- Files in `.env`, `.venv`, `.local`, and `__pycache__` are gitignored
