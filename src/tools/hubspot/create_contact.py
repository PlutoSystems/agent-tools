import sys
import requests
from typing import Any
from tools.hubspot import HUBSPOT_TOKEN, BASE_URL, headers, format_contact


def create_contact(
    email: str,
    firstname: str | None = None,
    lastname: str | None = None,
    phone: str | None = None,
    jobtitle: str | None = None,
    company_id: str | None = None,
) -> str:
    """Create a HubSpot contact, optionally linked to a company."""
    if not HUBSPOT_TOKEN:
        return "Error: HUBSPOT_ACCESS_TOKEN not set"

    url = f"{BASE_URL}/crm/v3/objects/contacts"

    properties: dict[str, str] = {"email": email}
    if firstname:
        properties["firstname"] = firstname
    if lastname:
        properties["lastname"] = lastname
    if phone:
        properties["phone"] = phone
    if jobtitle:
        properties["jobtitle"] = jobtitle

    payload: dict[str, Any] = {"properties": properties}

    if company_id:
        payload["associations"] = [
            {
                "to": {"id": company_id},
                "types": [
                    {"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 279}
                ],
            }
        ]

    resp = requests.post(url, headers=headers(), json=payload)
    if resp.status_code == 409:
        return "Error: Contact already exists"
    if resp.status_code != 201:
        return f"Error: {resp.status_code}"

    return format_contact(resp.json())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("email")
    parser.add_argument("--firstname", "-f")
    parser.add_argument("--lastname", "-l")
    parser.add_argument("--phone", "-p")
    parser.add_argument("--jobtitle", "-j")
    parser.add_argument("--company", "-c", dest="company_id")
    args = parser.parse_args()

    print(
        create_contact(
            args.email,
            args.firstname,
            args.lastname,
            args.phone,
            args.jobtitle,
            args.company_id,
        )
    )
