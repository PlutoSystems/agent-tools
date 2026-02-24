import sys
import requests
from tools.hubspot import HUBSPOT_TOKEN, BASE_URL, headers, MEETING_OUTCOMES

MEETING_PROPERTIES = [
    "hs_meeting_title",
    "hs_meeting_body",
    "hs_meeting_start_time",
    "hs_meeting_end_time",
    "hs_meeting_location",
    "hs_meeting_outcome",
    "hs_timestamp",
    "hubspot_owner_id",
]


def format_meeting(m: dict) -> str:
    props = m.get("properties", {})
    lines = [f"[{m['id']}] {props.get('hs_meeting_title', 'Untitled')}"]
    if props.get("hs_meeting_start_time"):
        start = props["hs_meeting_start_time"][:16].replace("T", " ")
        end_part = ""
        if props.get("hs_meeting_end_time"):
            end_part = f" - {props['hs_meeting_end_time'][11:16]}"
        lines.append(f"  Time: {start}{end_part}")
    elif props.get("hs_timestamp"):
        lines.append(f"  Date: {props['hs_timestamp'][:16].replace('T', ' ')}")
    if props.get("hs_meeting_location"):
        lines.append(f"  Location: {props['hs_meeting_location']}")
    if props.get("hs_meeting_outcome"):
        lines.append(f"  Outcome: {props['hs_meeting_outcome']}")
    if props.get("hs_meeting_body"):
        body = props["hs_meeting_body"][:200]
        lines.append(f"  Notes: {body}")
    return "\n".join(lines)


def search_meetings(
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
    outcome: str | None = None,
    after_date: str | None = None,
    before_date: str | None = None,
    limit: int = 10,
) -> str:
    """
    Search HubSpot meetings by association or filters.

    Args:
        contact_id: Find meetings associated with this contact
        company_id: Find meetings associated with this company
        deal_id: Find meetings associated with this deal/project
        outcome: Filter by outcome (SCHEDULED, COMPLETED, RESCHEDULED, NO_SHOW, CANCELLED)
        after_date: Only meetings after this date (YYYY-MM-DD)
        before_date: Only meetings before this date (YYYY-MM-DD)
        limit: Max results (default 10)

    At least one filter must be provided.
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    if outcome and outcome not in MEETING_OUTCOMES:
        return f"Error: Invalid outcome. Must be one of: {', '.join(MEETING_OUTCOMES)}"

    # If searching by association, use the associations endpoint then batch read
    if contact_id or company_id or deal_id:
        return _search_by_association(
            contact_id, company_id, deal_id, outcome, after_date, before_date, limit
        )

    # Otherwise use the search endpoint with filters
    filters: list[dict] = []
    if outcome:
        filters.append(
            {"propertyName": "hs_meeting_outcome", "operator": "EQ", "value": outcome}
        )
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
        return "Error: Provide at least one filter (contact_id, company_id, deal_id, outcome, or date range)"

    payload = {
        "filterGroups": [{"filters": filters}],
        "properties": MEETING_PROPERTIES,
        "sorts": [{"propertyName": "hs_timestamp", "direction": "DESCENDING"}],
        "limit": limit,
    }

    resp = requests.post(
        f"{BASE_URL}/crm/v3/objects/meetings/search", headers=headers(), json=payload
    )
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    results = resp.json().get("results", [])
    if not results:
        return "No meetings found"

    return "\n\n".join(format_meeting(m) for m in results)


def _search_by_association(
    contact_id: str | None,
    company_id: str | None,
    deal_id: str | None,
    outcome: str | None,
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

    assoc_url = f"{BASE_URL}/crm/v4/objects/{obj_type}/{obj_id}/associations/meetings"
    resp = requests.get(assoc_url, headers=headers(), params={"limit": 500})
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    ids = [r["toObjectId"] for r in resp.json().get("results", [])]
    if not ids:
        return "No meetings found"

    batch_url = f"{BASE_URL}/crm/v3/objects/meetings/batch/read"
    batch_resp = requests.post(
        batch_url,
        headers=headers(),
        json={
            "inputs": [{"id": mid} for mid in ids[: limit * 2]],
            "properties": MEETING_PROPERTIES,
        },
    )
    if batch_resp.status_code != 200:
        return f"Error: {batch_resp.status_code}"

    results = batch_resp.json().get("results", [])

    # Apply client-side filters
    if outcome:
        results = [
            m
            for m in results
            if m.get("properties", {}).get("hs_meeting_outcome") == outcome
        ]
    if after_date:
        results = [
            m
            for m in results
            if (m.get("properties", {}).get("hs_timestamp") or "") >= after_date
        ]
    if before_date:
        results = [
            m
            for m in results
            if (m.get("properties", {}).get("hs_timestamp") or "")
            <= f"{before_date}T23:59:59Z"
        ]

    results.sort(
        key=lambda m: m.get("properties", {}).get("hs_timestamp", ""), reverse=True
    )
    results = results[:limit]

    if not results:
        return "No meetings found"

    return "\n\n".join(format_meeting(m) for m in results)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--contact", "-c", dest="contact_id")
    parser.add_argument("--company", dest="company_id")
    parser.add_argument("--deal", "-d", dest="deal_id")
    parser.add_argument("--outcome", "-o")
    parser.add_argument("--after", dest="after_date")
    parser.add_argument("--before", dest="before_date")
    parser.add_argument("--limit", "-l", type=int, default=10)
    args = parser.parse_args()
    print(
        search_meetings(
            args.contact_id,
            args.company_id,
            args.deal_id,
            args.outcome,
            args.after_date,
            args.before_date,
            args.limit,
        )
    )
