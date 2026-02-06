import os
import requests
from dotenv import load_dotenv

load_dotenv()

HUBSPOT_TOKEN = os.getenv("HUBSPOT_ACCESS_TOKEN")
BASE_URL = os.getenv("HUBSPOT_BASE_URL", "https://api.hubapi.com")

CONTACT_PROPERTIES = ["firstname", "lastname", "email", "phone", "jobtitle"]

COMPANY_PROPERTIES = [
    "name",
    "domain",
    "phone",
    "city",
    "state",
    "annual_unit_volume",
    "hs_lead_status",
    "hs_ideal_customer_profile",
    "product_types",
    "hubspot_owner_id",
]

LEAD_STATUS_VALUES = [
    "Prospect",
    "In Discovery",
    "In Proposal",
    "Contract Sent",
    "Active Customer",
    "Revisit",
    "Uninterested",
]

PRODUCT_TYPE_VALUES = [
    "Single Family",
    "Multi-Family",
    "Condo (low-rise)",
    "Condo (high-rise)",
]

DEAL_PROPERTIES = [
    "dealname",
    "dealstage",
    "launch_date",
    "number_of_units",
    "product_type",
    "city",
    "google_maps_link",
]

# Maps user-friendly stage labels to HubSpot internal names
DEAL_STAGES = {
    "Rumored": "appointmentscheduled",
    "Confirmed": "qualifiedtobuy",
    "Pursuing": "presentationscheduled",
    "Quoted": "decisionmakerboughtin",
    "Active on Pluto": "contractsent",
    "Closed Lost": "closedlost",
    "Cancelled": "1295465318",
}

# Reverse mapping for display
DEAL_STAGES_REVERSE = {v: k for k, v in DEAL_STAGES.items()}

# ICP Tier mapping (label -> internal)
ICP_TIERS = {
    "Tier 1": "tier_1",
    "Tier 2": "tier_2",
    "Tier 3": "tier_3",
}
ICP_TIERS_REVERSE = {v: k for k, v in ICP_TIERS.items()}

# Association type IDs for engagements
ASSOC_IDS = {
    "note": {"contact": 202, "company": 190, "deal": 214},
    "call": {"contact": 194, "company": 182, "deal": 206},
    "meeting": {"contact": 200, "company": 188, "deal": 212},
}

CALL_OUTCOMES = {
    "Connected": "f240bbac-87c9-4f6e-bf70-924b57d47db7",
    "Busy": "9d9162e7-6cf3-4944-bf63-4dff82258764",
    "No answer": "73a0d17f-1163-4015-bdd5-ec830791da20",
    "Left voicemail": "b2cf5968-551e-4856-9783-c0ac3b8c2e9c",
    "Left live message": "a4c4c377-d246-4b32-a13b-75a56a4cd0ff",
    "Wrong number": "17b47fee-58de-441e-a44c-c6300d46f273",
}

MEETING_OUTCOMES = ["SCHEDULED", "COMPLETED", "RESCHEDULED", "NO_SHOW", "CANCELLED"]


def build_associations(
    engagement_type: str,
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
) -> list[dict]:
    """Build associations array for engagement creation."""
    associations = []
    ids = ASSOC_IDS[engagement_type]

    if contact_id:
        associations.append(
            {
                "to": {"id": contact_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": ids["contact"],
                    }
                ],
            }
        )
    if company_id:
        associations.append(
            {
                "to": {"id": company_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": ids["company"],
                    }
                ],
            }
        )
    if deal_id:
        associations.append(
            {
                "to": {"id": deal_id},
                "types": [
                    {
                        "associationCategory": "HUBSPOT_DEFINED",
                        "associationTypeId": ids["deal"],
                    }
                ],
            }
        )

    return associations


def headers():
    return {
        "Authorization": f"Bearer {HUBSPOT_TOKEN}",
        "Content-Type": "application/json",
    }


def format_contact(contact: dict) -> str:
    props = contact.get("properties", {})
    name = f"{props.get('firstname', '')} {props.get('lastname', '')}".strip()
    return f"[{contact['id']}] {name} | {props.get('email', '')} | {props.get('jobtitle', '')}"


