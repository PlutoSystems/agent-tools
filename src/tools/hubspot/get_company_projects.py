import sys
import requests
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    DEAL_PROPERTIES,
    headers,
    format_project,
)


def get_company_projects(company_id: str) -> str:
    """
    Get all projects (deals) associated with a company.

    Args:
        company_id: HubSpot company ID

    Returns:
        Formatted list of all projects linked to this company.
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    # Get associated deal IDs
    assoc_url = f"{BASE_URL}/crm/v3/objects/companies/{company_id}/associations/deals"
    assoc_resp = requests.get(assoc_url, headers=headers())

    if assoc_resp.status_code == 404:
        return "Error: Company not found"
    if assoc_resp.status_code != 200:
        return f"Error: {assoc_resp.status_code}"

    results = assoc_resp.json().get("results", [])
    if not results:
        return "No projects found for this company"

    deal_ids = [r["id"] for r in results]

    # Batch fetch deal details
    batch_url = f"{BASE_URL}/crm/v3/objects/deals/batch/read"
    batch_payload = {
        "properties": DEAL_PROPERTIES,
        "inputs": [{"id": deal_id} for deal_id in deal_ids],
    }

    batch_resp = requests.post(batch_url, headers=headers(), json=batch_payload)
    if batch_resp.status_code != 200:
        return f"Error fetching project details: {batch_resp.status_code}"

    deals = batch_resp.json().get("results", [])
    if not deals:
        return "No project details found"

    return "\n\n".join(format_project(deal) for deal in deals)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("company_id")
    args = parser.parse_args()

    print(get_company_projects(args.company_id))
