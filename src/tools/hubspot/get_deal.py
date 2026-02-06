import sys
import requests
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    DEAL_PROPERTIES,
    headers,
    format_project,
    get_company_name,
)


def get_project(deal_id: str) -> str:
    """
    Get a real estate project by ID.

    Returns project details including:
    - Project name
    - Stage (Rumored, Confirmed, Pursuing, Quoted, Active on Pluto, Closed Lost, Cancelled)
    - City location
    - Number of units
    - Product type (Single Family, Multi-Family, Condo low/high-rise)
    - Launch date (public sales date, not construction start)
    - Google Maps link
    - Associated company
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    url = f"{BASE_URL}/crm/v3/objects/deals/{deal_id}"
    params = {
        "properties": ",".join(DEAL_PROPERTIES),
        "associations": "companies",
    }

    resp = requests.get(url, headers=headers(), params=params)
    if resp.status_code == 404:
        return "Error: Project not found"
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    data = resp.json()
    output = [format_project(data)]

    companies = data.get("associations", {}).get("companies", {}).get("results", [])
    if companies:
        company_name = get_company_name(companies[0]["id"])
        if company_name:
            output.append(f"  Company: {company_name}")

    return "\n".join(output)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_deal.py <deal_id>")
        sys.exit(1)
    print(get_project(sys.argv[1]))
