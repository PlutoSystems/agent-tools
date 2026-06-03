import sys
import os
import json
import time
from google import genai
from pydantic import BaseModel, Field
from typing import Literal
from dotenv import load_dotenv
from lib.extract_frame import extract_frame
from lib.extract_clip import extract_clip

load_dotenv()

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.getenv("LOCAL_STORE_PATH", os.path.join(_REPO_ROOT, ".local"))

PROMPT = """You are a UX QA agent working for Pluto Systems.

Analyze the recording and transcript together and find each distinct QA issue mentioned or shown.

Output requirements:
- Keep each issue concise and task-ready.
- Capture repeated mentions as separate issues if they occur at different times.
- Do not invent details not explicitly supported by transcript or video.

When transcript and video differ, prefer video for timing and transcript for exact wording.
"""


class QAIssue(BaseModel):
    category: Literal["bug", "feature_request", "ux_issue"] = Field(
        description="The type of issue identified."
    )
    quote: str = Field(description="The user's direct quote from the video.")
    explanation: str = Field(description="A brief explanation of the issue.")
    start_time: str = Field(
        description="When the user starts talking about it (HH:MM:SS)."
    )
    end_time: str = Field(description="When they stop talking about it (HH:MM:SS).")
    evidence_source: Literal["transcript", "video", "both"] = Field(
        description="Whether this issue is supported by transcript, video, or both."
    )


class QAResult(BaseModel):
    issues: list[QAIssue] = Field(
        description="List of identified issues. Empty if none found."
    )


def time_to_seconds(t: str) -> float:
    parts = t.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


def analyze_qa_recording(
    video_path: str, transcript_path: str, meeting_name: str | None = None
) -> str:
    if not os.path.exists(video_path):
        return json.dumps({"error": f"Video not found at {video_path}"})

    if not os.path.exists(transcript_path):
        return json.dumps({"error": f"Transcript not found at {transcript_path}"})

    with open(transcript_path, "r", encoding="utf-8") as f:
        transcript_text = f.read().strip()

    if not meeting_name:
        meeting_name = os.path.splitext(os.path.basename(video_path))[0]

    safe_name = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in meeting_name
    ).strip()
    results_dir = os.path.join(ROOT, "qa_results", safe_name)
    imgs_dir = os.path.join(results_dir, "imgs")
    clips_dir = os.path.join(results_dir, "clips")
    os.makedirs(imgs_dir, exist_ok=True)
    os.makedirs(clips_dir, exist_ok=True)

    print("1. Uploading video to Gemini...", file=sys.stderr)
    client = genai.Client()
    video_file = client.files.upload(file=video_path)

    try:
        print("2. Waiting for file processing...", file=sys.stderr)
        while video_file.state.name == "PROCESSING":
            time.sleep(5)
            video_file = client.files.get(name=video_file.name)
            print(f"   State: {video_file.state.name}", file=sys.stderr)

        if video_file.state.name != "ACTIVE":
            return json.dumps(
                {"error": f"File processing failed with state {video_file.state.name}"}
            )

        print("3. Analyzing video and transcript with Gemini Flash...", file=sys.stderr)
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[
                video_file,
                f"{PROMPT}\n\nUse the transcript as supporting evidence for exact wording and use the video for visual/timing context.\n\nTranscript:\n{transcript_text}",
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": QAResult,
            },
        )

        usage = response.usage_metadata
        print(
            f"   Tokens — prompt: {usage.prompt_token_count}, response: {usage.candidates_token_count}, total: {usage.total_token_count}",
            file=sys.stderr,
        )

        result = QAResult.model_validate_json(response.text)
        issues = [issue.model_dump() for issue in result.issues]

        results_path = os.path.join(results_dir, "issues.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(issues, f, indent=2)
        print(f"3. Saved {len(issues)} issues to {results_path}", file=sys.stderr)

        print("4. Extracting screenshots and clips...", file=sys.stderr)
        for issue in issues:
            start_sec = time_to_seconds(issue["start_time"])
            end_sec = time_to_seconds(issue["end_time"])
            mid_sec = (start_sec + end_sec) / 2
            category = issue["category"]

            clip_start = max(0, start_sec - 5)
            clip_filename = f"{category}_{issue['start_time'].replace(':', '-')}.mp4"
            clip_path = os.path.join(clips_dir, clip_filename)
            clip_result = extract_clip(video_path, clip_start, end_sec, clip_path)
            print(f"   {clip_result}", file=sys.stderr)
            issue["clip"] = clip_path

            issue["screenshots"] = []
            for label, ts in [
                ("pre", clip_start),
                ("start", start_sec),
                ("mid", mid_sec),
                ("end", end_sec),
            ]:
                ts_str = (
                    issue["start_time"].replace(":", "-")
                    if label == "start"
                    else (
                        issue["end_time"].replace(":", "-")
                        if label == "end"
                        else f"{int(ts // 3600):02d}-{int((ts % 3600) // 60):02d}-{int(ts % 60):02d}"
                    )
                )
                filename = f"{category}_{ts_str}_{label}.jpg"
                out_path = os.path.join(imgs_dir, filename)
                frame_result = extract_frame(video_path, ts, out_path)
                print(f"   {frame_result}", file=sys.stderr)
                issue["screenshots"].append(out_path)

        output = {
            "meeting_name": meeting_name,
            "transcript_path": transcript_path,
            "total_issues": len(issues),
            "results_dir": results_dir,
            "tokens": {
                "prompt": usage.prompt_token_count,
                "response": usage.candidates_token_count,
                "total": usage.total_token_count,
            },
            "issues": issues,
        }

        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2)

        return json.dumps(output, indent=2)
    finally:
        print("Cleaning up uploaded file...", file=sys.stderr)
        try:
            client.files.delete(name=video_file.name)
        except Exception:
            pass


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: uv run python -m src.tools.analyze_qa_recording_tool <video_path> <transcript_path> [meeting_name]"
        )
        sys.exit(1)

    video_path = sys.argv[1]
    transcript_path = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else None
    print(analyze_qa_recording(video_path, transcript_path, name))
