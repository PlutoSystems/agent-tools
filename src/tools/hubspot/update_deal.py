import sys
import requests
from typing import Any
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    DEAL_PROPERTIES,
    headers,
    format_project,
    validate_deal_stage,
    validate_product_type,
)


def update_project(
    deal_id: str,
    name: str | None = None,
    stage: str | None = None,
    city: str | None = None,
    number_of_units: int | None = None,
    product_type: str | None = None,
    launch_date: str | None = None,
    google_maps_link: str | None = None,
) -> str:
    """
    Update an existing real estate project. Only provided fields are updated.

    Args:
        deal_id: HubSpot deal/project ID (required)
        name: Project name
        stage: Must be one of: Rumored, Confirmed, Pursuing, Quoted,
               Active on Pluto, Closed Lost, Cancelled
        city: City location
        number_of_units: Total units in the project
        product_type: Must be one of: Single Family, Multi-Family,
                      Condo (low-rise), Condo (high-rise)
        launch_date: Expected public sales launch date (YYYY-MM-DD format)
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

    properties: dict[str, Any] = {}
    if name:
        properties["dealname"] = name
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

    if not properties:
        return "Error: No properties to update"

    url = f"{BASE_URL}/crm/v3/objects/deals/{deal_id}"
    payload: dict[str, Any] = {"properties": properties}

    resp = requests.patch(url, headers=headers(), json=payload)
    if resp.status_code == 404:
        return "Error: Project not found"
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    # Fetch full deal to get all properties (PATCH only returns updated ones)
    get_resp = requests.get(
        url, headers=headers(), params={"properties": ",".join(DEAL_PROPERTIES)}
    )
    if get_resp.status_code == 200:
        return format_project(get_resp.json())
    return format_project(resp.json())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("deal_id")
    parser.add_argument("--name", "-n")
    parser.add_argument("--stage", "-s")
    parser.add_argument("--city")
    parser.add_argument("--units", type=int, dest="number_of_units")
    parser.add_argument("--product-type", "-p")
    parser.add_argument("--launch-date")
    parser.add_argument("--map-link")
    args = parser.parse_args()

    print(
        update_project(
            args.deal_id,
            args.name,
            args.stage,
            args.city,
            args.number_of_units,
            args.product_type,
            args.launch_date,
            args.map_link,
        )
    )
