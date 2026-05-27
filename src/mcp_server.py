import sys
import json
from typing import Literal
from mcp.server.fastmcp import FastMCP
from tools.parse_email_tool import parse_email
from tools.download_transcript_tool import fetch_transcript
from tools.download_recording_tool import download_recording as _download_recording
from tools.analyze_qa_recording_tool import (
    analyze_qa_recording as _analyze_qa_recording,
)
from tools.analyze_content_recording_tool import (
    analyze_content_recording as _analyze_content_recording,
)

EXCLUDED = set()
i = 1
while i < len(sys.argv):
    if sys.argv[i] == "--exclude" and i + 1 < len(sys.argv):
        EXCLUDED.add(sys.argv[i + 1].lower())
        i += 2
    else:
        i += 1

mcp = FastMCP("Pluto Shared MCP Tools")


@mcp.tool()
def download_transcript(join_url: str, output_path: str = "") -> str:
    """
    Downloads and saves a Microsoft Teams meeting transcript.

    This tool authenticates with Microsoft Graph API (requires interactive browser
    authentication on first use), retrieves the meeting transcript, cleans the VTT
    format to plain text with speaker names, and saves it to .local/transcripts/.
    Optionally also saves to output_path if provided.

    Args:
        join_url: The Teams meeting Join Web URL (e.g., from meeting invite or calendar)
        output_path: Optional file path to also save the transcript to.

    Returns:
        Success message with the saved file path, or error message if the operation fails.

    Notes:
        - Requires MS_CLIENT_ID in .env file
        - Auth credentials are cached in .local/auth_record.json for subsequent runs
    """
    try:
        content = fetch_transcript(join_url, output_path or None)
        return content
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def download_recording(join_url: str) -> str:
    """
    Downloads a Microsoft Teams meeting recording as an MP4 file.

    Authenticates with Microsoft Graph API, retrieves the meeting recording,
    and saves it to the .local/ directory. Returns metadata including file name,
    size, and meeting details.

    Args:
        join_url: The Teams meeting Join Web URL (e.g., from meeting invite or calendar).

    Returns:
        Success message with file path and metadata, or error message if the operation fails.
    """
    try:
        return _download_recording(join_url)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def analyze_qa_recording(
    video_path: str, transcript_path: str, meeting_name: str = ""
) -> str:
    """
    Analyze a Teams meeting recording for UX issues, bugs, and feature requests.

    Uses Gemini Flash to watch the video and identify every mentioned issue. For each
    issue found, extracts video clips and screenshots at the relevant timestamps.

    Args:
        video_path: Path to the MP4 recording file (e.g., from download_recording).
        transcript_path: Path to the transcript text file for supporting evidence.
        meeting_name: Optional name for the meeting, used to organize output folders.
                      Defaults to the video filename if not provided.

    Returns:
        JSON with meeting_name, total_issues, token usage, and an issues array.
        Each issue contains: category, quote, explanation, start_time, end_time,
        evidence_source,
        clip (file path to video clip), and screenshots (list of image file paths).
    """
    try:
        return _analyze_qa_recording(video_path, transcript_path, meeting_name or None)
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def analyze_content_recording(
    video_path: str, transcript_path: str, meeting_name: str = ""
) -> str:
    """
    Analyze a recording for marketing and sales content feedback.

    Uses Gemini Flash to organize non-technical content ideas into a simple list and
    extracts supporting clips/screenshots for each idea.

    Args:
        video_path: Path to the MP4 recording file.
        transcript_path: Path to the transcript text file for supporting evidence.
        meeting_name: Optional name for organizing output folders.

    Returns:
        JSON with meeting_name, total_ideas, token usage, and ideas array.
        Each idea contains: category, title, summary, quote, start_time, end_time,
        evidence_source,
        clip (file path), and screenshots (list of file paths).
    """
    try:
        return _analyze_content_recording(
            video_path, transcript_path, meeting_name or None
        )
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def parse_email_file(file_path: str) -> str:
    """
    Parse a .msg email file and extract its contents.

    Extracts sender, recipients (to/cc/bcc), subject, body, and attachments
    from a Microsoft Outlook .msg file. Long URLs in the body are replaced
    with [LINK]. Attachment content is returned as base64.

    Args:
        file_path: Absolute path to the .msg file to parse.

    Returns:
        JSON string with keys: sentOn (epoch ms), from, to, cc, bcc, subject, body, attachments.
    """
    try:
        result = parse_email(file_path)
        return json.dumps(result, default=str)
    except Exception as e:
        return f"Error: {str(e)}"


