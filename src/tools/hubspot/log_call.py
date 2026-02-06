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
    CALL_OUTCOMES,
)


def _to_utc(time_str: str, tz: ZoneInfo) -> str:
    """Convert a local datetime string to UTC format for HubSpot."""
    dt = datetime.strptime(time_str.rstrip("Z"), "%Y-%m-%dT%H:%M:%S")
    local_dt = dt.replace(tzinfo=tz)
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def log_call(
    title: str,
    body: str | None = None,
    duration_minutes: int | None = None,
    outcome: str | None = None,
    direction: str | None = None,
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
    call_time: str | None = None,
    tz: str = "America/Edmonton",
) -> str:
    """
    Log a phone call to HubSpot.

    Args:
        title: Call title/subject (required)
        body: Call notes/description
        duration_minutes: Length of call in minutes
        outcome: Must be one of: Connected, Busy, No answer, Left voicemail,
                 Left live message, Wrong number
        direction: INBOUND or OUTBOUND
        contact_id: Associate with this contact
        company_id: Associate with this company
        deal_id: Associate with this project/deal
        call_time: When the call happened in LOCAL time (format: YYYY-MM-DDTHH:MM:SS)
        tz: IANA timezone name for call_time (default: America/Edmonton for MST/MDT)

    At least one of contact_id, company_id, or deal_id must be provided.
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    if not any([contact_id, company_id, deal_id]):
        return "Error: Must provide at least one of contact_id, company_id, or deal_id"

    if outcome and outcome not in CALL_OUTCOMES:
        return (
            f"Error: Invalid outcome. Must be one of: {', '.join(CALL_OUTCOMES.keys())}"
        )

    if direction and direction not in ["INBOUND", "OUTBOUND"]:
        return "Error: direction must be INBOUND or OUTBOUND"

    url = f"{BASE_URL}/crm/v3/objects/calls"

    # Convert call_time to UTC or use current time
    if call_time:
        try:
            local_tz = ZoneInfo(tz)
        except Exception:
            return f"Error: Invalid timezone '{tz}'"
        timestamp = _to_utc(call_time, local_tz)
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

    properties: dict[str, Any] = {
        "hs_timestamp": timestamp,
        "hs_call_title": title,
        "hs_call_status": "COMPLETED",
    }

    if body:
        properties["hs_call_body"] = body
    if duration_minutes is not None:
        properties["hs_call_duration"] = str(
            duration_minutes * 60 * 1000
        )  # Convert to ms
    if outcome:
        properties["hs_call_disposition"] = CALL_OUTCOMES[outcome]
    if direction:
        properties["hs_call_direction"] = direction

    payload: dict[str, Any] = {
        "properties": properties,
        "associations": build_associations("call", contact_id, company_id, deal_id),
    }

    resp = requests.post(url, headers=headers(), json=payload)
    if resp.status_code != 201:
        return f"Error: {resp.status_code}"

    return f"Call logged successfully [ID: {resp.json()['id']}]"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("title")
    parser.add_argument("--body", "-b")
    parser.add_argument("--duration", "-m", type=int, dest="duration_minutes")
    parser.add_argument("--outcome", "-o")
    parser.add_argument("--direction", "-dir")
    parser.add_argument("--contact", "-c", dest="contact_id")
    parser.add_argument("--company", dest="company_id")
    parser.add_argument("--deal", "-d", dest="deal_id")
    parser.add_argument("--time", dest="call_time")
    parser.add_argument("--tz", default="America/Edmonton")
    args = parser.parse_args()

    print(
        log_call(
            args.title,
            args.body,
            args.duration_minutes,
            args.outcome,
            args.direction,
            args.contact_id,
            args.company_id,
            args.deal_id,
            args.call_time,
            args.tz,
        )
    )
