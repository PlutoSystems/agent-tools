import sys
import json
import requests
from tools.ms_graph.auth import auth_headers, GRAPH_BASE

SCOPES = [
    "https://graph.microsoft.com/Channel.ReadBasic.All",
]


def list_channels(team_id: str) -> str:
    headers = auth_headers(SCOPES)
    url = f"{GRAPH_BASE}/teams/{team_id}/channels"

    all_channels: list[dict[str, str | bool]] = []

    while url:
        resp = requests.get(url, headers=headers)
        if not resp.ok:
            return f"Error fetching channels: {resp.status_code} {resp.text}"

        data = resp.json()
        for ch in data.get("value", []):
            all_channels.append(
                {
                    "id": ch["id"],
                    "name": ch.get("displayName", ""),
                    "description": ch.get("description", "") or "",
                    "membershipType": ch.get("membershipType", ""),
                    "webUrl": ch.get("webUrl", ""),
                    "isArchived": ch.get("isArchived", False),
                }
            )
        url = data.get("@odata.nextLink")

    all_channels.sort(key=lambda c: c["name"].lower())
    return json.dumps({"count": len(all_channels), "channels": all_channels}, indent=2)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python list_channels.py <TEAM_ID>")
        sys.exit(1)
    print(list_channels(sys.argv[1]))
