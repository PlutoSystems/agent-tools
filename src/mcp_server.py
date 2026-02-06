from mcp.server.fastmcp import FastMCP
from tools.transcript_fetch import fetch_transcript
from tools.hubspot.search_contacts import search_contacts
from tools.hubspot.get_contact import get_contact
from tools.hubspot.create_contact import create_contact
from tools.hubspot.update_contact import update_contact
from tools.hubspot.search_companies import search_companies
from tools.hubspot.get_company import get_company
from tools.hubspot.create_company import create_company
from tools.hubspot.update_company import update_company
from tools.hubspot.get_company_projects import get_company_projects
from tools.hubspot.search_deals import search_projects
from tools.hubspot.get_deal import get_project
from tools.hubspot.create_deal import create_project
from tools.hubspot.update_deal import update_project
from tools.hubspot.add_note import add_note
from tools.hubspot.log_call import log_call
from tools.hubspot.log_meeting import log_meeting
from tools.hubspot.list_users import list_users

# Create the server
mcp = FastMCP("Pluto Shared MCP Tools")


@mcp.tool()
def fetch_transcript_tool(join_url: str, output_path: str) -> str:
    """
    Downloads and saves a Microsoft Teams meeting transcript.

    This tool authenticates with Microsoft Graph API (requires interactive browser
    authentication on first use), retrieves the meeting transcript, cleans the VTT
    format to plain text with speaker names, and saves it to the specified path.

    Args:
        join_url: The Teams meeting Join Web URL (e.g., from meeting invite or calendar)
        output_path: Absolute file path where the cleaned transcript should be saved (e.g.,
                    'C:/Users/user/Desktop/meeting.txt'). Parent directories will be created if needed.

    Returns:
        Success message with the saved file path, or error message if the operation fails.

    Notes:
        - Requires MS_CLIENT_ID in .env file
        - Auth credentials are cached in .local/auth_record.json for subsequent runs
    """
    try:
        content = fetch_transcript(join_url, output_path)
        return content
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def hubspot_search_contacts(query: str, limit: int = 10) -> str:
    """Search HubSpot contacts by name or email."""
    return search_contacts(query, limit)


@mcp.tool()
def hubspot_get_contact(contact_id: str) -> str:
    """Get a HubSpot contact by ID."""
    return get_contact(contact_id)


@mcp.tool()
def hubspot_create_contact(
    email: str,
    firstname: str | None = None,
    lastname: str | None = None,
    phone: str | None = None,
    jobtitle: str | None = None,
    company_id: str | None = None,
) -> str:
    """Create a HubSpot contact, optionally linked to a company."""
    return create_contact(email, firstname, lastname, phone, jobtitle, company_id)


@mcp.tool()
def hubspot_update_contact(
    contact_id: str,
    email: str | None = None,
    firstname: str | None = None,
    lastname: str | None = None,
    phone: str | None = None,
    jobtitle: str | None = None,
) -> str:
    """
    Update a HubSpot contact. Only provided fields are updated.

    Args:
        contact_id: HubSpot contact ID (required)
        email: Contact email address
        firstname: First name
        lastname: Last name
        phone: Phone number
        jobtitle: Job title
    """
    return update_contact(contact_id, email, firstname, lastname, phone, jobtitle)


@mcp.tool()
def hubspot_search_companies(
    query: str | None = None, lead_status: str | None = None, limit: int = 10
) -> str:
    """
    Search HubSpot companies by name/domain or filter by lead status.

    Args:
        query: Search term to match against company name or domain
        lead_status: Filter by lead status (Prospect, In Discovery, In Proposal,
                     Contract Sent, Active Customer, Revisit, Uninterested)
        limit: Max results (default 10)
    """
    return search_companies(query, lead_status, limit)


@mcp.tool()
def hubspot_get_company(company_id: str) -> str:
    """
    Get a HubSpot company by ID.

    Returns: Name, website, location, lead status, annual unit volume, product types.
    """
    return get_company(company_id)


