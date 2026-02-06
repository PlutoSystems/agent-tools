# HubSpot MCP Server Build Guide

## Overview

Build a custom HubSpot MCP server with update capabilities to integrate into your existing `agent-tools` infrastructure.

---

## Tool Definitions

```python
tools = [
    "hubspot_search_companies",   # Search by name, domain, lead status, etc.
    "hubspot_create_company",
    "hubspot_get_company",        # Get by ID to verify before update
    "hubspot_update_company",

    "hubspot_search_contacts",    # Search by email, name, company
    "hubspot_create_contact",
    "hubspot_get_contact",        # Get by ID to verify before update
    "hubspot_update_contact",

    "hubspot_search_deals",       # Search by name, stage, associated company
    "hubspot_create_deal",
    "hubspot_get_deal",
    "hubspot_update_deal",

    "hubspot_log_activity",
    "hubspot_add_note"
]
```

## Company Properties & Guidelines

- company is the primary contact we use to track our sales performance
- the most important value is the company 'Lead Status', take care when updating this
- only attempt to create, read, or update the properties listed below. Ignore all other properties

* Company Name - [Builtin]
* Website URL - [Builtin]
* Phone (phone) - [Builtin]
* City (city) - [Builtin]
* State/Region (state) - [Builtin]
* Annual Unit Volume (annual_unit_volume) - [CUSTOM] Number of units per year this developer company builds
* Lead Status (hs_lead_status) - [Builtin] I customized the allowed values here:
  Prospect → Future account to target, no formal communication yet
  In Discovery → Booked first meeting, learning about them, demo 1 or 2
  In Proposal → At least one demo and expressed interest, sending quotes / proposals
  Contract Sent → Sent formal contract for real project
  Active Customer → Contract has been signed for at least one project, and therefore are active Pluto customers
  Revisit → Expressed interest but not right now, open to future opportunities
  Uninterested → Expressed no interest, leave alone
* Ideal Customer Profile Tier (hs_ideal_customer_profile) - [Builtin] how closely they match our ICP, which should also be available to the agent
* Product Types (product_types) - [CUSTOM] Multi-select types of products this developer is known to build or is planning to build. Must be from list of allowed values: Single Family, Multi-Family, Condo (low-rise), Condo (high-rise)
* Company Owner (hubspot_owner_id) - [Builtin] Important for commission calculations, whoever is the sales 'lead' on the company

## Contact Properties & Guidelines

- contact's usually only exist when connected to a company, always try to find the associated company for a new contact before adding, and if it's missing ask the user if they want to create a company before creating the contact
- only attempt to connect contacts to companies, not to deals or other objects
- only attempt to create, read, or update the properties listed below. Ignore all other properties

* Name
* Email
* Phone
* Job Title

## Deal Properties & Guidelines

- we are using hubspot's "deal" system to represent real estate projects of our customer companies. Each deal corresponds to a single real estate project, and must be connected to at least one company. If the company for a deal is not found, ask the user to create the company first before continuing
- this 'deal' is the term used by hubspot, not by Pluto. Pluto will refer to these as 'projects' in the context of real estate companies, so use the term 'project' when communicating with the user, and only use the 'deal' object to create the API requests to hubspot and to understand the Hubspot API documentation
- only associate deals with companies, not contacts or other objects
- only attempt to create, read, or update the properties listed below. Ignore all other properties

* Deal Name (dealname) - [BUILTIN]
* Deal Stage - (dealstage) - [BUILTIN] I customized these values:
  Rumored → We have heard about the project but not personally verified the details
  Confirmed → Personally verified the deal is going to happen
  Pursuing → Actively in communication with builder about the project. This is the default for project's being built by existing Pluto customers
  Quoted → Quote or proposal has been sent
  Active on Pluto → Contract is signed for this project, or has already been onboarded
  Closed Lost → Project went on without Pluto
  Cancelled → Project was cancelled by the developer
* Launch Date (launch_date) - [CUSTOM] Date we expect the project to be launched for public sales (NOT THE CONSTRUCTION START DATE!)
* Number of Units (number_of_units) - [CUSTOM]
* Product Type (product_type) - [CUSTOM] Must be selected from list of available values: Single Family, Multi-Family, Condo (low-rise), Condo (high-rise)
* City (city) [CUSTOM]
* Google Maps Link - [CUSTOM] Google maps public link to the development or best guess location

---

## Error Handling Considerations

1. **Rate Limits**: HubSpot allows 100 requests per 10 seconds for private apps
2. **Invalid Properties**: Validate property names before sending
3. **Not Found**: Handle 404s gracefully when company/contact doesn't exist
4. **Authentication**: Handle 401 for expired/invalid tokens

## Resources

- [HubSpot CRM API Reference](https://developers.hubspot.com/docs/api/crm/companies)
- [HubSpot Properties API](https://developers.hubspot.com/docs/api/crm/properties)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
