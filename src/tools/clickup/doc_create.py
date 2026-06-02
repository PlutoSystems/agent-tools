import json
import requests
from tools.clickup import CLICKUP_API_KEY, CLICKUP_TEAM_ID, BASE_URL_V3, headers

PARENT_TYPE_MAP = {
    "space": 4,
    "folder": 5,
    "list": 6,
    "everything": 7,
    "workspace": 12,
}


def create_doc(
    name: str,
    parent_id: str,
    parent_type: str = "space",
    create_page: bool = True,
) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    type_num = PARENT_TYPE_MAP.get(parent_type.lower())
    if type_num is None:
        return f"Error: Unknown parent_type '{parent_type}'. Use: {', '.join(PARENT_TYPE_MAP)}"

    payload = {
        "name": name,
        "parent": {"id": parent_id, "type": type_num},
        "visibility": "PUBLIC",
        "create_page": create_page,
    }

    resp = requests.post(
        f"{BASE_URL_V3}/workspaces/{CLICKUP_TEAM_ID}/docs",
        headers=headers(),
        json=payload,
    )
    if not resp.ok:
        return f"Error creating doc: {resp.text}"

    doc = resp.json()
    return json.dumps(
        {
            "id": doc.get("id"),
            "name": doc.get("name"),
            "parent": doc.get("parent"),
            "workspace_id": doc.get("workspace_id"),
        },
        indent=2,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a ClickUp document")
    parser.add_argument("name", help="Document name")
    parser.add_argument("parent_id", help="Parent entity ID (space, folder, or list)")
    parser.add_argument(
        "--parent-type",
        default="space",
        choices=list(PARENT_TYPE_MAP),
        help="Type of parent entity",
    )
    parser.add_argument(
        "--no-page", action="store_true", help="Don't create an initial page"
    )
    args = parser.parse_args()
    print(create_doc(args.name, args.parent_id, args.parent_type, not args.no_page))
