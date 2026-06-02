import json
import requests
from tools.clickup import CLICKUP_API_KEY, BASE_URL, headers


def list_tasks(
    list_id: str,
    page: int = 0,
    include_closed: bool = False,
    assignees: list[str] | None = None,
) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    params: dict = {
        "page": page,
        "include_closed": str(include_closed).lower(),
    }
    if assignees:
        for a in assignees:
            params.setdefault("assignees[]", [])
            params["assignees[]"].append(a)

    resp = requests.get(
        f"{BASE_URL}/list/{list_id}/task",
        headers=headers(),
        params=params,
    )
    if not resp.ok:
        return f"Error fetching tasks: {resp.text}"

    tasks = resp.json().get("tasks", [])
    results = []
    for t in tasks:
        results.append(
            {
                "id": t.get("id"),
                "name": t.get("name"),
                "status": t.get("status", {}).get("status"),
                "assignees": [a.get("username") for a in t.get("assignees", [])],
                "url": t.get("url"),
                "date_created": t.get("date_created"),
                "due_date": t.get("due_date"),
            }
        )
    return json.dumps(results, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="List tasks in a ClickUp list")
    parser.add_argument("list_id", help="ClickUp list ID")
    parser.add_argument("--page", type=int, default=0)
    parser.add_argument("--include-closed", action="store_true")
    args = parser.parse_args()
    print(list_tasks(args.list_id, args.page, args.include_closed))
