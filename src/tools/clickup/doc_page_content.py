import json
import requests
from tools.clickup import headers, BASE_URL_V3, CLICKUP_TEAM_ID


def get_page_content(doc_id: str, page_id: str) -> str:
    resp = requests.get(
        f"{BASE_URL_V3}/workspaces/{CLICKUP_TEAM_ID}/docs/{doc_id}/pages/{page_id}",
        headers=headers(),
        params={"content_format": "text/md"},
    )
    resp.raise_for_status()
    return json.dumps(resp.json(), indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Get content of a ClickUp doc page")
    parser.add_argument("doc_id", help="ClickUp document ID")
    parser.add_argument("page_id", help="ClickUp page ID")
    args = parser.parse_args()
    print(get_page_content(args.doc_id, args.page_id))
