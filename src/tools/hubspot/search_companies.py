import sys
import requests
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    COMPANY_PROPERTIES,
    LEAD_STATUS_VALUES,
    headers,
    format_company,
)


def search_companies(
    query: str | None = None, lead_status: str | None = None, limit: int = 10
) -> str:
    """
    Search HubSpot companies by name/domain or filter by lead status.

    Args:
        query: Search term to match against company name or domain
        lead_status: Filter by lead status (Prospect, In Discovery, In Proposal,
                     Contract Sent, Active Customer, Revisit, Uninterested)
        limit: Max results to return (default 10)
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    url = f"{BASE_URL}/crm/v3/objects/companies/search"

    filter_groups = []

    if query:
        filter_groups.extend(
            [
                {
                    "filters": [
                        {
                            "propertyName": "name",
                            "operator": "CONTAINS_TOKEN",
                            "value": query,
                        }
                    ]
                },
                {
                    "filters": [
                        {
                            "propertyName": "domain",
                            "operator": "CONTAINS_TOKEN",
                            "value": query,
                        }
                    ]
                },
            ]
        )

    if lead_status:
        if lead_status not in LEAD_STATUS_VALUES:
            return f"Error: Invalid lead_status. Must be one of: {', '.join(LEAD_STATUS_VALUES)}"
        filter_groups.append(
            {
                "filters": [
                    {
                        "propertyName": "hs_lead_status",
                        "operator": "EQ",
                        "value": lead_status,
                    }
                ]
            }
        )

    if not filter_groups:
        return "Error: Provide either query or lead_status"

    payload = {
        "filterGroups": filter_groups,
        "properties": COMPANY_PROPERTIES,
        "limit": limit,
    }

    resp = requests.post(url, headers=headers(), json=payload)
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    results = resp.json().get("results", [])
    if not results:
        return "No companies found"

    return "\n\n".join(format_company(c) for c in results)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--query", "-q")
    parser.add_argument("--lead-status", "-s")
    parser.add_argument("--limit", "-l", type=int, default=10)
    args = parser.parse_args()
    print(search_companies(args.query, args.lead_status, args.limit))
