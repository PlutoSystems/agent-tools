import json
import requests
from tools.clickup import CLICKUP_API_KEY, BASE_URL, headers


def delete_task(task_id: str) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    resp = requests.delete(
        f"{BASE_URL}/task/{task_id}",
        headers=headers(),
    )
    if not resp.ok:
        return f"Error deleting task: {resp.text}"

    return json.dumps({"success": True, "task_id": task_id}, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Delete a ClickUp task")
    parser.add_argument("task_id", help="ClickUp task ID")
    args = parser.parse_args()
    print(delete_task(args.task_id))
