import json
import requests
from tools.clickup import CLICKUP_API_KEY, BASE_URL, headers, get_task_type_id
from tools.clickup.my_tasks import (
    _get_current_user_id,
    _get_personal_list_id,
    NOT_CONFIGURED_MSG,
)


def add_personal_task(
    name: str,
    description: str = "",
    task_type: str | None = None,
    priority: int | None = None,
    due_date: int | None = None,
) -> str:
    list_id = _get_personal_list_id()
    if not list_id:
        return NOT_CONFIGURED_MSG

    user_id = _get_current_user_id()
    if not user_id:
        return "Error: Could not determine current user ID"

    payload: dict = {
        "name": name,
        "markdown_content": description,
        "assignees": [int(user_id)],
        "status": "to do",
    }
    if task_type:
        type_id = get_task_type_id(task_type)
        if type_id is not None:
            payload["custom_item_id"] = type_id
        else:
            return f"Error: Unknown task type '{task_type}'"
    if priority is not None:
        payload["priority"] = priority
    if due_date is not None:
        payload["due_date"] = due_date

    resp = requests.post(
        f"{BASE_URL}/list/{list_id}/task", headers=headers(), json=payload
    )
    if not resp.ok:
        return f"Error creating task: {resp.text}"

    task = resp.json()
    return json.dumps(
        {
            "id": task.get("id"),
            "name": task.get("name"),
            "url": task.get("url"),
            "status": task.get("status", {}).get("status"),
        },
        indent=2,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("--description", default="")
    parser.add_argument("--task-type")
    parser.add_argument("--priority", type=int)
    args = parser.parse_args()
    print(add_personal_task(args.name, args.description, args.task_type, args.priority))
