import sys
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
    id: str | None = None,
    name: str | None = None,
    query: str | None = None,
    force_refresh: bool = False,
) -> str:
    """
    Search the ClickUp workspace hierarchy for a space, folder, list, or doc.

    Resolution order:
    1. ID exact match
    2. Name exact match (case-insensitive)
    3. Fuzzy match on `query` (or `name` as fallback) — returns ranked candidates for AI selection

    Args:
        entity_type: Optional filter — "space", "folder", "list", or "doc"
        id:          Find by exact ClickUp ID
        name:        Find by exact name (case-insensitive)
        query:       Natural-language description for fuzzy/AI matching
        force_refresh: Re-fetch hierarchy from API instead of using cache
    """
    index = get_hierarchy_index(force_refresh)
    internal_type = _TYPE_MAP[entity_type] if entity_type else None
    candidates = [
        e for e in index if internal_type is None or e["type"] == internal_type
    ]

    if id:
        matches = [e for e in candidates if e["id"] == id]
        if matches:
            return json.dumps(matches[0], indent=2)
        return json.dumps(
            {"error": f"No {entity_type or 'entity'} found with id '{id}'"}, indent=2
        )

    if name:
        exact = [e for e in candidates if e["name"].lower() == name.lower()]
        if exact:
            return json.dumps(exact if len(exact) > 1 else exact[0], indent=2)

    search_term = query or name
    if search_term:
        client = genai.Client()
        candidates_json = json.dumps(
            [{"id": e["id"], "name": e["name"], "path": e["path"]} for e in candidates],
            indent=2,
        )
        prompt = (
            f"You are selecting the best matching ClickUp entity from a list.\n"
            f'Query: "{search_term}"\n\n'
            f"Candidates:\n{candidates_json}\n\n"
            f"Return ONLY the id of the single best match, nothing else."
        )
        response = client.models.generate_content(
            model="gemini-flash-lite-latest",
            contents=prompt,
        )
        best_id = response.text.strip().strip('"').strip("'")
        match = next((e for e in candidates if e["id"] == best_id), None)
        if match:
            return json.dumps(match, indent=2)
        return json.dumps({"error": f"No matches found for '{search_term}'"})

    return json.dumps(candidates, indent=2)


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
    parser.add_argument("--name", help="Exact name (case-insensitive)")
    parser.add_argument("--query", help="Fuzzy/natural-language search term")
    parser.add_argument(
        "--refresh", action="store_true", help="Force re-fetch hierarchy from API"
    )
    args = parser.parse_args()

    if not any([args.id, args.name, args.query]):
        parser.error("Provide at least one of --id, --name, or --query")

    print(
        search_structure(
            entity_type=args.entity_type,
            id=args.id,
            name=args.name,
            query=args.query,
            force_refresh=args.refresh,
        )
    )
