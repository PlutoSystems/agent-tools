import json
import requests
from typing import Literal
from tools.clickup import CLICKUP_API_KEY, CLICKUP_TEAM_ID, BASE_URL_V3, headers

EditMode = Literal["replace", "append", "prepend"]


def update_page(
    doc_id: str,
    page_id: str,
    content: str,
    name: str | None = None,
    sub_title: str | None = None,
    content_edit_mode: EditMode = "replace",
) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    payload: dict = {
        "content": content,
        "content_edit_mode": content_edit_mode,
        "content_format": "text/md",
    }
    if name is not None:
        payload["name"] = name
    if sub_title is not None:
        payload["sub_title"] = sub_title

    resp = requests.put(
        f"{BASE_URL_V3}/workspaces/{CLICKUP_TEAM_ID}/docs/{doc_id}/pages/{page_id}",
        headers=headers(),
        json=payload,
    )
    if not resp.ok:
        return f"Error updating page: {resp.text}"

    return json.dumps({"success": True}, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Update a ClickUp doc page")
    parser.add_argument("doc_id", help="ClickUp document ID")
    parser.add_argument("page_id", help="ClickUp page ID")
    parser.add_argument("content", help="Page content in markdown")
    parser.add_argument("--name", help="Update page name")
    parser.add_argument("--sub-title", help="Update page subtitle")
    parser.add_argument(
        "--mode",
        default="replace",
        choices=["replace", "append", "prepend"],
        help="How to apply the content (default: replace)",
    )
    args = parser.parse_args()
    print(
        update_page(
            args.doc_id,
            args.page_id,
            args.content,
            args.name,
            args.sub_title,
            args.mode,
        )
    )
