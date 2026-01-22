import sys
import os
import json
import re
import requests
import urllib.parse
from dotenv import load_dotenv
from azure.identity import (
    InteractiveBrowserCredential,
    TokenCachePersistenceOptions,
    AuthenticationRecord,
)

load_dotenv()

AUTH_RECORD_PATH = ".local/auth_record.json"
CLIENT_ID = os.getenv("MS_CLIENT_ID")
SCOPES = [
    "https://graph.microsoft.com/OnlineMeetings.Read",
    "https://graph.microsoft.com/OnlineMeetingTranscript.Read.All",
]


def get_silent_credential():
    # 1. Setup Cache Options
    cache_options = TokenCachePersistenceOptions(allow_unencrypted_storage=True)

    auth_record = None

    # 2. Try to load the "ID Card" from disk
    if os.path.exists(AUTH_RECORD_PATH):
        print(f"DEBUG: Found {AUTH_RECORD_PATH}, loading user identity...")
        try:
            with open(AUTH_RECORD_PATH, "r") as f:
                json_record = json.load(f)
                auth_record = AuthenticationRecord.deserialize(json_record)
        except Exception as e:
            print(f"DEBUG: Failed to load auth record: {e}")

    # 3. Create the Credential
    # If we pass 'authentication_record', it attempts silent login first
    credential = InteractiveBrowserCredential(
        client_id=CLIENT_ID,
        cache_persistence_options=cache_options,
        authentication_record=auth_record,
    )

    return credential


def fetch_transcript(join_web_url, output_path) -> str:
    print(f"--- Authenticating ---")
    credential = get_silent_credential()

    print("DEBUG: Attempting to get token from cache or authenticate...")
    token_obj = credential.get_token(*SCOPES)
    access_token = token_obj.token

    record = credential.authenticate(scopes=SCOPES)
    with open(AUTH_RECORD_PATH, "w") as f:
        json.dump(record.serialize(), f)
        print(f"DEBUG: Saved user identity to {AUTH_RECORD_PATH}")

    headers = {
        "Authorization": f"Bearer {access_token}",
        # Accept header is mandatory for VTT
    }

    print("1. Resolving Meeting ID...")
    encoded_url = urllib.parse.quote(join_web_url)
    base_url = "https://graph.microsoft.com/v1.0"

    # Get Meeting ID
    lookup_url = f"{base_url}/me/onlineMeetings?$filter=JoinWebUrl eq '{encoded_url}'"
    resp = requests.get(lookup_url, headers=headers)

    if not resp.ok:
        return f"Error finding meeting: {resp.text}"

    data = resp.json()
    if not data["value"]:
        return "No meeting found for this Join URL."

    meeting_id = data["value"][0]["id"]
    meeting_subject = data["value"][0].get("subject", "Unknown Meeting")

    # Get Transcript ID
    print("2. Fetching Transcript List...")
    transcripts_url = f"{base_url}/me/onlineMeetings/{meeting_id}/transcripts"
    resp = requests.get(transcripts_url, headers=headers)

    transcripts = resp.json().get("value", [])
    if not transcripts:
        return "No transcripts available."

    transcript_id = transcripts[0]["id"]

    # Download
    print("3. Downloading Content...")
    content_url = (
        f"{base_url}/me/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
    )
    vtt_headers = headers.copy()
    vtt_headers["Accept"] = "text/vtt"
    resp = requests.get(content_url, headers=vtt_headers)

    if not resp.ok:
        return f"Error downloading transcript: {resp.text}"

    # Clean VTT format
    print("4. Cleaning VTT format...")
    vtt_content = resp.text
    lines = vtt_content.split("\n")
    cleaned_lines = []

    for line in lines:
        # Skip VTT headers, timestamps, and empty lines
        if (
            line.startswith("WEBVTT")
            or line.startswith("NOTE")
            or "-->" in line
            or re.match(r"^\d+$", line.strip())
        ):
            continue
        if line.strip():
            # Remove timestamp tags like <v Speaker Name>
            cleaned = re.sub(r"<v ([^>]+)>", r"\1: ", line)
            cleaned = re.sub(r"</v>", "", cleaned)
            cleaned_lines.append(cleaned.strip())

    transcript_text = "\n".join(cleaned_lines)

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(transcript_text)

    return f"\n✓ Successfully saved transcript to: {output_path}"


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python transcript_tool.py <JOIN_WEB_URL> <OUTPUT_PATH>")
        sys.exit(1)

    join_web_url = sys.argv[1]
    output_path = sys.argv[2]
    print(fetch_transcript(join_web_url, output_path))
