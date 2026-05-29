import sys
import os
import re
import requests
import urllib.parse
from tools.ms_graph.auth import auth_headers, ROOT, GRAPH_BASE

SCOPES = [
    "https://graph.microsoft.com/OnlineMeetings.Read",
    "https://graph.microsoft.com/OnlineMeetingTranscript.Read.All",
]


def fetch_transcript(join_web_url: str, output_path: str | None = None) -> str:
    headers = auth_headers(SCOPES)

    encoded_url = urllib.parse.quote(join_web_url)
    lookup_url = f"{GRAPH_BASE}/me/onlineMeetings?$filter=JoinWebUrl eq '{encoded_url}'"
    resp = requests.get(lookup_url, headers=headers)

    if not resp.ok:
        return f"Error finding meeting: {resp.text}"

    data = resp.json()
    if not data["value"]:
        return "No meeting found for this Join URL."

    meeting_id = data["value"][0]["id"]
    meeting_subject = data["value"][0].get("subject", "Unknown Meeting")

    transcripts_url = f"{GRAPH_BASE}/me/onlineMeetings/{meeting_id}/transcripts"
    resp = requests.get(transcripts_url, headers=headers)

    transcripts = resp.json().get("value", [])
    if not transcripts:
        return "No transcripts available."

    transcript_id = transcripts[0]["id"]

    content_url = f"{GRAPH_BASE}/me/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"
    vtt_headers = {**headers, "Accept": "text/vtt"}
    resp = requests.get(content_url, headers=vtt_headers)

    if not resp.ok:
        return f"Error downloading transcript: {resp.text}"

    lines = resp.text.split("\n")
    cleaned_lines = []
    for line in lines:
        if (
            line.startswith("WEBVTT")
            or line.startswith("NOTE")
            or "-->" in line
            or re.match(r"^\d+$", line.strip())
        ):
            continue
        if line.strip():
            cleaned = re.sub(r"<v ([^>]+)>", r"\1: ", line)
            cleaned = re.sub(r"</v>", "", cleaned)
            cleaned_lines.append(cleaned.strip())

    transcript_text = "\n".join(cleaned_lines)

    safe_subject = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in meeting_subject
    ).strip()
    filename = f"{safe_subject}_{transcript_id[:8]}.txt"
    local_path = os.path.join(ROOT, "transcripts", filename)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    with open(local_path, "w", encoding="utf-8") as f:
        f.write(transcript_text)

    saved_paths = [local_path]

    if output_path:
        output_path = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(transcript_text)
        saved_paths.append(output_path)

    return f"\n✓ Successfully saved transcript to: {', '.join(saved_paths)}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_transcript.py <JOIN_WEB_URL> [OUTPUT_PATH]")
        sys.exit(1)
    print(fetch_transcript(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None))
