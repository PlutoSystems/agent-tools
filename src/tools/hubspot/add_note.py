import sys
from datetime import datetime, timezone
import requests
from typing import Any
from tools.hubspot import HUBSPOT_TOKEN, BASE_URL, headers, build_associations


def add_note(
    body: str,
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
) -> str:
    """
    Add a note to a HubSpot record.

    Args:
        body: Note text content (required)
        contact_id: Associate with this contact
        company_id: Associate with this company
        deal_id: Associate with this project/deal

    At least one of contact_id, company_id, or deal_id must be provided.
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    if not any([contact_id, company_id, deal_id]):
        return "Error: Must provide at least one of contact_id, company_id, or deal_id"

    url = f"{BASE_URL}/crm/v3/objects/notes"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    payload: dict[str, Any] = {
        "properties": {
            "hs_timestamp": timestamp,
            "hs_note_body": body,
        },
        "associations": build_associations("note", contact_id, company_id, deal_id),
    }

    resp = requests.post(url, headers=headers(), json=payload)
    if resp.status_code != 201:
        return f"Error: {resp.status_code}"

    return f"Note added successfully [ID: {resp.json()['id']}]"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("body")
    parser.add_argument("--contact", "-c", dest="contact_id")
    parser.add_argument("--company", "-o", dest="company_id")
    parser.add_argument("--deal", "-d", dest="deal_id")
    args = parser.parse_args()

    print(add_note(args.body, args.contact_id, args.company_id, args.deal_id))
