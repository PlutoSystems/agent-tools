import sys
import requests
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    CONTACT_PROPERTIES,
    headers,
    format_contact,
    get_company_name,
    get_recent_engagement,
)


def get_contact(contact_id: str) -> str:
    """Get a HubSpot contact by ID with company and recent activity."""
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    url = f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}"
    params = {"properties": ",".join(CONTACT_PROPERTIES), "associations": "companies"}

    resp = requests.get(url, headers=headers(), params=params)
    if resp.status_code == 404:
        return "Error: Contact not found"
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    data = resp.json()
    output = [format_contact(data)]

    companies = data.get("associations", {}).get("companies", {}).get("results", [])
    if companies:
        company_name = get_company_name(companies[0]["id"])
        if company_name:
            output.append(f"Company: {company_name}")

    activity = get_recent_engagement(contact_id)
    if activity:
        output.append(f"Recent: {activity}")

    return "\n".join(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_contact.py <contact_id>")
        sys.exit(1)
    print(get_contact(sys.argv[1]))
