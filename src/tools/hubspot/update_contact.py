import sys
import requests
from typing import Any
from tools.hubspot import (
    HUBSPOT_TOKEN,
    BASE_URL,
    CONTACT_PROPERTIES,
    headers,
    format_contact,
)


def update_contact(
    contact_id: str,
    email: str | None = None,
    firstname: str | None = None,
    lastname: str | None = None,
    phone: str | None = None,
    jobtitle: str | None = None,
) -> str:
    """
    Update an existing HubSpot contact. Only provided fields will be updated.

    Args:
        contact_id: HubSpot contact ID (required)
        email: Contact email address
        firstname: First name
        lastname: Last name
        phone: Phone number
        jobtitle: Job title
    """
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    properties: dict[str, str] = {}
    if email:
        properties["email"] = email
    if firstname:
        properties["firstname"] = firstname
    if lastname:
        properties["lastname"] = lastname
    if phone:
        properties["phone"] = phone
    if jobtitle:
        properties["jobtitle"] = jobtitle

    if not properties:
        return "Error: No properties to update"

    url = f"{BASE_URL}/crm/v3/objects/contacts/{contact_id}"
    payload: dict[str, Any] = {"properties": properties}

    resp = requests.patch(url, headers=headers(), json=payload)
    if resp.status_code == 404:
        return "Error: Contact not found"
    if resp.status_code != 200:
        return f"Error: {resp.status_code}"

    # Fetch full contact to get all properties (PATCH only returns updated ones)
    get_resp = requests.get(
        url, headers=headers(), params={"properties": ",".join(CONTACT_PROPERTIES)}
    )
    if get_resp.status_code == 200:
        return format_contact(get_resp.json())
    return format_contact(resp.json())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("contact_id")
    parser.add_argument("--email", "-e")
    parser.add_argument("--firstname", "-f")
    parser.add_argument("--lastname", "-l")
    parser.add_argument("--phone", "-p")
    parser.add_argument("--jobtitle", "-j")
    args = parser.parse_args()

    print(
        update_contact(
            args.contact_id,
            args.email,
            args.firstname,
            args.lastname,
            args.phone,
            args.jobtitle,
        )
    )
