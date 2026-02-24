import sys
import requests
from tools.hubspot import HUBSPOT_TOKEN, BASE_URL, headers, CALL_OUTCOMES

CALL_PROPERTIES = [
    "hs_call_title",
    "hs_call_body",
    "hs_call_duration",
    "hs_call_direction",
    "hs_call_disposition",
    "hs_call_status",
    "hs_timestamp",
]

CALL_OUTCOMES_REVERSE = {v: k for k, v in CALL_OUTCOMES.items()}


def format_call(c: dict) -> str:
    props = c.get("properties", {})
    lines = [f"[{c['id']}] {props.get('hs_call_title', 'Untitled')}"]
    if props.get("hs_timestamp"):
        lines.append(f"  Date: {props['hs_timestamp'][:16].replace('T', ' ')}")
    if props.get("hs_call_direction"):
        lines.append(f"  Direction: {props['hs_call_direction']}")
    if props.get("hs_call_duration"):
        try:
            mins = int(props["hs_call_duration"]) // 60000
            lines.append(f"  Duration: {mins} min")
        except ValueError:
            pass
    if props.get("hs_call_disposition"):
        outcome_label = CALL_OUTCOMES_REVERSE.get(
            props["hs_call_disposition"], props["hs_call_disposition"]
        )
        lines.append(f"  Outcome: {outcome_label}")
    if props.get("hs_call_body"):
        body = props["hs_call_body"][:200]
        lines.append(f"  Notes: {body}")
    return "\n".join(lines)


def search_calls(
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
    after_date: str | None = None,
    before_date: str | None = None,
    limit: int = 10,
) -> str:
    """
    Search HubSpot calls by association or date range.

    Args:
        contact_id: Find calls associated with this contact
        company_id: Find calls associated with this company
        deal_id: Find calls associated with this deal/project
        after_date: Only calls after this date (YYYY-MM-DD)
        before_date: Only calls before this date (YYYY-MM-DD)
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
        "properties": CALL_PROPERTIES,
        "sorts": [{"propertyName": "hs_timestamp", "direction": "DESCENDING"}],
        "limit": limit,
    }

    resp = requests.post(
        f"{BASE_URL}/crm/v3/objects/calls/search", headers=headers(), json=payload
    )
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    results = resp.json().get("results", [])
    if not results:
        return "No calls found"

    return "\n\n".join(format_call(c) for c in results)


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

    assoc_url = f"{BASE_URL}/crm/v4/objects/{obj_type}/{obj_id}/associations/calls"
    resp = requests.get(assoc_url, headers=headers(), params={"limit": 500})
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    ids = [r["toObjectId"] for r in resp.json().get("results", [])]
    if not ids:
        return "No calls found"

    batch_url = f"{BASE_URL}/crm/v3/objects/calls/batch/read"
    batch_resp = requests.post(
        batch_url,
        headers=headers(),
        json={
            "inputs": [{"id": cid} for cid in ids[: limit * 2]],
            "properties": CALL_PROPERTIES,
        },
    )
    if batch_resp.status_code != 200:
        return f"Error: {batch_resp.status_code}"

    results = batch_resp.json().get("results", [])

    if after_date:
        results = [
            c
            for c in results
            if (c.get("properties", {}).get("hs_timestamp") or "") >= after_date
        ]
    if before_date:
        results = [
            c
            for c in results
            if (c.get("properties", {}).get("hs_timestamp") or "")
            <= f"{before_date}T23:59:59Z"
        ]

    results.sort(
        key=lambda c: c.get("properties", {}).get("hs_timestamp", ""), reverse=True
    )
    results = results[:limit]

    if not results:
        return "No calls found"

    return "\n\n".join(format_call(c) for c in results)


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
        search_calls(
            args.contact_id,
            args.company_id,
            args.deal_id,
            args.after_date,
            args.before_date,
            args.limit,
        )
    )
