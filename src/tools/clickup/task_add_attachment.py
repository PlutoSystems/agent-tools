import sys
import os
import json
import requests
from tools.clickup import CLICKUP_API_KEY, BASE_URL


def add_attachment(task_id: str, file_path: str) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    url = f"{BASE_URL}/task/{task_id}/attachment"
    filename = os.path.basename(file_path)

    with open(file_path, "rb") as f:
        resp = requests.post(
            url,
            headers={"Authorization": CLICKUP_API_KEY},
            files={"attachment": (filename, f)},
        )

    if not resp.ok:
        return f"Error uploading attachment: {resp.text}"

    data = resp.json()
    return json.dumps(data, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python add_attachment.py <task_id> <file_path>")
        sys.exit(1)

    result = add_attachment(sys.argv[1], sys.argv[2])
    print(result)
