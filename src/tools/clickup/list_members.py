import sys
import json
import requests
from tools.clickup import CLICKUP_API_KEY, CLICKUP_TEAM_ID, BASE_URL, headers


def list_members() -> str:
    if not CLICKUP_API_KEY:
        return "Error: CLICKUP_API_KEY not set"

    resp = requests.get(f"{BASE_URL}/team", headers=headers())
    if not resp.ok:
        return f"Error fetching members: {resp.text}"

    teams = resp.json().get("teams", [])
    target = CLICKUP_TEAM_ID
    members = []
    for team in teams:
        if target and str(team.get("id")) != str(target):
            continue
        for member in team.get("members", []):
            user = member.get("user", {})
            members.append(
                {
                    "id": user.get("id"),
                    "username": user.get("username"),
                    "email": user.get("email"),
                    "role": member.get("role", user.get("role")),
                }
            )

    return json.dumps(members, indent=2)


if __name__ == "__main__":
    print(list_members())
