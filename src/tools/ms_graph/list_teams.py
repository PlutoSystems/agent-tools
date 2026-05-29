import sys
import json
import requests
from tools.ms_graph.auth import auth_headers, GRAPH_BASE

SCOPES = [
    "https://graph.microsoft.com/Team.ReadBasic.All",
    "https://graph.microsoft.com/User.Read",
]


def list_my_teams() -> str:
    headers = auth_headers(SCOPES)
    url = f"{GRAPH_BASE}/me/joinedTeams"

    all_teams: list[dict[str, str]] = []

    while url:
        resp = requests.get(url, headers=headers)
        if not resp.ok:
            return f"Error fetching teams: {resp.status_code} {resp.text}"

        data = resp.json()
        for team in data.get("value", []):
            all_teams.append(
                {
                    "id": team["id"],
                    "name": team.get("displayName", ""),
                    "description": team.get("description", "") or "",
                    "visibility": team.get("visibility", ""),
                    "webUrl": team.get("webUrl", ""),
                    "isArchived": team.get("isArchived", False),
                }
            )
        url = data.get("@odata.nextLink")

    all_teams.sort(key=lambda t: t["name"].lower())
    return json.dumps({"count": len(all_teams), "teams": all_teams}, indent=2)


if __name__ == "__main__":
    print(list_my_teams())
