import cv2


def extract_frame(
    video_path: str, timestamp_in_seconds: float, output_image_path: str
) -> str:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return f"Error: Could not open video at {video_path}"

    cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_in_seconds * 1000)
    success, frame = cap.read()
    cap.release()

    if not success:
        return f"Error: Could not read frame at {timestamp_in_seconds}s"

    cv2.imwrite(output_image_path, frame)
    return f"Saved screenshot to {output_image_path}"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print(
            "Usage: python extract_frame.py <video_path> <timestamp_seconds> <output_image_path>"
        )
        sys.exit(1)

    result = extract_frame(sys.argv[1], float(sys.argv[2]), sys.argv[3])
    print(result)
