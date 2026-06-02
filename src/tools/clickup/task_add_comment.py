import json
import requests
from tools.clickup import CLICKUP_API_KEY, BASE_URL, headers


def add_comment(
    task_id: str,
    comment_text: str,
    assignee: int | None = None,
    notify_all: bool = False,
) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    payload: dict = {
        "comment_text": comment_text,
        "notify_all": notify_all,
    }
    if assignee is not None:
        payload["assignee"] = assignee

    resp = requests.post(
        f"{BASE_URL}/task/{task_id}/comment",
        headers=headers(),
        json=payload,
    )
    if not resp.ok:
        return f"Error adding comment: {resp.text}"

    data = resp.json()
    return json.dumps(
        {
            "id": data.get("id"),
            "hist_id": data.get("hist_id"),
            "date": data.get("date"),
        },
        indent=2,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Add a comment to a ClickUp task")
    parser.add_argument("task_id", help="ClickUp task ID")
    parser.add_argument("comment_text", help="Comment text")
    parser.add_argument("--assignee", type=int, help="User ID to assign the comment to")
    parser.add_argument("--notify-all", action="store_true")
    args = parser.parse_args()
    print(add_comment(args.task_id, args.comment_text, args.assignee, args.notify_all))
