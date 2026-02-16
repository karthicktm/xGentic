"""CRM tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for CRM operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "query_contacts",
                "description": "Query contacts from the CRM with optional filters such as status, company, or date range.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter_field": {
                            "type": "string",
                            "description": "Field to filter by (e.g., 'status', 'company', 'created_date').",
                        },
                        "filter_value": {
                            "type": "string",
                            "description": "Value to match for the filter field.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of contacts to return (default 10, max 100).",
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Number of records to skip for pagination (default 0).",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_contact",
                "description": "Create a new contact in the CRM. Requires at least a first name and either a phone number or email.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "first_name": {
                            "type": "string",
                            "description": "Contact's first name.",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Contact's last name.",
                        },
                        "email": {
                            "type": "string",
                            "description": "Contact's email address.",
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "Contact's phone number in E.164 format (e.g., +14155551234).",
                        },
                        "company": {
                            "type": "string",
                            "description": "Company or organization name.",
                        },
                        "title": {
                            "type": "string",
                            "description": "Contact's job title.",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Additional notes about the contact.",
                        },
                    },
                    "required": ["first_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_contact",
                "description": "Update an existing contact's information in the CRM.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "contact_id": {
                            "type": "string",
                            "description": "Unique identifier of the contact to update.",
                        },
                        "first_name": {
                            "type": "string",
                            "description": "Updated first name.",
                        },
                        "last_name": {
                            "type": "string",
                            "description": "Updated last name.",
                        },
                        "email": {
                            "type": "string",
                            "description": "Updated email address.",
                        },
                        "phone_number": {
                            "type": "string",
                            "description": "Updated phone number in E.164 format.",
                        },
                        "company": {
                            "type": "string",
                            "description": "Updated company name.",
                        },
                        "title": {
                            "type": "string",
                            "description": "Updated job title.",
                        },
                        "status": {
                            "type": "string",
                            "description": "Updated contact status (e.g., 'active', 'inactive', 'lead').",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Updated notes.",
                        },
                    },
                    "required": ["contact_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_contacts",
                "description": "Search contacts by keyword across name, email, phone, and company fields.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to match against contact fields (name, email, phone, company).",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default 10, max 50).",
                        },
                    },
                    "required": ["query"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a CRM tool function."""
    handlers = {
        "query_contacts": _query_contacts,
        "create_contact": _create_contact,
        "update_contact": _update_contact,
        "search_contacts": _search_contacts,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _query_contacts(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Query contacts with optional filters."""
    # TODO: Implement with actual CRM API or database calls
    return {
        "status": "success",
        "message": "Not yet implemented",
        "contacts": [],
        "total": 0,
        "filter_field": args.get("filter_field"),
        "filter_value": args.get("filter_value"),
        "limit": args.get("limit", 10),
        "offset": args.get("offset", 0),
    }


async def _create_contact(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Create a new contact."""
    # TODO: Implement with actual CRM API or database calls
    return {
        "status": "success",
        "message": "Not yet implemented",
        "contact_id": None,
        "first_name": args.get("first_name"),
        "last_name": args.get("last_name"),
    }


async def _update_contact(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Update an existing contact."""
    # TODO: Implement with actual CRM API or database calls
    return {
        "status": "success",
        "message": "Not yet implemented",
        "contact_id": args.get("contact_id"),
    }


async def _search_contacts(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Search contacts by keyword."""
    # TODO: Implement with actual CRM API or database calls
    return {
        "status": "success",
        "message": "Not yet implemented",
        "query": args.get("query"),
        "contacts": [],
        "total": 0,
    }
