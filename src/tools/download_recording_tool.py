import sys
import os
import json
import requests
import urllib.parse
from dotenv import load_dotenv
from azure.identity import (
    InteractiveBrowserCredential,
    TokenCachePersistenceOptions,
    AuthenticationRecord,
)

load_dotenv()

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.getenv("LOCAL_STORE_PATH", os.path.join(_REPO_ROOT, ".local"))
AUTH_RECORD_PATH = os.path.join(ROOT, "ms_auth_record.json")
CLIENT_ID = os.getenv("MS_CLIENT_ID")
SCOPES = [
    "https://graph.microsoft.com/OnlineMeetings.Read",
    "https://graph.microsoft.com/OnlineMeetingRecording.Read.All",
]


def get_silent_credential():
    cache_options = TokenCachePersistenceOptions(allow_unencrypted_storage=True)
    auth_record = None

    if os.path.exists(AUTH_RECORD_PATH):
        print(f"DEBUG: Found {AUTH_RECORD_PATH}, loading user identity...")
        try:
            with open(AUTH_RECORD_PATH, "r") as f:
                json_record = json.load(f)
                auth_record = AuthenticationRecord.deserialize(json_record)
        except Exception as e:
            print(f"DEBUG: Failed to load auth record: {e}")

    credential = InteractiveBrowserCredential(
        client_id=CLIENT_ID,
        cache_persistence_options=cache_options,
        authentication_record=auth_record,
    )
    return credential


def download_recording(join_web_url: str) -> str:
    if not CLIENT_ID:
        return "Error: MS_CLIENT_ID not set in environment variables."

    print("--- Authenticating ---")
    credential = get_silent_credential()

    print("DEBUG: Attempting to get token from cache or authenticate...")
    token_obj = credential.get_token(*SCOPES)
    access_token = token_obj.token

    record = credential.authenticate(scopes=SCOPES)
    os.makedirs(os.path.dirname(os.path.abspath(AUTH_RECORD_PATH)), exist_ok=True)
    with open(AUTH_RECORD_PATH, "w") as f:
        json.dump(record.serialize(), f)
        print(f"DEBUG: Saved user identity to {AUTH_RECORD_PATH}")

    headers = {"Authorization": f"Bearer {access_token}"}

    print("1. Resolving Meeting ID...")
    encoded_url = urllib.parse.quote(join_web_url)
    base_url = "https://graph.microsoft.com/v1.0"

    lookup_url = f"{base_url}/me/onlineMeetings?$filter=JoinWebUrl eq '{encoded_url}'"
    resp = requests.get(lookup_url, headers=headers)

    if not resp.ok:
        return f"Error finding meeting: {resp.text}"

    data = resp.json()
    if not data["value"]:
        return "No meeting found for this Join URL."

    meeting = data["value"][0]
    meeting_id = meeting["id"]
    meeting_subject = meeting.get("subject", "Unknown Meeting")

    print("2. Fetching Recording List...")
    recordings_url = f"{base_url}/me/onlineMeetings/{meeting_id}/recordings"
    resp = requests.get(recordings_url, headers=headers)

    if not resp.ok:
        return f"Error fetching recordings: {resp.text}"

    recordings = resp.json().get("value", [])
    if not recordings:
        return "No recordings available for this meeting."

    recording = recordings[0]
    recording_id = recording["id"]

    print("3. Downloading Recording...")
    content_url = (
        f"{base_url}/me/onlineMeetings/{meeting_id}/recordings/{recording_id}/content"
    )
    resp = requests.get(content_url, headers=headers, stream=True)

    if not resp.ok:
        return f"Error downloading recording: {resp.text}"

    safe_subject = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in meeting_subject
    ).strip()
    filename = f"{safe_subject}_{recording_id[:8]}.mp4"
    output_path = os.path.join(ROOT, "recordings", filename)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    total_bytes = 0
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            total_bytes += len(chunk)

    size_mb = total_bytes / (1024 * 1024)

    metadata_lines = [
        f"Meeting: {meeting_subject}",
        f"Recording ID: {recording_id}",
        f"File: {filename}",
        f"Size: {size_mb:.1f} MB",
        f"Start: {meeting.get('startDateTime', 'N/A')}",
        f"End: {meeting.get('endDateTime', 'N/A')}",
    ]

    created = recording.get("createdDateTime")
    if created:
        metadata_lines.append(f"Recorded: {created}")

    print("\n".join(metadata_lines))
    return f"\n✓ Saved recording to: {output_path}\n" + "\n".join(metadata_lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_recording.py <JOIN_WEB_URL>")
        sys.exit(1)

    join_web_url = sys.argv[1]
    print(download_recording(join_web_url))
