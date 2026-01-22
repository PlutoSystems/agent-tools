from mcp.server.fastmcp import FastMCP
from tools.transcript_fetch import fetch_transcript

# Create the server
mcp = FastMCP("Pluto Shared MCP Tools")


@mcp.tool()
def fetch_transcript(join_url: str, output_path: str) -> str:
    """
    Downloads and saves a Microsoft Teams meeting transcript.

    This tool authenticates with Microsoft Graph API (requires interactive browser
    authentication on first use), retrieves the meeting transcript, cleans the VTT
    format to plain text with speaker names, and saves it to the specified path.

    Args:
        join_url: The Teams meeting Join Web URL (e.g., from meeting invite or calendar)
        output_path: Absolute file path where the cleaned transcript should be saved (e.g.,
                    'C:/Users/user/Desktop/meeting.txt'). Parent directories will be created if needed.

    Returns:
        Success message with the saved file path, or error message if the operation fails.

    Notes:
        - Requires MS_CLIENT_ID in .env file
        - Auth credentials are cached in .local/auth_record.json for subsequent runs
    """
    try:
        content = fetch_transcript(join_url, output_path)
        return content
    except Exception as e:
        return f"Error: {str(e)}"


if __name__ == "__main__":
    mcp.run()
