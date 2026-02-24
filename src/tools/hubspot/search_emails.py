import sys
import requests
from tools.hubspot import HUBSPOT_TOKEN, BASE_URL, headers

EMAIL_PROPERTIES = [
    "hs_email_subject",
    "hs_email_text",
    "hs_email_direction",
    "hs_email_status",
    "hs_email_sender_email",
    "hs_email_to_email",
    "hs_timestamp",
]


def format_email(e: dict) -> str:
    props = e.get("properties", {})
    subject = props.get("hs_email_subject", "No Subject")
    lines = [f"[{e['id']}] {subject}"]
    if props.get("hs_timestamp"):
        lines.append(f"  Date: {props['hs_timestamp'][:16].replace('T', ' ')}")
    direction = props.get("hs_email_direction", "")
    sender = props.get("hs_email_sender_email", "")
    to = props.get("hs_email_to_email", "")
    if direction == "INCOMING_EMAIL":
        lines.append(f"  From: {sender}")
    elif sender or to:
        lines.append(f"  From: {sender} → To: {to}")
    if props.get("hs_email_status"):
        lines.append(f"  Status: {props['hs_email_status']}")
    if props.get("hs_email_text"):
        lines.append(f"  Body: {props['hs_email_text'][:2000]}")
    return "\n".join(lines)


def search_emails(
    contact_id: str | None = None,
    company_id: str | None = None,
    subject: str | None = None,
    after_date: str | None = None,
    before_date: str | None = None,
    limit: int = 10,
) -> str:
    """
    Search HubSpot emails by association, subject, or date range.

    Args:
        contact_id: Find emails associated with this contact
        company_id: Find emails associated with this company
        subject: Search by email subject (partial match)
        after_date: Only emails after this date (YYYY-MM-DD)
        before_date: Only emails before this date (YYYY-MM-DD)
        limit: Max results (default 10)

    At least one filter must be provided.
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    if contact_id or company_id:
        return _search_by_association(
            contact_id, company_id, subject, after_date, before_date, limit
        )

    filters: list[dict] = []
    if subject:
        filters.append(
            {
                "propertyName": "hs_email_subject",
                "operator": "CONTAINS_TOKEN",
                "value": subject,
            }
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
        return "Error: Provide at least one filter (contact_id, company_id, subject, or date range)"

    payload = {
        "filterGroups": [{"filters": filters}],
        "properties": EMAIL_PROPERTIES,
        "sorts": [{"propertyName": "hs_timestamp", "direction": "DESCENDING"}],
        "limit": limit,
    }

    resp = requests.post(
        f"{BASE_URL}/crm/v3/objects/emails/search", headers=headers(), json=payload
    )
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    results = resp.json().get("results", [])
    if not results:
        return "No emails found"

    return "\n\n".join(format_email(e) for e in results)


def _search_by_association(
    contact_id: str | None,
    company_id: str | None,
    subject: str | None,
    after_date: str | None,
    before_date: str | None,
    limit: int,
) -> str:
    obj_type, obj_id = None, None
    if contact_id:
        obj_type, obj_id = "contacts", contact_id
    elif company_id:
        obj_type, obj_id = "companies", company_id

    assoc_url = f"{BASE_URL}/crm/v4/objects/{obj_type}/{obj_id}/associations/emails"
    resp = requests.get(assoc_url, headers=headers(), params={"limit": 500})
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    ids = [r["toObjectId"] for r in resp.json().get("results", [])]
    if not ids:
        return "No emails found"

    batch_url = f"{BASE_URL}/crm/v3/objects/emails/batch/read"
    batch_resp = requests.post(
        batch_url,
        headers=headers(),
        json={
            "inputs": [{"id": eid} for eid in ids[: limit * 3]],
            "properties": EMAIL_PROPERTIES,
        },
    )
    if batch_resp.status_code != 200:
        return f"Error: {batch_resp.status_code}"

    results = batch_resp.json().get("results", [])

    if subject:
        subject_lower = subject.lower()
        results = [
            e
            for e in results
            if subject_lower
            in (e.get("properties", {}).get("hs_email_subject") or "").lower()
        ]
    if after_date:
        results = [
            e
            for e in results
            if (e.get("properties", {}).get("hs_timestamp") or "") >= after_date
        ]
    if before_date:
        results = [
            e
            for e in results
            if (e.get("properties", {}).get("hs_timestamp") or "")
            <= f"{before_date}T23:59:59Z"
        ]

    results.sort(
        key=lambda e: e.get("properties", {}).get("hs_timestamp", ""), reverse=True
    )
    results = results[:limit]

    if not results:
        return "No emails found"

    return "\n\n".join(format_email(e) for e in results)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--contact", "-c", dest="contact_id")
    parser.add_argument("--company", dest="company_id")
    parser.add_argument("--subject", "-s")
    parser.add_argument("--after", dest="after_date")
    parser.add_argument("--before", dest="before_date")
    parser.add_argument("--limit", "-l", type=int, default=10)
    args = parser.parse_args()
    print(
        search_emails(
            args.contact_id,
            args.company_id,
            args.subject,
            args.after_date,
            args.before_date,
            args.limit,
        )
    )
