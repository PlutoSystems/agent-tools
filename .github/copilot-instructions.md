## Overview

You are are a coding assistant for Pluto Systems. This repository is a shared location for MCP server and tools that help with various agents and automated workflows across the Pluto company's internal tools.

## Guidelines

- Write everything in python. Follow best practices but keep code succinct, avoid excessive error handling
- Don't add comments unless absolutely necessary
- IF you are saving MCP auth credentials or other transient data, save to the .local/ folder
- New tools should always be in the /src/tools folder, make sure they can be tested by running them directly with CLI arguments corresponding to their exposed tool args
