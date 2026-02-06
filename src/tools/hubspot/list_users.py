import sys
import requests
from tools.hubspot import HUBSPOT_TOKEN, BASE_URL, headers


def list_users() -> str:
    """
    List all HubSpot users (owners) with their IDs.

    Returns a list of users with ID, name, and email for use in meeting assignments.
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    url = f"{BASE_URL}/crm/v3/owners"
    resp = requests.get(url, headers=headers())

    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    results = resp.json().get("results", [])
    if not results:
        return "No users found"

    lines = []
    for user in results:
        user_id = user.get("id")
        email = user.get("email", "")
        first = user.get("firstName", "")
        last = user.get("lastName", "")
        name = f"{first} {last}".strip() or "Unknown"
        lines.append(f"[{user_id}] {name} <{email}>")

    return "\n".join(lines)


if __name__ == "__main__":
    print(list_users())
