import json
import re
import requests
from typing import Any
from tools.clickup import CLICKUP_API_KEY, CLICKUP_TEAM_ID, BASE_URL, headers

_CUSTOM_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]*-\d+$")


def parse_task_ref(ref: str) -> tuple[str, str | None]:
    """Accepts a task ID or a ClickUp task URL (/t/{task_id} or /t/{workspace_id}/{task_id}).

    Returns (task_id, workspace_id | None).
    """
    ref = ref.split("?")[0].split("#")[0].rstrip("/")
    m = re.match(r"https?://app\.clickup\.com/t/(?:(\d+)/)?([^/]+)$", ref)
    if m:
        return m.group(2), m.group(1)
    return ref, None


def fetch_task(task_ref: str) -> tuple[dict[str, Any] | None, str | None]:
    """Returns (task_json, error)."""
    if not CLICKUP_API_KEY:
        return None, "CLICKUP_API_KEY not set"

    task_id, workspace_id = parse_task_ref(task_ref)
    params: dict[str, str] = {
        "include_markdown_description": "true",
        "include_subtasks": "true",
    }
    if _CUSTOM_ID_RE.match(task_id):
        team_id = workspace_id or CLICKUP_TEAM_ID
        if team_id:
            params["custom_task_ids"] = "true"
            params["team_id"] = team_id

    resp = requests.get(f"{BASE_URL}/task/{task_id}", headers=headers(), params=params)
    if not resp.ok:
        return None, f"Could not fetch task '{task_id}': {resp.text}"
    return resp.json(), None


def summarize_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": task.get("id"),
        "custom_id": task.get("custom_id"),
        "name": task.get("name"),
        "description": task.get("markdown_description") or task.get("description"),
        "status": (task.get("status") or {}).get("status"),
        "priority": (task.get("priority") or {}).get("priority"),
        "assignees": [a.get("username") for a in task.get("assignees", [])],
        "tags": [t.get("name") for t in task.get("tags", [])],
        "due_date": task.get("due_date"),
        "parent": task.get("parent"),
        "subtasks": [
            {"id": s.get("id"), "name": s.get("name")} for s in task.get("subtasks", [])
        ],
        "list": task.get("list", {}),
        "url": task.get("url"),
    }


def get_task(task_id: str) -> str:
    task, err = fetch_task(task_id)
    if err or task is None:
        return f"Error: {err}"
    return json.dumps(summarize_task(task), indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Get a ClickUp task with description")
    parser.add_argument("task_id", help="ClickUp task ID or task URL")
    args = parser.parse_args()
    print(get_task(args.task_id))