# --- HubSpot tools (excludable with --exclude hubspot) ---

if "hubspot" not in EXCLUDED:
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
    from tools.hubspot.search_meetings import search_meetings
    from tools.hubspot.search_calls import search_calls
    from tools.hubspot.search_notes import search_notes
    from tools.hubspot.search_emails import search_emails

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

    @mcp.tool()
    def hubspot_search_meetings(
        contact_id: str | None = None,
        company_id: str | None = None,
        deal_id: str | None = None,
        outcome: str | None = None,
        after_date: str | None = None,
        before_date: str | None = None,
        limit: int = 10,
    ) -> str:
        """
        Search HubSpot meetings by association or filters.

        Args:
            contact_id: Find meetings associated with this contact
            company_id: Find meetings associated with this company
            deal_id: Find meetings associated with this project
            outcome: Filter by outcome (SCHEDULED, COMPLETED, RESCHEDULED, NO_SHOW, CANCELLED)
            after_date: Only meetings after this date (YYYY-MM-DD)
            before_date: Only meetings before this date (YYYY-MM-DD)
            limit: Max results (default 10)

        At least one filter must be provided.
        """
        return search_meetings(
            contact_id, company_id, deal_id, outcome, after_date, before_date, limit
        )

    @mcp.tool()
    def hubspot_search_calls(
        contact_id: str | None = None,
        company_id: str | None = None,
        deal_id: str | None = None,
        after_date: str | None = None,
        before_date: str | None = None,
        limit: int = 10,
    ) -> str:
        """
        Search HubSpot calls by association or date range.

        Args:
            contact_id: Find calls associated with this contact
            company_id: Find calls associated with this company
            deal_id: Find calls associated with this project
            after_date: Only calls after this date (YYYY-MM-DD)
            before_date: Only calls before this date (YYYY-MM-DD)
            limit: Max results (default 10)

        At least one filter must be provided.
        """
        return search_calls(
            contact_id, company_id, deal_id, after_date, before_date, limit
        )

    @mcp.tool()
    def hubspot_search_notes(
        contact_id: str | None = None,
        company_id: str | None = None,
        deal_id: str | None = None,
        after_date: str | None = None,
        before_date: str | None = None,
        limit: int = 10,
    ) -> str:
        """
        Search HubSpot notes by association or date range.

        Args:
            contact_id: Find notes associated with this contact
            company_id: Find notes associated with this company
            deal_id: Find notes associated with this project
            after_date: Only notes after this date (YYYY-MM-DD)
            before_date: Only notes before this date (YYYY-MM-DD)
            limit: Max results (default 10)

        At least one filter must be provided.
        """
        return search_notes(
            contact_id, company_id, deal_id, after_date, before_date, limit
        )

    @mcp.tool()
    def hubspot_search_emails(
        contact_id: str | None = None,
        company_id: str | None = None,
        subject: str | None = None,
        after_date: str | None = None,
        before_date: str | None = None,
        limit: int = 10,
    ) -> str:
        """
        Search HubSpot emails by association, subject, or date range.

        Args:
            contact_id: Find emails associated with this contact
            company_id: Find emails associated with this company
            subject: Search by email subject (partial match)
            after_date: Only emails after this date (YYYY-MM-DD)
            before_date: Only emails before this date (YYYY-MM-DD)
            limit: Max results (default 10)

        At least one filter must be provided.
        """
        return search_emails(
            contact_id, company_id, subject, after_date, before_date, limit
        )


# --- Conversion tools (excludable with --exclude conversions) ---

