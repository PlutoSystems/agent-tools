import json
import requests
from tools.clickup import headers, BASE_URL_V3, CLICKUP_TEAM_ID


def get_doc_pages(doc_id: str, max_page_depth: int = -1) -> str:
    resp = requests.get(
        f"{BASE_URL_V3}/workspaces/{CLICKUP_TEAM_ID}/docs/{doc_id}/page_listing",
        headers=headers(),
        params={"max_page_depth": max_page_depth},
    )
    resp.raise_for_status()
    return json.dumps(resp.json(), indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch page listing for a ClickUp doc")
    parser.add_argument("doc_id", help="ClickUp document ID")
    parser.add_argument(
        "--depth", type=int, default=-1, help="Max page depth (-1 for unlimited)"
    )
    args = parser.parse_args()
    print(get_doc_pages(args.doc_id, args.depth))
