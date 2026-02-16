"""Salesforce tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for Salesforce operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "query_contacts",
                "description": "Query contacts from Salesforce with optional filters. Uses SOQL under the hood.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_term": {
                            "type": "string",
                            "description": "Search term to match against contact name, email, or phone.",
                        },
                        "account_name": {
                            "type": "string",
                            "description": "Filter contacts by their associated account/company name.",
                        },
                        "owner_id": {
                            "type": "string",
                            "description": "Filter contacts by Salesforce owner user ID.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of contacts to return (default 10, max 200).",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_opportunities",
                "description": "Query opportunities from Salesforce pipeline with optional filters for stage, amount, and close date.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "stage": {
                            "type": "string",
                            "description": "Filter by opportunity stage (e.g., 'Prospecting', 'Qualification', 'Proposal', 'Closed Won', 'Closed Lost').",
                        },
                        "account_name": {
                            "type": "string",
                            "description": "Filter by associated account name.",
                        },
                        "min_amount": {
                            "type": "number",
                            "description": "Minimum opportunity amount to filter by.",
                        },
                        "max_amount": {
                            "type": "number",
                            "description": "Maximum opportunity amount to filter by.",
                        },
                        "close_date_from": {
                            "type": "string",
                            "description": "Filter opportunities closing on or after this date (YYYY-MM-DD format).",
                        },
                        "close_date_to": {
                            "type": "string",
                            "description": "Filter opportunities closing on or before this date (YYYY-MM-DD format).",
                        },
                        "owner_id": {
                            "type": "string",
                            "description": "Filter by opportunity owner user ID.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default 10, max 200).",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_case",
                "description": "Create a new support case in Salesforce for tracking customer issues, inquiries, or service requests.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "Brief subject line for the case.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the issue or request.",
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "Salesforce Contact ID to associate with the case.",
                        },
                        "account_id": {
                            "type": "string",
                            "description": "Salesforce Account ID to associate with the case.",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["High", "Medium", "Low"],
                            "description": "Case priority level.",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["Question", "Problem", "Feature Request"],
                            "description": "Type of case.",
                        },
                        "origin": {
                            "type": "string",
                            "enum": ["Phone", "Email", "Web", "Chat"],
                            "description": "Channel through which the case originated.",
                        },
                    },
                    "required": ["subject"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_record",
                "description": "Update any Salesforce record by specifying the object type, record ID, and fields to update.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "object_type": {
                            "type": "string",
                            "description": "Salesforce object type (e.g., 'Contact', 'Account', 'Opportunity', 'Case').",
                        },
                        "record_id": {
                            "type": "string",
                            "description": "The 18-character Salesforce record ID.",
                        },
                        "fields": {
                            "type": "object",
                            "description": "Key-value pairs of field API names and their new values to update.",
                        },
                    },
                    "required": ["object_type", "record_id", "fields"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a Salesforce tool function."""
    handlers = {
        "query_contacts": _query_contacts,
        "query_opportunities": _query_opportunities,
        "create_case": _create_case,
        "update_record": _update_record,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _query_contacts(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Query contacts from Salesforce."""
    # TODO: Implement with Salesforce REST API (GET /services/data/vXX.0/query/?q=SOQL)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "contacts": [],
        "total": 0,
    }


async def _query_opportunities(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Query opportunities from Salesforce."""
    # TODO: Implement with Salesforce REST API (GET /services/data/vXX.0/query/?q=SOQL)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "opportunities": [],
        "total": 0,
    }


async def _create_case(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Create a new case in Salesforce."""
    # TODO: Implement with Salesforce REST API (POST /services/data/vXX.0/sobjects/Case)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "case_id": None,
        "case_number": None,
        "subject": args.get("subject"),
    }


async def _update_record(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Update a Salesforce record."""
    # TODO: Implement with Salesforce REST API (PATCH /services/data/vXX.0/sobjects/{ObjectType}/{RecordId})
    return {
        "status": "success",
        "message": "Not yet implemented",
        "object_type": args.get("object_type"),
        "record_id": args.get("record_id"),
    }
