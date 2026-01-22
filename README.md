# Agent Tools

MCP server providing shared tools for Pluto agent applications. This repository is designed to be used as a Git submodule in multiple agent projects.

## Setup Instructions

### 1. Add as Submodule

In your parent agent repository, add this as a submodule:

```bash
git submodule add <repository-url> agent-tools
git submodule update --init --recursive
```

### 2. Install Dependencies

Ensure Python 3.12+ is installed (required for compatibility with certain libraries). Then install dependencies using uv:

```bash
cd agent-tools
uv sync
```

This automatically creates a virtual environment and installs all required packages.

### 3. Configuration

Create a `.env` file in the `agent-tools` directory:

```env
MS_CLIENT_ID=5997af4b-e6c7-4a97-8fd9-963df073f60b
LOCAL_STORE_PATH=<absolute-path-to-agent-tools>/.local
```

**Required:**

- `MS_CLIENT_ID`: Azure AD application client ID (already configured in Azure)
- `LOCAL_STORE_PATH`: Absolute path where authentication tokens will be cached (e.g., `C:/pluto/my-agent/agent-tools/.local`)

### 4. First Run Authentication

On first use, the tool will open a browser for interactive Microsoft authentication. Credentials are cached in `.local/ms_auth_record.json` for subsequent runs.

## Files Not Committed (per .gitignore)

- `.env` - Environment variables (create per deployment)
- `.venv` - Virtual environment
- `.local` - Cached authentication tokens
- `__pycache__` and other Python build artifacts
