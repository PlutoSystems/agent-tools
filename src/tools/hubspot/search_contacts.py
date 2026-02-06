import sys
import requests
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    CONTACT_PROPERTIES,
    headers,
    format_contact,
)


def search_contacts(query: str, limit: int = 10) -> str:
    """Search HubSpot contacts by name or email."""
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    url = f"{BASE_URL}/crm/v3/objects/contacts/search"
    payload = {
        "filterGroups": [
            {
                "filters": [
                    {
                        "propertyName": "email",
                        "operator": "CONTAINS_TOKEN",
                        "value": query,
                    }
                ]
            },
            {
                "filters": [
                    {
                        "propertyName": "firstname",
                        "operator": "CONTAINS_TOKEN",
                        "value": query,
                    }
                ]
            },
            {
                "filters": [
                    {
                        "propertyName": "lastname",
                        "operator": "CONTAINS_TOKEN",
                        "value": query,
                    }
                ]
            },
        ],
        "properties": CONTACT_PROPERTIES,
        "limit": limit,
    }

    resp = requests.post(url, headers=headers(), json=payload)
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    results = resp.json().get("results", [])
    if not results:
        return "No contacts found"

    return "\n".join(format_contact(c) for c in results)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python search_contacts.py <query>")
        sys.exit(1)
    print(search_contacts(sys.argv[1]))
