import json
import requests
from tools.clickup import CLICKUP_API_KEY, BASE_URL, headers, get_task_type_id


def update_task(
    task_id: str,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
    priority: int | None = None,
    due_date: int | None = None,
    assignees_add: list[int] | None = None,
    assignees_rem: list[int] | None = None,
    task_type: str | None = None,
    tags_add: list[str] | None = None,
    tags_rem: list[str] | None = None,
) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    payload: dict = {}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["markdown_content"] = description
    if status is not None:
        payload["status"] = status
    if priority is not None:
        payload["priority"] = priority
    if due_date is not None:
        payload["due_date"] = due_date
    if assignees_add or assignees_rem:
        payload["assignees"] = {
            "add": assignees_add or [],
            "rem": assignees_rem or [],
        }
    if task_type is not None:
        type_id = get_task_type_id(task_type)
        if type_id is None:
            return f"Error: Unknown task type '{task_type}'"
        payload["custom_item_id"] = type_id

    if payload:
        resp = requests.put(
            f"{BASE_URL}/task/{task_id}",
            headers=headers(),
            json=payload,
        )
        if not resp.ok:
            return f"Error updating task: {resp.text}"

    errors = []
    for tag in tags_add or []:
        tag = tag.lower()
        r = requests.post(f"{BASE_URL}/task/{task_id}/tag/{tag}", headers=headers())
        if not r.ok:
            errors.append(f"Error adding tag '{tag}': {r.text}")
    for tag in tags_rem or []:
        tag = tag.lower()
        r = requests.delete(f"{BASE_URL}/task/{task_id}/tag/{tag}", headers=headers())
        if not r.ok:
            errors.append(f"Error removing tag '{tag}': {r.text}")

    if not payload and not tags_add and not tags_rem:
        return "Error: No fields to update"

    if errors:
        return json.dumps({"partial_errors": errors}, indent=2)

    resp = requests.get(f"{BASE_URL}/task/{task_id}", headers=headers())
    task = resp.json() if resp.ok else {}
    return json.dumps(
        {
            "id": task.get("id", task_id),
            "name": task.get("name"),
            "status": task.get("status", {}).get("status"),
            "url": task.get("url"),
            "tags": [t.get("name") for t in task.get("tags", [])],
        },
        indent=2,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update a ClickUp task")
    parser.add_argument("task_id", help="ClickUp task ID")
    parser.add_argument("--name", help="New task name")
    parser.add_argument("--status", help="New status")
    parser.add_argument("--description", help="New description (markdown)")
    parser.add_argument("--priority", type=int, help="Priority (1=urgent, 4=low)")
    args = parser.parse_args()
    print(
        update_task(
            args.task_id, args.name, args.description, args.status, args.priority
        )
    )
