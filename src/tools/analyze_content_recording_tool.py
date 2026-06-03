import sys
import os
import json
import time
from typing import Literal
from google import genai
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from lib.extract_frame import extract_frame
from lib.extract_clip import extract_clip

load_dotenv()

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.getenv("LOCAL_STORE_PATH", os.path.join(_REPO_ROOT, ".local"))

PROMPT = """You are a reviewer for marketing and sales content.

Analyze the recording and transcript together and extract practical, non-technical improvement ideas (website copy, messaging, landing pages, sales enablement, etc.).

Output requirements:
- Keep ideas concise, clear, and directly actionable.
- Only include ideas explicitly supported by transcript or on-screen evidence.
- Do not over-infer strategy beyond what is shown/said.

evidence_source rules:
- transcript: idea is supported by spoken/written transcript evidence only.
- video: idea is supported by visible on-screen evidence only (no clear transcript support).
- both: idea is supported by both transcript and video.

When transcript and video differ, prefer video for timing and transcript for exact wording.
"""


class ContentIdea(BaseModel):
    title: str = Field(description="Short task-friendly title for this idea.")
    summary: str = Field(description="Short explanation of what should be changed.")
    quote: str = Field(
        description="Direct quote or explicit on-screen text that supports this idea."
    )
    start_time: str = Field(
        description="When this idea starts in the recording (HH:MM:SS)."
    )
    end_time: str = Field(
        description="When this idea ends in the recording (HH:MM:SS)."
    )
    evidence_source: Literal["transcript", "video", "both"] = Field(
        description="Whether this idea is supported by transcript, video, or both."
    )


class ContentResult(BaseModel):
    ideas: list[ContentIdea] = Field(
        description="List of organized content improvement ideas. Empty if none found."
    )


def time_to_seconds(t: str) -> float:
    parts = t.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(parts[0])


def analyze_content_recording(
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
    results_dir = os.path.join(ROOT, "content_results", safe_name)
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

        print(
            "3. Analyzing content with video and transcript using Gemini Flash...",
            file=sys.stderr,
        )
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=[
                video_file,
                f"{PROMPT}\n\nUse the transcript as supporting evidence for exact wording and use the video for visual/timing context.\n\nTranscript:\n{transcript_text}",
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": ContentResult,
            },
        )

        usage = response.usage_metadata
        print(
            f"   Tokens - prompt: {usage.prompt_token_count}, response: {usage.candidates_token_count}, total: {usage.total_token_count}",
            file=sys.stderr,
        )

        result = ContentResult.model_validate_json(response.text)
        ideas = [idea.model_dump() for idea in result.ideas]

        results_path = os.path.join(results_dir, "ideas.json")
        print(
            f"4. Extracting screenshots and clips for {len(ideas)} ideas...",
            file=sys.stderr,
        )

        for idea in ideas:
            start_sec = time_to_seconds(idea["start_time"])
            end_sec = time_to_seconds(idea["end_time"])
            mid_sec = (start_sec + end_sec) / 2

            clip_start = max(0, start_sec - 5)
            clip_filename = f"{idea['start_time'].replace(':', '-')}.mp4"
            clip_path = os.path.join(clips_dir, clip_filename)
            clip_result = extract_clip(video_path, clip_start, end_sec, clip_path)
            print(f"   {clip_result}", file=sys.stderr)
            idea["clip"] = clip_path

            idea["screenshots"] = []
            for label, ts in [
                ("pre", clip_start),
                ("start", start_sec),
                ("mid", mid_sec),
                ("end", end_sec),
            ]:
                ts_str = (
                    idea["start_time"].replace(":", "-")
                    if label == "start"
                    else (
                        idea["end_time"].replace(":", "-")
                        if label == "end"
                        else f"{int(ts // 3600):02d}-{int((ts % 3600) // 60):02d}-{int(ts % 60):02d}"
                    )
                )
                filename = f"{ts_str}_{label}.jpg"
                out_path = os.path.join(imgs_dir, filename)
                frame_result = extract_frame(video_path, ts, out_path)
                print(f"   {frame_result}", file=sys.stderr)
                idea["screenshots"].append(out_path)

        output = {
            "meeting_name": meeting_name,
            "transcript_path": transcript_path,
            "analysis_type": "marketing_sales_content",
            "total_ideas": len(ideas),
            "results_dir": results_dir,
            "tokens": {
                "prompt": usage.prompt_token_count,
                "response": usage.candidates_token_count,
                "total": usage.total_token_count,
            },
            "ideas": ideas,
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
            "Usage: python analyze_content_recording_tool.py <video_path> <transcript_path> [meeting_name]"
        )
        sys.exit(1)

    video_path = sys.argv[1]
    transcript_path = sys.argv[2]
    name = sys.argv[3] if len(sys.argv) > 3 else None
    print(analyze_content_recording(video_path, transcript_path, name))
