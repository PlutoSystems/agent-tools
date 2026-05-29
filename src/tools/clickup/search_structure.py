import json
from typing import Literal
from google import genai
from tools.clickup import get_hierarchy_index

EntityType = Literal["Space", "Folder", "List", "Document"]

_TYPE_MAP: dict[str, str] = {
    "Space": "space",
    "Folder": "folder",
    "List": "list",
    "Document": "doc",
}


def search_structure(
    entity_type: EntityType | None = None,
    keyword_search: str | None = None,
    query: str | None = None,
    space_id: str | None = None,
    force_refresh: bool = False,
) -> str:
    """
    Search the ClickUp workspace hierarchy for spaces, folders, lists, or docs.

    Always returns a JSON array of ALL matching results (up to 50).

    Search strategy — always try `keyword_search` first. Only use `query` if keyword_search
    returns no results or you have a descriptive/natural-language request that doesn't map
    to a specific name:
      1. `keyword_search` — fast substring match against entity names (case-insensitive).
                            Use this first with the most specific term you have.
      2. `query`          — AI-powered semantic search; results sorted by relevance.
                            Use only as a fallback when keyword_search yields nothing,
                            or when the search intent is descriptive rather than name-based.

    Args:
        entity_type:    Optional filter — "Space", "Folder", "List", or "Document"
        keyword_search: Substring to match against entity names (case-insensitive)
        query:          Natural-language description for AI-ranked semantic matching
        space_id:       Optional ClickUp space ID to restrict results to that space
        force_refresh:  Re-fetch hierarchy from API instead of using cache
    """
    index = get_hierarchy_index(force_refresh)
    internal_type = _TYPE_MAP[entity_type] if entity_type else None
    candidates = [
        e
        for e in index
        if (internal_type is None or e["type"] == internal_type)
        and (space_id is None or e["space_id"] == space_id)
    ]

    if keyword_search:
        kw = keyword_search.lower()
        matches = [e for e in candidates if kw in e["name"].lower()][:50]
        if matches:
            return json.dumps(matches, indent=2)

    search_term = query or keyword_search
    if search_term:
        client = genai.Client()
        candidates_json = json.dumps(
            [{"id": e["id"], "name": e["name"], "path": e["path"]} for e in candidates],
            indent=2,
        )
        prompt = (
            f"You are selecting all relevant ClickUp entities from a list.\n"
            f'Query: "{search_term}"\n\n'
            f"Candidates:\n{candidates_json}\n\n"
            f"Return ONLY a JSON array of IDs for all relevant matches, best first, up to 50. No other text."
        )
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=prompt,
        )
        try:
            matched_ids: list[str] = json.loads(response.text.strip())
        except Exception:
            matched_ids = [response.text.strip().strip('"').strip("'")]
        id_order = {mid: i for i, mid in enumerate(matched_ids)}
        matches = sorted(
            [e for e in candidates if e["id"] in id_order],
            key=lambda e: id_order[e["id"]],
        )[:50]
        if matches:
            return json.dumps(matches, indent=2)
        return json.dumps({"error": f"No matches found for '{search_term}'"})

    return json.dumps(candidates[:50], indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Search ClickUp workspace structure")
    parser.add_argument(
        "--type",
        dest="entity_type",
        choices=list(_TYPE_MAP.keys()),
        help="Entity type filter",
    )
    parser.add_argument("--id", help="Exact ClickUp ID")
    parser.add_argument(
        "--keyword-search",
        dest="keyword_search",
        help="Substring match against entity names",
    )
    parser.add_argument("--query", help="Fuzzy/natural-language search term")
    parser.add_argument(
        "--space-id", dest="space_id", help="Restrict results to this space ID"
    )
    parser.add_argument(
        "--refresh", action="store_true", help="Force re-fetch hierarchy from API"
    )
    args = parser.parse_args()

    if not any([args.id, args.keyword_search, args.query]):
        parser.error("Provide at least one of --id, --keyword-search, or --query")

    print(
        search_structure(
            entity_type=args.entity_type,
            keyword_search=args.keyword_search,
            query=args.query,
            space_id=args.space_id,
            force_refresh=args.refresh,
        )
    )
