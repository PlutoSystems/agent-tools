import sys
import json
import requests
from tools.clickup import CLICKUP_API_KEY, BASE_URL, headers, get_task_type_id


def create_task(
    list_id: str,
    name: str,
    markdown_content: str,
    task_type: str | None = None,
    parent: str | None = None,
) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    payload: dict = {
        "name": name,
        "markdown_content": markdown_content,
        "status": "Open",
    }

    if task_type:
        type_id = get_task_type_id(task_type)
        if type_id is not None:
            payload["custom_item_id"] = type_id
        else:
            return f"Error: Unknown task type '{task_type}'. Available types will be cached on first call."

    if parent:
        payload["parent"] = parent

    resp = requests.post(
        f"{BASE_URL}/list/{list_id}/task",
        headers=headers(),
        json=payload,
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
    if len(sys.argv) < 4:
        print(
            "Usage: python create_task.py <list_id> <name> <markdown_content> [task_type] [parent_id]"
        )
        sys.exit(1)

    result = create_task(
        list_id=sys.argv[1],
        name=sys.argv[2],
        markdown_content=sys.argv[3],
        task_type=sys.argv[4] if len(sys.argv) > 4 else None,
        parent=sys.argv[5] if len(sys.argv) > 5 else None,
    )
    print(result)