@mcp.tool()
def hubspot_create_company(
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
        phone: Phone number
        city: City location
        state: State/region
        annual_unit_volume: Units this developer builds per year
        lead_status: Must be: Prospect, In Discovery, In Proposal, Contract Sent,
                     Active Customer, Revisit, or Uninterested
        product_types: List from: Single Family, Multi-Family, Condo (low-rise), Condo (high-rise)
        icp_tier: Ideal Customer Profile tier - must be: Tier 1, Tier 2, or Tier 3
    """
    return create_company(
        name,
        domain,
        phone,
        city,
        state,
        annual_unit_volume,
        lead_status,
        product_types,
        icp_tier,
    )


@mcp.tool()
def hubspot_update_company(
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
    Update a HubSpot company. Only provided fields are updated.

    IMPORTANT: Lead Status is critical for sales tracking - verify current status first.

    Args:
        company_id: HubSpot company ID (required)
        name: Company name
        domain: Website domain
        phone: Phone number
        city: City location
        state: State/region
        annual_unit_volume: Units this developer builds per year
        lead_status: Must be: Prospect, In Discovery, In Proposal, Contract Sent,
                     Active Customer, Revisit, or Uninterested
        product_types: List from: Single Family, Multi-Family, Condo (low-rise), Condo (high-rise)
        icp_tier: Ideal Customer Profile tier - must be: Tier 1, Tier 2, or Tier 3
    """
    return update_company(
        company_id,
        name,
        domain,
        phone,
        city,
        state,
        annual_unit_volume,
        lead_status,
        product_types,
        icp_tier,
    )


@mcp.tool()
def hubspot_get_company_projects(company_id: str) -> str:
    """
    Get all projects (deals) associated with a company.

    Args:
        company_id: HubSpot company ID

    Returns:
        Formatted list of all projects linked to this company with details:
        name, stage, city, units, product type, launch date, map link.
    """
    return get_company_projects(company_id)


@mcp.tool()
def hubspot_search_projects(
    query: str | None = None,
    stage: str | None = None,
    limit: int = 10,
) -> str:
    """
    Search real estate projects by name or filter by stage.

    Args:
        query: Search term to match against project name
        stage: Filter by stage - must be one of: Rumored, Confirmed, Pursuing,
               Quoted, Active on Pluto, Closed Lost, Cancelled
        limit: Max results (default 10)
    """
    return search_projects(query, stage, limit)


@mcp.tool()
def hubspot_get_project(project_id: str) -> str:
    """
    Get a real estate project by ID.

    Returns: Project name, stage, city, units, product type, launch date, map link, company.
    """
    return get_project(project_id)


@mcp.tool()
def hubspot_create_project(
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
        company_id: HubSpot company ID to associate (required)
        stage: Must be one of: Rumored, Confirmed, Pursuing, Quoted,
               Active on Pluto, Closed Lost, Cancelled
        city: City location
        number_of_units: Total units in project
        product_type: Must be one of: Single Family, Multi-Family,
                      Condo (low-rise), Condo (high-rise)
        launch_date: Expected public sales date (YYYY-MM-DD, NOT construction start)
        google_maps_link: Google Maps URL to location
    """
    return create_project(
        name,
        company_id,
        stage,
        city,
        number_of_units,
        product_type,
        launch_date,
        google_maps_link,
    )


@mcp.tool()
def hubspot_update_project(
    project_id: str,
    name: str | None = None,
    stage: str | None = None,
    city: str | None = None,
    number_of_units: int | None = None,
    product_type: str | None = None,
    launch_date: str | None = None,
    google_maps_link: str | None = None,
) -> str:
    """
    Update a real estate project. Only provided fields are updated.

    Args:
        project_id: HubSpot project ID (required)
        name: Project name
        stage: Must be one of: Rumored, Confirmed, Pursuing, Quoted,
               Active on Pluto, Closed Lost, Cancelled
        city: City location
        number_of_units: Total units in project
        product_type: Must be one of: Single Family, Multi-Family,
                      Condo (low-rise), Condo (high-rise)
        launch_date: Expected public sales date (YYYY-MM-DD)
        google_maps_link: Google Maps URL to location
    """
    return update_project(
        project_id,
        name,
        stage,
        city,
        number_of_units,
        product_type,
        launch_date,
        google_maps_link,
    )


@mcp.tool()
def hubspot_add_note(
    body: str,
    contact_id: str | None = None,
    company_id: str | None = None,
    deal_id: str | None = None,
) -> str:
    """
    Add a note to a HubSpot contact, company, or project.

    Args:
        body: Note text content - PLAIN TEXT ONLY, no markdown (required)
        contact_id: Associate with this contact
        company_id: Associate with this company
        deal_id: Associate with this project

    At least one of contact_id, company_id, or deal_id must be provided.
    """
    return add_note(body, contact_id, company_id, deal_id)


@mcp.tool()
def hubspot_log_call(
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
        body: Call notes - PLAIN TEXT ONLY, no markdown
        duration_minutes: Length of call in minutes
        outcome: Must be one of: Connected, Busy, No answer, Left voicemail,
                 Left live message, Wrong number
        direction: INBOUND or OUTBOUND
        contact_id: Associate with this contact
        company_id: Associate with this company
        deal_id: Associate with this project
        call_time: When the call happened in LOCAL time (format: YYYY-MM-DDTHH:MM:SS)
        tz: IANA timezone for call_time (default: America/Edmonton for Calgary MST/MDT)

    At least one of contact_id, company_id, or deal_id must be provided.
    """
    return log_call(
        title,
        body,
        duration_minutes,
        outcome,
        direction,
        contact_id,
        company_id,
        deal_id,
        call_time,
        tz,
    )


@mcp.tool()
def hubspot_log_meeting(
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
        body: Meeting notes - PLAIN TEXT ONLY, no markdown
        start_time: Meeting start in LOCAL time (format: YYYY-MM-DDTHH:MM:SS, e.g. 2026-02-03T15:00:00)
        end_time: Meeting end in LOCAL time (format: YYYY-MM-DDTHH:MM:SS)
        location: Meeting location (room, Zoom link, address, etc.)
        outcome: Must be one of: SCHEDULED, COMPLETED, RESCHEDULED, NO_SHOW, CANCELLED
        contact_id: Associate with this contact
        company_id: Associate with this company
        deal_id: Associate with this project
        tz: IANA timezone for the times (default: America/Edmonton for Calgary MST/MDT)
        owner_id: HubSpot user ID for meeting organizer (use hubspot_list_users to find IDs)
        attendee_ids: List of HubSpot user IDs for internal staff attendees

    At least one of contact_id, company_id, or deal_id must be provided.
    """
    return log_meeting(
        title,
        body,
        start_time,
        end_time,
        location,
        outcome,
        contact_id,
        company_id,
        deal_id,
        tz,
        owner_id,
        attendee_ids,
    )


@mcp.tool()
def hubspot_list_users() -> str:
    """
    List all HubSpot users (owners) with their IDs.

    Returns a list of users with ID, name, and email.
    Use these IDs for owner_id and attendee_ids in hubspot_log_meeting.
    """
    return list_users()


if __name__ == "__main__":
    mcp.run()
