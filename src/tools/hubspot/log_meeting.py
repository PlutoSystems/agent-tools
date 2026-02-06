import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import requests
from typing import Any
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    headers,
    build_associations,
    MEETING_OUTCOMES,
)


def _to_utc(time_str: str, tz: ZoneInfo) -> str:
    """Convert a local datetime string to UTC format for HubSpot."""
    # Parse without timezone, then localize
    dt = datetime.strptime(time_str.rstrip("Z"), "%Y-%m-%dT%H:%M:%S")
    local_dt = dt.replace(tzinfo=tz)
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def log_meeting(
    title: str,
    body: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    location: str | None = None,
    outcome: str | None = None,
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
    tz: str = "America/Edmonton",
    owner_id: str | None = None,
    attendee_ids: list[str] | None = None,
) -> str:
    """
    Log a meeting to HubSpot.

    Args:
        title: Meeting title (required)
        body: Meeting notes/description
        start_time: When the meeting started in LOCAL time (format: YYYY-MM-DDTHH:MM:SS)
        end_time: When the meeting ended in LOCAL time (format: YYYY-MM-DDTHH:MM:SS)
        location: Meeting location (room, Zoom link, address, etc.)
        outcome: Must be one of: SCHEDULED, COMPLETED, RESCHEDULED, NO_SHOW, CANCELLED
        contact_id: Associate with this contact
        company_id: Associate with this company
        deal_id: Associate with this project/deal
        tz: IANA timezone name for the provided times (default: America/Edmonton for MST/MDT)
        owner_id: HubSpot user ID for meeting organizer (use hubspot_list_users to find IDs)
        attendee_ids: List of HubSpot user IDs for internal staff attendees

    At least one of contact_id, company_id, or deal_id must be provided.
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    if not any([contact_id, company_id, deal_id]):
        return "Error: Must provide at least one of contact_id, company_id, or deal_id"

    if outcome and outcome not in MEETING_OUTCOMES:
        return f"Error: Invalid outcome. Must be one of: {', '.join(MEETING_OUTCOMES)}"

    url = f"{BASE_URL}/crm/v3/objects/meetings"

    try:
        local_tz = ZoneInfo(tz)
    except Exception:
        return f"Error: Invalid timezone '{tz}'"

    # Convert times to UTC
    if start_time:
        start_utc = _to_utc(start_time, local_tz)
    else:
        start_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    properties: dict[str, Any] = {
        "hs_timestamp": start_utc,
        "hs_meeting_title": title,
    }

    if body:
        properties["hs_meeting_body"] = body
    if start_time:
        properties["hs_meeting_start_time"] = start_utc
    if end_time:
        properties["hs_meeting_end_time"] = _to_utc(end_time, local_tz)
    if location:
        properties["hs_meeting_location"] = location
    if outcome:
        properties["hs_meeting_outcome"] = outcome
    if owner_id:
        properties["hubspot_owner_id"] = owner_id
    if attendee_ids:
        properties["hs_attendee_owner_ids"] = ";".join(attendee_ids)

    payload: dict[str, Any] = {
        "properties": properties,
        "associations": build_associations("meeting", contact_id, company_id, deal_id),
    }

    resp = requests.post(url, headers=headers(), json=payload)
    if resp.status_code != 201:
        return f"Error: {resp.status_code}"

    return f"Meeting logged successfully [ID: {resp.json()['id']}]"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("title")
    parser.add_argument("--body", "-b")
    parser.add_argument("--start", dest="start_time")
    parser.add_argument("--end", dest="end_time")
    parser.add_argument("--location", "-l")
    parser.add_argument("--outcome", "-o")
    parser.add_argument("--contact", "-c", dest="contact_id")
    parser.add_argument("--company", dest="company_id")
    parser.add_argument("--deal", "-d", dest="deal_id")
    parser.add_argument("--tz", default="America/Edmonton")
    parser.add_argument("--owner", dest="owner_id")
    parser.add_argument("--attendees", nargs="+", dest="attendee_ids")
    args = parser.parse_args()

    print(
        log_meeting(
            args.title,
            args.body,
            args.start_time,
            args.end_time,
            args.location,
            args.outcome,
            args.contact_id,
            args.company_id,
            args.deal_id,
            args.tz,
            args.owner_id,
            args.attendee_ids,
        )
    )
