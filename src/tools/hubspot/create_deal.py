import sys
import requests
from typing import Any
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    headers,
    format_project,
    validate_deal_stage,
    validate_product_type,
)


def create_project(
    name: str,
    company_id: str,
    stage: str | None = None,
    city: str | None = None,
    number_of_units: int | None = None,
    product_type: str | None = None,
    launch_date: str | None = None,
    google_maps_link: str | None = None,
) -> str:
    """
    Create a new real estate project. Must be linked to a company.

    Args:
        name: Project name (required)
        company_id: HubSpot company ID to associate with (required)
        stage: Project stage - must be one of: Rumored, Confirmed, Pursuing,
               Quoted, Active on Pluto, Closed Lost, Cancelled
               (Default for existing customers is "Pursuing")
        city: City where project is located
        number_of_units: Total units in the project
        product_type: Must be one of: Single Family, Multi-Family,
                      Condo (low-rise), Condo (high-rise)
        launch_date: Expected public sales launch date (YYYY-MM-DD format,
                     NOT the construction start date)
        google_maps_link: Google Maps URL to project location
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    internal_stage = None
    if stage:
        internal_stage, err = validate_deal_stage(stage)
        if err:
            return f"Error: {err}"

    if product_type:
        err = validate_product_type(product_type)
        if err:
            return f"Error: {err}"

    url = f"{BASE_URL}/crm/v3/objects/deals"

    properties: dict[str, Any] = {"dealname": name}
    if internal_stage:
        properties["dealstage"] = internal_stage
    if city:
        properties["city"] = city
    if number_of_units is not None:
        properties["number_of_units"] = str(number_of_units)
    if product_type:
        properties["product_type"] = product_type
    if launch_date:
        properties["launch_date"] = launch_date
    if google_maps_link:
        properties["google_maps_link"] = google_maps_link

    payload: dict[str, Any] = {
        "properties": properties,
        "associations": [
            {
                "to": {"id": company_id},
                "types": [
                    {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 341}
                ],
            }
        ],
    }

    resp = requests.post(url, headers=headers(), json=payload)
    if resp.status_code != 201:
        return f"Error: {resp.status_code}"

    return format_project(resp.json())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    parser.add_argument("company_id")
    parser.add_argument("--stage", "-s")
    parser.add_argument("--city")
    parser.add_argument("--units", type=int, dest="number_of_units")
    parser.add_argument("--product-type", "-p")
    parser.add_argument("--launch-date")
    parser.add_argument("--map-link")
    args = parser.parse_args()

    print(
        create_project(
            args.name,
            args.company_id,
            args.stage,
            args.city,
            args.number_of_units,
            args.product_type,
            args.launch_date,
            args.map_link,
        )
    )
