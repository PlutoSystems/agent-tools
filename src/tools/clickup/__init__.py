import os
import json
import requests
from typing import Any
from dotenv import load_dotenv

load_dotenv()

CLICKUP_API_KEY = os.getenv("CLICKUP_API_KEY")
CLICKUP_TEAM_ID = os.getenv("CLICKUP_TEAM_ID")
BASE_URL = "https://api.clickup.com/api/v2"
BASE_URL_V3 = "https://api.clickup.com/api/v3"
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ROOT = os.getenv("LOCAL_STORE_PATH", os.path.join(_REPO_ROOT, ".local"))
CACHE_PATH = os.path.join(ROOT, "clickup", "custom_task_types.json")
HIERARCHY_CACHE_PATH = os.path.join(ROOT, "clickup", "hierarchy.json")


def headers() -> dict[str, str]:
    return {
        "Authorization": CLICKUP_API_KEY,
        "Content-Type": "application/json",
    }


_custom_task_types: dict[str, int] | None = None


def get_custom_task_types() -> dict[str, int]:
    global _custom_task_types
    if _custom_task_types is not None:
        return _custom_task_types

    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            _custom_task_types = json.load(f)
        return _custom_task_types

    if not CLICKUP_API_KEY or not CLICKUP_TEAM_ID:
        _custom_task_types = {}
        return _custom_task_types

    resp = requests.get(
        f"{BASE_URL}/team/{CLICKUP_TEAM_ID}/custom_item",
        headers=headers(),
    )
    resp.raise_for_status()

    items = resp.json().get("custom_items", [])
    _custom_task_types = {item["name"].lower(): item["id"] for item in items}

    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump(_custom_task_types, f, indent=2)

    return _custom_task_types


def get_task_type_id(task_type: str) -> int | None:
    types = get_custom_task_types()
    return types.get(task_type.lower())


_hierarchy: dict[str, Any] | None = None


def load_hierarchy(force_refresh: bool = False) -> dict[str, Any]:
    """Fetches the full ClickUp hierarchy (spaces → folders → lists + docs) and caches to disk."""
    global _hierarchy
    if _hierarchy is not None and not force_refresh:
        return _hierarchy

    if os.path.exists(HIERARCHY_CACHE_PATH) and not force_refresh:
        print(f"Loading hierarchy from cache: {HIERARCHY_CACHE_PATH}")
        with open(HIERARCHY_CACHE_PATH) as f:
            _hierarchy = json.load(f)
        return _hierarchy

    if not CLICKUP_API_KEY or not CLICKUP_TEAM_ID:
        return {"spaces": [], "docs": []}

    print("Rebuilding hierarchy from ClickUp API...")

    spaces_resp = requests.get(
        f"{BASE_URL}/team/{CLICKUP_TEAM_ID}/space",
        headers=headers(),
        params={"archived": "false"},
    )
    spaces_resp.raise_for_status()
    spaces_raw = spaces_resp.json().get("spaces", [])

    space_map: dict[str, dict[str, Any]] = {}
    folder_map: dict[str, dict[str, Any]] = {}
    spaces: list[dict[str, Any]] = []
    for s in spaces_raw:
        print(f"  Fetching space: {s['name']}")
        space: dict[str, Any] = {
            "id": s["id"],
            "name": s["name"],
            "docs": [],
            "folders": [],
            "lists": [],
        }
        space_map[s["id"]] = space

        folders_resp = requests.get(
            f"{BASE_URL}/space/{s['id']}/folder",
            headers=headers(),
            params={"archived": "false"},
        )
        folders_resp.raise_for_status()
        for f in folders_resp.json().get("folders", []):
            folder: dict[str, Any] = {
                "id": f["id"],
                "name": f["name"],
                "docs": [],
                "lists": [
                    {"id": l["id"], "name": l["name"]} for l in f.get("lists", [])
                ],
            }
            folder_map[f["id"]] = folder
            space["folders"].append(folder)

        lists_resp = requests.get(
            f"{BASE_URL}/space/{s['id']}/list",
            headers=headers(),
            params={"archived": "false"},
        )
        lists_resp.raise_for_status()
        space["lists"] = [
            {"id": l["id"], "name": l["name"]}
            for l in lists_resp.json().get("lists", [])
        ]

        spaces.append(space)

    try:
        print("  Fetching docs (paginated)...")
        doc_count = 0
        cursor: str | None = None
        while True:
            params: dict[str, Any] = {
                "deleted": "false",
                "archived": "false",
                "limit": 100,
            }
            if cursor:
                params["cursor"] = cursor
            docs_resp = requests.get(
                f"{BASE_URL_V3}/workspaces/{CLICKUP_TEAM_ID}/docs",
                headers=headers(),
                params=params,
            )
            if not docs_resp.ok:
                break
            body = docs_resp.json()
            for d in body.get("docs", []):
                doc = {"id": d["id"], "name": d.get("name") or d.get("title", "")}
                parent = d.get("parent") or {}
                parent_type = parent.get("type")
                parent_id = str(parent.get("id", ""))
                if parent_type == 4 and parent_id in space_map:
                    space_map[parent_id]["docs"].append(doc)
                    doc_count += 1
                elif parent_type == 5 and parent_id in folder_map:
                    folder_map[parent_id]["docs"].append(doc)
                    doc_count += 1
            cursor = body.get("next_cursor")
            if not cursor:
                break
        print(f"  Fetched {doc_count} docs")
    except Exception:
        pass

    _hierarchy = {"spaces": spaces}
    os.makedirs(os.path.dirname(HIERARCHY_CACHE_PATH), exist_ok=True)
    with open(HIERARCHY_CACHE_PATH, "w") as f:
        json.dump(_hierarchy, f, indent=2)
    print(f"Hierarchy saved to {HIERARCHY_CACHE_PATH}")

    return _hierarchy


def get_hierarchy_index(force_refresh: bool = False) -> list[dict[str, Any]]:
    """Returns a flat list of all spaces, folders, lists, and docs with path breadcrumbs."""
    hierarchy = load_hierarchy(force_refresh)
    index: list[dict[str, Any]] = []

    for space in hierarchy.get("spaces", []):
        space_id = space["id"]
        index.append(
            {
                "type": "space",
                "id": space_id,
                "name": space["name"],
                "path": space["name"],
                "space_id": space_id,
            }
        )
        for doc in space.get("docs", []):
            index.append(
                {
                    "type": "doc",
                    "id": doc["id"],
                    "name": doc["name"],
                    "path": f"{space['name']} > {doc['name']}",
                    "space_id": space_id,
                }
            )
        for folder in space.get("folders", []):
            index.append(
                {
                    "type": "folder",
                    "id": folder["id"],
                    "name": folder["name"],
                    "path": f"{space['name']} > {folder['name']}",
                    "space_id": space_id,
                }
            )
            for doc in folder.get("docs", []):
                index.append(
                    {
                        "type": "doc",
                        "id": doc["id"],
                        "name": doc["name"],
                        "path": f"{space['name']} > {folder['name']} > {doc['name']}",
                        "space_id": space_id,
                    }
                )
            for lst in folder.get("lists", []):
                index.append(
                    {
                        "type": "list",
                        "id": lst["id"],
                        "name": lst["name"],
                        "path": f"{space['name']} > {folder['name']} > {lst['name']}",
                        "space_id": space_id,
                    }
                )
        for lst in space.get("lists", []):
            index.append(
                {
                    "type": "list",
                    "id": lst["id"],
                    "name": lst["name"],
                    "path": f"{space['name']} > {lst['name']}",
                    "space_id": space_id,
                }
            )

    return index