def format_company(company: dict) -> str:
    props = company.get("properties", {})
    lines = [f"[{company['id']}] {props.get('name', 'Unnamed')}"]
    if props.get("domain"):
        lines.append(f"  Website: {props['domain']}")
    if props.get("city") or props.get("state"):
        lines.append(
            f"  Location: {props.get('city', '')} {props.get('state', '')}".strip()
        )
    if props.get("hs_lead_status"):
        lines.append(f"  Lead Status: {props['hs_lead_status']}")
    if props.get("hs_ideal_customer_profile"):
        icp_label = ICP_TIERS_REVERSE.get(
            props["hs_ideal_customer_profile"], props["hs_ideal_customer_profile"]
        )
        lines.append(f"  ICP Tier: {icp_label}")
    if props.get("annual_unit_volume"):
        lines.append(f"  Annual Units: {props['annual_unit_volume']}")
    if props.get("product_types"):
        lines.append(f"  Product Types: {props['product_types']}")
    return "\n".join(lines)


def validate_lead_status(value: str) -> str | None:
    if value not in LEAD_STATUS_VALUES:
        return f"Invalid lead status. Must be one of: {', '.join(LEAD_STATUS_VALUES)}"
    return None


def validate_product_types(values: list[str]) -> str | None:
    invalid = [v for v in values if v not in PRODUCT_TYPE_VALUES]
    if invalid:
        return f"Invalid product types: {invalid}. Must be from: {', '.join(PRODUCT_TYPE_VALUES)}"
    return None


def validate_icp_tier(value: str) -> tuple[str | None, str | None]:
    """Returns (internal_name, error). If valid, error is None."""
    if value not in ICP_TIERS:
        return None, f"Invalid ICP tier. Must be one of: {', '.join(ICP_TIERS.keys())}"
    return ICP_TIERS[value], None


def validate_product_type(value: str) -> str | None:
    if value not in PRODUCT_TYPE_VALUES:
        return f"Invalid product type. Must be one of: {', '.join(PRODUCT_TYPE_VALUES)}"
    return None


def validate_deal_stage(value: str) -> tuple[str | None, str | None]:
    """Returns (internal_name, error). If valid, error is None."""
    if value not in DEAL_STAGES:
        return None, f"Invalid stage. Must be one of: {', '.join(DEAL_STAGES.keys())}"
    return DEAL_STAGES[value], None


def format_project(deal: dict) -> str:
    props = deal.get("properties", {})
    lines = [f"[{deal['id']}] {props.get('dealname', 'Unnamed Project')}"]
    if props.get("dealstage"):
        stage_label = DEAL_STAGES_REVERSE.get(props["dealstage"], props["dealstage"])
        lines.append(f"  Stage: {stage_label}")
    if props.get("city"):
        lines.append(f"  City: {props['city']}")
    if props.get("number_of_units"):
        lines.append(f"  Units: {props['number_of_units']}")
    if props.get("product_type"):
        lines.append(f"  Product Type: {props['product_type']}")
    if props.get("launch_date"):
        lines.append(f"  Launch Date: {props['launch_date']}")
    if props.get("google_maps_link"):
        lines.append(f"  Map: {props['google_maps_link']}")
    return "\n".join(lines)


def get_company_name(company_id: str) -> str | None:
    url = f"{BASE_URL}/crm/v3/objects/companies/{company_id}"
    resp = requests.get(url, headers=headers(), params={"properties": "name"})
    if resp.status_code != 200:
        return None
    return resp.json().get("properties", {}).get("name")


def get_recent_engagement(contact_id: str) -> str | None:
    url = f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}/associations/engagements"
    resp = requests.get(url, headers=headers())
    if resp.status_code != 200 or not resp.json().get("results"):
        return None

    engagement_id = resp.json()["results"][0]["id"]
    eng_url = f"{BASE_URL}/crm/v3/objects/engagements/{engagement_id}"
    eng_resp = requests.get(
        eng_url,
        headers=headers(),
        params={"properties": "hs_engagement_type,hs_timestamp,hs_body_preview"},
    )
    if eng_resp.status_code != 200:
        return None

    props = eng_resp.json().get("properties", {})
    eng_type = props.get("hs_engagement_type", "Activity")
    preview = props.get("hs_body_preview", "")[:100]
    return f"{eng_type}: {preview}" if preview else eng_type
