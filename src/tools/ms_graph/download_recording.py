import sys
import os
import requests
import urllib.parse
from tools.ms_graph.auth import auth_headers, ROOT, GRAPH_BASE

SCOPES = [
    "https://graph.microsoft.com/OnlineMeetings.Read",
    "https://graph.microsoft.com/OnlineMeetingRecording.Read.All",
]


def download_recording(join_web_url: str) -> str:
    headers = auth_headers(SCOPES)

    encoded_url = urllib.parse.quote(join_web_url)
    lookup_url = f"{GRAPH_BASE}/me/onlineMeetings?$filter=JoinWebUrl eq '{encoded_url}'"
    resp = requests.get(lookup_url, headers=headers)

    if not resp.ok:
        return f"Error finding meeting: {resp.text}"

    data = resp.json()
    if not data["value"]:
        return "No meeting found for this Join URL."

    meeting = data["value"][0]
    meeting_id = meeting["id"]
    meeting_subject = meeting.get("subject", "Unknown Meeting")

    recordings_url = f"{GRAPH_BASE}/me/onlineMeetings/{meeting_id}/recordings"
    resp = requests.get(recordings_url, headers=headers)

    if not resp.ok:
        return f"Error fetching recordings: {resp.text}"

    recordings = resp.json().get("value", [])
    if not recordings:
        return "No recordings available for this meeting."

    recording = recordings[0]
    recording_id = recording["id"]

    content_url = (
        f"{GRAPH_BASE}/me/onlineMeetings/{meeting_id}/recordings/{recording_id}/content"
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

    return f"\n✓ Saved recording to: {output_path}\n" + "\n".join(metadata_lines)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_recording.py <JOIN_WEB_URL>")
        sys.exit(1)
    print(download_recording(sys.argv[1]))
