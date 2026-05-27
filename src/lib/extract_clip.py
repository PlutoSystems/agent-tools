import sys
import av
from fractions import Fraction


def extract_clip(
    video_path: str, start_seconds: float, end_seconds: float, output_video_path: str
) -> str:
    input_container = av.open(video_path)
    output_container = av.open(output_video_path, mode="w")

    video_stream_in = input_container.streams.video[0]
    fps = Fraction(video_stream_in.average_rate)
    video_stream_out = output_container.add_stream(codec_name="h264", rate=fps)
    video_stream_out.width = video_stream_in.width
    video_stream_out.height = video_stream_in.height
    video_stream_out.pix_fmt = "yuv420p"
    video_stream_out.time_base = video_stream_in.time_base

    audio_stream_out = None
    if input_container.streams.audio:
        audio_stream_in = input_container.streams.audio[0]
        audio_stream_out = output_container.add_stream(
            codec_name="aac", rate=audio_stream_in.rate
        )
        audio_stream_out.layout = "stereo"

    input_container.seek(int(start_seconds * av.time_base), any_frame=False)

    streams = list(input_container.streams.video)
    if input_container.streams.audio:
        streams += list(input_container.streams.audio)

    video_frame_count = 0
    video_tb = video_stream_out.time_base

    for packet in input_container.demux(streams):
        for frame in packet.decode():
            ts = float(frame.pts * frame.time_base)
            if ts < start_seconds:
                continue
            if ts > end_seconds:
                for p in video_stream_out.encode():
                    output_container.mux(p)
                if audio_stream_out:
                    for p in audio_stream_out.encode():
                        output_container.mux(p)
                output_container.close()
                input_container.close()
                return f"Saved clip to {output_video_path}"

            if isinstance(frame, av.VideoFrame):
                frame = frame.reformat(format="yuv420p")
                frame.pts = int(Fraction(video_frame_count) / fps / video_tb)
                video_frame_count += 1
                for p in video_stream_out.encode(frame):
                    output_container.mux(p)
            elif isinstance(frame, av.AudioFrame) and audio_stream_out:
                frame.pts = None
                for p in audio_stream_out.encode(frame):
                    output_container.mux(p)

    for p in video_stream_out.encode():
        output_container.mux(p)
    if audio_stream_out:
        for p in audio_stream_out.encode():
            output_container.mux(p)

    output_container.close()
    input_container.close()
    return f"Saved clip to {output_video_path}"


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(
            "Usage: python extract_clip.py <video_path> <start_seconds> <end_seconds> <output_path>"
        )
        sys.exit(1)

    result = extract_clip(
        sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    )
    print(result)
