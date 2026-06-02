import os
import json
import requests
from tools.clickup import CLICKUP_API_KEY, BASE_URL, ROOT, headers

_PERSONAL_CACHE = os.path.join(ROOT, "clickup", "personal_list.json")

NOT_CONFIGURED_MSG = (
    "Error: Personal List not configured. "
    "Ask the user to provide their ClickUp Personal List URL or list ID, "
    "then call clickup_set_personal_list to save it."
)


def _get_personal_list_id() -> str | None:
    if not os.path.exists(_PERSONAL_CACHE):
        return None
    with open(_PERSONAL_CACHE) as f:
        return json.load(f).get("list_id")


def _get_current_user_id() -> str | None:
    resp = requests.get(f"{BASE_URL}/user", headers=headers())
    if not resp.ok:
        return None
    return str(resp.json().get("user", {}).get("id", ""))


def my_tasks(include_closed: bool = False, page: int = 0) -> str:
    list_id = _get_personal_list_id()
    if not list_id:
        return NOT_CONFIGURED_MSG

    resp = requests.get(
        f"{BASE_URL}/list/{list_id}/task",
        headers=headers(),
        params={"page": page, "include_closed": str(include_closed).lower()},
    )
    if not resp.ok:
        return f"Error fetching tasks: {resp.text}"

    return json.dumps(
        [
            {
                "id": t.get("id"),
                "name": t.get("name"),
                "status": t.get("status", {}).get("status"),
                "url": t.get("url"),
                "due_date": t.get("due_date"),
                "priority": (
                    t.get("priority", {}).get("priority") if t.get("priority") else None
                ),
            }
            for t in resp.json().get("tasks", [])
        ],
        indent=2,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--include-closed", action="store_true")
    parser.add_argument("--page", type=int, default=0)
    args = parser.parse_args()
    print(my_tasks(args.include_closed, args.page))
