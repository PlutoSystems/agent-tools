## Overview

You are are a coding assistant for Pluto Systems. This repository is a shared location for MCP server and tools that help with various agents and automated workflows across the Pluto company's internal tools. This package uses 'uv' tool for python package management, so make sure your CLI commands use 'uv' instead of 'pip' or 'python -m venv' etc. For example, to install a new package, run 'uv add <package-name>'.

## Guidelines

- Write everything in python. Follow best practices but keep code succinct, avoid excessive error handling
- Don't add comments unless absolutely necessary
- IF you are saving MCP auth credentials or other transient data, save to the .local/ folder
- New tools should always be in the /src/tools folder, make sure they can be tested by running them directly with CLI arguments corresponding to their exposed tool args

## Python Writing

- pylance is in standard mode, so always include '| None' for optional args with default None
- Use `list[dict[str, Any]]` or similar explicit type hints for complex nested structures to avoid Pylance errors
