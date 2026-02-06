import sys
import requests
from typing import Any
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    COMPANY_PROPERTIES,
    headers,
    format_company,
    validate_lead_status,
    validate_product_types,
    validate_icp_tier,
)


def update_company(
    company_id: str,
    name: str | None = None,
    domain: str | None = None,
    phone: str | None = None,
    city: str | None = None,
    state: str | None = None,
    annual_unit_volume: int | None = None,
    lead_status: str | None = None,
    product_types: list[str] | None = None,
    icp_tier: str | None = None,
) -> str:
    """
    Update an existing HubSpot company. Only provided fields will be updated.

    IMPORTANT: Lead Status is critical for sales tracking. Verify current status
    with get_company before changing.

    Args:
        company_id: HubSpot company ID (required)
        name: Company name
        domain: Website domain
        phone: Company phone number
        city: City location
        state: State/region
        annual_unit_volume: Number of units this developer builds per year
        lead_status: Sales stage - must be one of: Prospect, In Discovery,
                     In Proposal, Contract Sent, Active Customer, Revisit, Uninterested
        product_types: List of product types - each must be from:
                       Single Family, Multi-Family, Condo (low-rise), Condo (high-rise)
        icp_tier: Ideal Customer Profile tier - must be: Tier 1, Tier 2, or Tier 3
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    if lead_status:
        err = validate_lead_status(lead_status)
        if err:
            return f"Error: {err}"

    if product_types:
        err = validate_product_types(product_types)
        if err:
            return f"Error: {err}"

    internal_icp = None
    if icp_tier:
        internal_icp, err = validate_icp_tier(icp_tier)
        if err:
            return f"Error: {err}"

    properties: dict[str, Any] = {}
    if name:
        properties["name"] = name
    if domain:
        properties["domain"] = domain
    if phone:
        properties["phone"] = phone
    if city:
        properties["city"] = city
    if state:
        properties["state"] = state
    if annual_unit_volume is not None:
        properties["annual_unit_volume"] = str(annual_unit_volume)
    if lead_status:
        properties["hs_lead_status"] = lead_status
    if product_types:
        properties["product_types"] = ";".join(product_types)
    if internal_icp:
        properties["hs_ideal_customer_profile"] = internal_icp

    if not properties:
        return "Error: No properties to update"

    url = f"{BASE_URL}/crm/v3/objects/companies/{company_id}"
    payload: dict[str, Any] = {"properties": properties}

    resp = requests.patch(url, headers=headers(), json=payload)
    if resp.status_code == 404:
        return "Error: Company not found"
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    # Fetch full company to get all properties (PATCH only returns updated ones)
    get_resp = requests.get(
        url, headers=headers(), params={"properties": ",".join(COMPANY_PROPERTIES)}
    )
    if get_resp.status_code == 200:
        return format_company(get_resp.json())
    return format_company(resp.json())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("company_id")
    parser.add_argument("--name", "-n")
    parser.add_argument("--domain", "-d")
    parser.add_argument("--phone", "-p")
    parser.add_argument("--city")
    parser.add_argument("--state")
    parser.add_argument("--annual-units", type=int, dest="annual_unit_volume")
    parser.add_argument("--lead-status", "-s")
    parser.add_argument("--product-types", nargs="+")
    parser.add_argument("--icp-tier")
    args = parser.parse_args()

    print(
        update_company(
            args.company_id,
            args.name,
            args.domain,
            args.phone,
            args.city,
            args.state,
            args.annual_unit_volume,
            args.lead_status,
            args.product_types,
            args.icp_tier,
        )
    )
