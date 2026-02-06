import sys
import requests
from typing import Any
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    headers,
    format_company,
    validate_lead_status,
    validate_product_types,
    validate_icp_tier,
)


def create_company(
    name: str,
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
    Create a new HubSpot company.

    Args:
        name: Company name (required)
        domain: Website domain (e.g. "acme.com")
        phone: Company phone number
        city: City location
        state: State/region
        annual_unit_volume: Number of units this developer builds per year
        lead_status: Sales stage - must be one of: Prospect, In Discovery,
                     In Proposal, Contract Sent, Active Customer, Revisit, Uninterested
        product_types: List of product types built - each must be from:
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

    url = f"{BASE_URL}/crm/v3/objects/companies"

    properties: dict[str, Any] = {"name": name}
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

    payload: dict[str, Any] = {"properties": properties}

    resp = requests.post(url, headers=headers(), json=payload)
    if resp.status_code != 201:
        return f"Error: {resp.status_code}"

    return format_company(resp.json())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("name")
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
        create_company(
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
