import json
import requests
from tools.clickup import CLICKUP_API_KEY, CLICKUP_TEAM_ID, BASE_URL_V3, headers


def create_page(
    doc_id: str,
    name: str,
    content: str = "",
    parent_page_id: str | None = None,
    sub_title: str | None = None,
) -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    payload = {
        "name": name,
        "parent_page_id": parent_page_id,
        "sub_title": sub_title,
        "content": content,
        "content_format": "text/md",
    }

    resp = requests.post(
        f"{BASE_URL_V3}/workspaces/{CLICKUP_TEAM_ID}/docs/{doc_id}/pages",
        headers=headers(),
        json=payload,
    )
    if not resp.ok:
        return f"Error creating page: {resp.text}"

    page = resp.json()
    return json.dumps(
        {
            "id": page.get("id"),
            "doc_id": page.get("doc_id"),
            "name": page.get("name"),
            "parent_page_id": page.get("parent_page_id"),
        },
        indent=2,
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create a page in a ClickUp doc")
    parser.add_argument("doc_id", help="ClickUp document ID")
    parser.add_argument("name", help="Page name")
    parser.add_argument("--content", default="", help="Page content in markdown")
    parser.add_argument(
        "--parent-page-id", help="Parent page ID for creating sub-pages"
    )
    parser.add_argument("--sub-title", help="Page subtitle")
    args = parser.parse_args()
    print(
        create_page(
            args.doc_id, args.name, args.content, args.parent_page_id, args.sub_title
        )
    )
