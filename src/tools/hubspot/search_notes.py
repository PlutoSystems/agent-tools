import sys
import requests
from tools.hubspot import HUBSPOT_TOKEN, BASE_URL, headers

NOTE_PROPERTIES = [
    "hs_note_body",
    "hs_timestamp",
    "hubspot_owner_id",
]


def format_note(n: dict) -> str:
    props = n.get("properties", {})
    lines = [f"[{n['id']}]"]
    if props.get("hs_timestamp"):
        lines[0] += f" {props['hs_timestamp'][:16].replace('T', ' ')}"
    body = props.get("hs_note_body", "")
    if body:
        lines.append(f"  {body[:300]}")
    return "\n".join(lines)


def search_notes(
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
    after_date: str | None = None,
    before_date: str | None = None,
    limit: int = 10,
) -> str:
    """
    Search HubSpot notes by association or date range.

    Args:
        contact_id: Find notes associated with this contact
        company_id: Find notes associated with this company
        deal_id: Find notes associated with this deal/project
        after_date: Only notes after this date (YYYY-MM-DD)
        before_date: Only notes before this date (YYYY-MM-DD)
        limit: Max results (default 10)

    At least one filter must be provided.
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    if contact_id or company_id or deal_id:
        return _search_by_association(
            contact_id, company_id, deal_id, after_date, before_date, limit
        )

    filters: list[dict] = []
    if after_date:
        filters.append(
            {
                "propertyName": "hs_timestamp",
                "operator": "GTE",
                "value": f"{after_date}T00:00:00Z",
            }
        )
    if before_date:
        filters.append(
            {
                "propertyName": "hs_timestamp",
                "operator": "LTE",
                "value": f"{before_date}T23:59:59Z",
            }
        )

    if not filters:
        return "Error: Provide at least one filter (contact_id, company_id, deal_id, or date range)"

    payload = {
        "filterGroups": [{"filters": filters}],
        "properties": NOTE_PROPERTIES,
        "sorts": [{"propertyName": "hs_timestamp", "direction": "DESCENDING"}],
        "limit": limit,
    }

    resp = requests.post(
        f"{BASE_URL}/crm/v3/objects/notes/search", headers=headers(), json=payload
    )
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    results = resp.json().get("results", [])
    if not results:
        return "No notes found"

    return "\n\n".join(format_note(n) for n in results)


def _search_by_association(
    contact_id: str | None,
    company_id: str | None,
    deal_id: str | None,
    after_date: str | None,
    before_date: str | None,
    limit: int,
) -> str:
    obj_type, obj_id = None, None
    if contact_id:
        obj_type, obj_id = "contacts", contact_id
    elif company_id:
        obj_type, obj_id = "companies", company_id
    elif deal_id:
        obj_type, obj_id = "deals", deal_id

    assoc_url = f"{BASE_URL}/crm/v4/objects/{obj_type}/{obj_id}/associations/notes"
    resp = requests.get(assoc_url, headers=headers(), params={"limit": 500})
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    ids = [r["toObjectId"] for r in resp.json().get("results", [])]
    if not ids:
        return "No notes found"

    batch_url = f"{BASE_URL}/crm/v3/objects/notes/batch/read"
    batch_resp = requests.post(
        batch_url,
        headers=headers(),
        json={
            "inputs": [{"id": nid} for nid in ids[: limit * 2]],
            "properties": NOTE_PROPERTIES,
        },
    )
    if batch_resp.status_code != 200:
        return f"Error: {batch_resp.status_code}"

    results = batch_resp.json().get("results", [])

    if after_date:
        results = [
            n
            for n in results
            if (n.get("properties", {}).get("hs_timestamp") or "") >= after_date
        ]
    if before_date:
        results = [
            n
            for n in results
            if (n.get("properties", {}).get("hs_timestamp") or "")
            <= f"{before_date}T23:59:59Z"
        ]

    results.sort(
        key=lambda n: n.get("properties", {}).get("hs_timestamp", ""), reverse=True
    )
    results = results[:limit]

    if not results:
        return "No notes found"

    return "\n\n".join(format_note(n) for n in results)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--contact", "-c", dest="contact_id")
    parser.add_argument("--company", dest="company_id")
    parser.add_argument("--deal", "-d", dest="deal_id")
    parser.add_argument("--after", dest="after_date")
    parser.add_argument("--before", dest="before_date")
    parser.add_argument("--limit", "-l", type=int, default=10)
    args = parser.parse_args()
    print(
        search_notes(
            args.contact_id,
            args.company_id,
            args.deal_id,
            args.after_date,
            args.before_date,
            args.limit,
        )
    )
