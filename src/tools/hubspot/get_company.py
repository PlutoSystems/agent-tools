import sys
import requests
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    COMPANY_PROPERTIES,
    headers,
    format_company,
    get_recent_engagement,
)


def get_company(company_id: str) -> str:
    """
    Get a HubSpot company by ID with full property details.

    Returns company info including:
    - Name, website domain, phone
    - City, state/region
    - Lead Status (sales pipeline stage)
    - Annual Unit Volume (units built per year)
    - Product Types (Single Family, Multi-Family, Condo low/high-rise)
    - ICP Tier (ideal customer profile match)
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    url = f"{BASE_URL}/crm/v3/objects/companies/{company_id}"
    params = {"properties": ",".join(COMPANY_PROPERTIES)}

    resp = requests.get(url, headers=headers(), params=params)
    if resp.status_code == 404:
        return "Error: Company not found"
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    return format_company(resp.json())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python get_company.py <company_id>")
        sys.exit(1)
    print(get_company(sys.argv[1]))
