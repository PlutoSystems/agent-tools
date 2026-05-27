import re
import sys
import json
import requests
from typing import Any
from tools.clickup import headers, BASE_URL, load_hierarchy

# ClickUp parent type enum values (from the view API's parent.type field)
_PARENT_TYPE_WORKSPACE = 1
_PARENT_TYPE_SPACE = 4
_PARENT_TYPE_FOLDER = 5
_PARENT_TYPE_LIST = 6

_PARENT_TYPE_ENTITY: dict[int, str] = {
    _PARENT_TYPE_WORKSPACE: "workspace",
    _PARENT_TYPE_SPACE: "space",
    _PARENT_TYPE_FOLDER: "folder",
    _PARENT_TYPE_LIST: "list",
}


def _get_view_parent(view_id: str) -> tuple[str, str] | None:
    """Returns (entity_type, parent_id) for a view, or None on failure."""
    resp = requests.get(f"{BASE_URL}/view/{view_id}", headers=headers())
    resp.raise_for_status()
    parent = resp.json().get("view", {}).get("parent", {})
    parent_type_int = parent.get("type")
    parent_id = str(parent.get("id", ""))
    entity_type = _PARENT_TYPE_ENTITY.get(parent_type_int)
    if entity_type and parent_id:
        return entity_type, parent_id
    return None


def _find_path(
    hierarchy: dict[str, Any], target_id: str
) -> list[dict[str, Any]] | None:
    """Walk the hierarchy tree and return the ancestor path for a given ID."""
    for space in hierarchy.get("spaces", []):
        s = {"type": "space", "id": space["id"], "name": space["name"]}

        if space["id"] == target_id:
            return [s]

        for doc in space.get("docs", []):
            if doc["id"] == target_id:
                return [s, {"type": "doc", "id": doc["id"], "name": doc["name"]}]

        for lst in space.get("lists", []):
            if lst["id"] == target_id:
                return [s, {"type": "list", "id": lst["id"], "name": lst["name"]}]

        for folder in space.get("folders", []):
            f = {"type": "folder", "id": folder["id"], "name": folder["name"]}

            if folder["id"] == target_id:
                return [s, f]

            for doc in folder.get("docs", []):
                if doc["id"] == target_id:
                    return [s, f, {"type": "doc", "id": doc["id"], "name": doc["name"]}]

            for lst in folder.get("lists", []):
                if lst["id"] == target_id:
                    return [
                        s,
                        f,
                        {"type": "list", "id": lst["id"], "name": lst["name"]},
                    ]

    return None


def resolve_clickup_url(url: str) -> str:
    """
    Interprets a ClickUp URL and returns the parent hierarchy as a list of IDs.

    Extracts entity IDs from the URL path, resolves view IDs via the ClickUp API
    when needed, then locates the entity in the local hierarchy cache.

    Args:
        url: A ClickUp app URL (e.g. https://app.clickup.com/14254316/v/l/dk07c-60177)

    Returns:
        JSON with the resolved hierarchy path, e.g.:
        { "hierarchy": [ { "type": "space", "id": "...", "name": "..." }, ... ] }
    """
    m = re.match(r"https://app\.clickup\.com/(\d+)/v/(.+)", url)
    if not m:
        return json.dumps({"error": "Not a valid ClickUp app URL"})

    segments = m.group(2).split("/")
    view_type = segments[0]
    rest = segments[1:]

    target_id: str | None = None

    if view_type == "o" and rest and rest[0] == "f" and len(rest) >= 2:
        # Folder overview: /v/o/f/{folder_id}
        target_id = rest[1]

    elif view_type == "dc" and rest:
        # Doc or page: /v/dc/{doc_id}/{page_id?} — use doc_id to locate in hierarchy
        target_id = rest[0]

    elif view_type in ("l", "b") and rest:
        seg = rest[0]

        if seg == "li" and len(rest) >= 2:
            # Board view with explicit list prefix: /v/b/li/{list_id}
            target_id = rest[1]

        elif "-" in seg:
            parts = seg.split("-")
            if parts[0].isdigit() and len(parts) >= 3:
                # Encoded view ID: {type_num}-{list_id}-{index} → extract list_id
                target_id = parts[1]
            else:
                # Named view ID like dk07c-60177 → fetch view to get parent
                result = _get_view_parent(seg)
                if result is None:
                    return json.dumps(
                        {"error": f"Could not resolve view parent for view '{seg}'"}
                    )
                _, target_id = result

        else:
            target_id = seg

    if not target_id:
        return json.dumps({"error": f"Could not extract an entity ID from URL: {url}"})

    hierarchy = load_hierarchy()
    path = _find_path(hierarchy, target_id)
    if path is None:
        return json.dumps(
            {
                "error": f"ID '{target_id}' not found in hierarchy cache. Try force_refresh via clickup_search_structure."
            }
        )

    return json.dumps({"hierarchy": path}, indent=2)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Resolve a ClickUp URL to its hierarchy"
    )
    parser.add_argument("url", help="ClickUp app URL to resolve")
    args = parser.parse_args()
    print(resolve_clickup_url(args.url))
