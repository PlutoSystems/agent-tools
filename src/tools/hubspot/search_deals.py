import sys
import requests
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    DEAL_PROPERTIES,
    DEAL_STAGES,
    headers,
    format_project,
)


def search_projects(
    query: str | None = None,
    stage: str | None = None,
    limit: int = 10,
) -> str:
    """
    Search real estate projects by name or filter by stage.

    Args:
        query: Search term to match against project name
        stage: Filter by project stage - must be one of: Rumored, Confirmed,
               Pursuing, Quoted, Active on Pluto, Closed Lost, Cancelled
        limit: Max results to return (default 10)
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    url = f"{BASE_URL}/crm/v3/objects/deals/search"

    filter_groups = []

    if query:
        filter_groups.append(
            {
                "filters": [
                    {
                        "propertyName": "dealname",
                        "operator": "CONTAINS_TOKEN",
                        "value": query,
                    }
                ]
            }
        )

    if stage:
        if stage not in DEAL_STAGES:
            return (
                f"Error: Invalid stage. Must be one of: {', '.join(DEAL_STAGES.keys())}"
            )
        filter_groups.append(
            {
                "filters": [
                    {
                        "propertyName": "dealstage",
                        "operator": "EQ",
                        "value": DEAL_STAGES[stage],
                    }
                ]
            }
        )

    if not filter_groups:
        return "Error: Provide either query or stage"

    payload = {
        "filterGroups": filter_groups,
        "properties": DEAL_PROPERTIES,
        "limit": limit,
    }

    resp = requests.post(url, headers=headers(), json=payload)
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    results = resp.json().get("results", [])
    if not results:
        return "No projects found"

    return "\n\n".join(format_project(d) for d in results)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--query", "-q")
    parser.add_argument("--stage", "-s")
    parser.add_argument("--limit", "-l", type=int, default=10)
    args = parser.parse_args()
    print(search_projects(args.query, args.stage, args.limit))
