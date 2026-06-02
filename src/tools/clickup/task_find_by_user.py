import json
import requests
from tools.clickup import CLICKUP_API_KEY, CLICKUP_TEAM_ID, BASE_URL, headers


def find_user_tasks(
    user_id: str,
    include_closed: bool = False,
    page: int = 0,
) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    params: dict = {
        "page": page,
        "include_closed": str(include_closed).lower(),
        "assignees[]": [user_id],
        "subtasks": "true",
    }

    resp = requests.get(
        f"{BASE_URL}/team/{CLICKUP_TEAM_ID}/task",
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
                "list": t.get("list", {}).get("name"),
                "url": t.get("url"),
                "due_date": t.get("due_date"),
            }
        )
    return json.dumps(results, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find tasks assigned to a user")
    parser.add_argument("user_id", help="ClickUp user ID")
    parser.add_argument("--include-closed", action="store_true")
    parser.add_argument("--page", type=int, default=0)
    args = parser.parse_args()
    print(find_user_tasks(args.user_id, args.include_closed, args.page))