if "conversions" not in EXCLUDED:
    from tools.conversions.pdf_to_markdown import pdf_to_markdown
    from tools.conversions.docx_to_markdown import docx_to_markdown

    @mcp.tool()
    def convert_pdf_to_markdown(file_path: str, output_path: str | None = None) -> str:
        """
        Convert a PDF file to Markdown text using markitdown.

        Args:
            file_path: Absolute path to the .pdf file to convert.
            output_path: Optional path to save the markdown output. If omitted, returns the markdown directly.

        Returns:
            The converted markdown text, or a confirmation message if output_path was provided.
        """
        return pdf_to_markdown(file_path, output_path)

    @mcp.tool()
    def convert_docx_to_markdown(file_path: str, output_path: str | None = None) -> str:
        """
        Convert a Word document (.doc/.docx) to Markdown text using markitdown.

        Args:
            file_path: Absolute path to the .doc or .docx file to convert.
            output_path: Optional path to save the markdown output. If omitted, returns the markdown directly.

        Returns:
            The converted markdown text, or a confirmation message if output_path was provided.
        """
        return docx_to_markdown(file_path, output_path)


# --- ClickUp tools (excludable with --exclude clickup) ---

if "clickup" not in EXCLUDED:
    from tools.clickup.search_structure import search_structure as _search_structure
    from tools.clickup.resolve_url import resolve_clickup_url as _resolve_clickup_url
    from tools.clickup.task_create import create_task
    from tools.clickup.task_add_attachment import add_attachment

    @mcp.tool()
    def clickup_search_structure(
        entity_type: Literal["Space", "Folder", "List", "Document"] | None = None,
        id: str | None = None,
        name: str | None = None,
        query: str | None = None,
        force_refresh: bool = False,
    ) -> str:
        """
        Search the ClickUp workspace hierarchy to find a space, folder, list, or doc.

        Use this FIRST before any other ClickUp operation when you need a list_id, folder_id,
        or space_id. The hierarchy is cached locally so this is fast — call with
        force_refresh=True only if you think the workspace structure has changed.

        Resolution order (stops at first success):
        1. Exact ID match — use when you already have an ID from a URL or prior result
        2. Exact name match (case-insensitive) — use when you know the precise name
        3. Fuzzy match on `query` — returns ranked candidates when name is uncertain

        Args:
            entity_type: Optional filter — "Space", "Folder", "List", or "Document"
            id:          Find by exact ClickUp ID (numeric string)
            name:        Find by exact name (case-insensitive)
            query:       Natural-language description for fuzzy matching when name is unknown
            force_refresh: Re-fetch hierarchy from ClickUp API (bypasses cache)

        Returns:
            JSON with matched entity: { type, id, name, path } — path shows breadcrumb
            e.g. "Engineering > Sprint > Backlog". Returns array if multiple matches found.
        """
        return _search_structure(entity_type, id, name, query, force_refresh)

    @mcp.tool()
    def clickup_resolve_url(url: str) -> str:
        """
        Resolve a ClickUp app URL to its parent hierarchy (list of IDs).

        Parses the URL to extract entity IDs, calls the ClickUp View API when
        needed to dereference view IDs, then looks up each ID in the local
        hierarchy cache to return the full ancestor chain.

        Supports all common ClickUp URL types:
        - Folder overview (/v/o/f/{folder_id})
        - Doc/page (/v/dc/{doc_id}/...)
        - List views (/v/l/{view_id} or /v/l/{type}-{list_id}-{n})
        - Board views (/v/b/{view_id} or /v/b/li/{list_id})

        Args:
            url: A ClickUp app URL (e.g. https://app.clickup.com/14254316/v/l/dk07c-60177)

        Returns:
            JSON with a "hierarchy" array of { type, id, name } objects from
            outermost (space) to innermost (list/folder/doc).
        """
        return _resolve_clickup_url(url)

    @mcp.tool()
    def clickup_create_task(
        list_id: str,
        name: str,
        markdown_content: str,
        task_type: str | None = None,
        parent: str | None = None,
    ) -> str:
        """
        Create a new task in a ClickUp list.

        Use clickup_search_structure to find the list_id before calling this.

        Args:
            list_id: ClickUp list ID to create the task in
            name: Task name/title
            markdown_content: Task description in markdown
            task_type: Optional custom task type name (e.g. "Bug", "Feature")
            parent: Optional parent task ID to nest this as a subtask
        """
        return create_task(list_id, name, markdown_content, task_type, parent)

    @mcp.tool()
    def clickup_add_attachment(task_id: str, file_path: str) -> str:
        """
        Upload a file as an attachment to a ClickUp task.

        Args:
            task_id: ClickUp task ID
            file_path: Absolute path to the file to attach
        """
        return add_attachment(task_id, file_path)


if __name__ == "__main__":
    mcp.run()
