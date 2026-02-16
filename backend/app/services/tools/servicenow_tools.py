"""ServiceNow tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for ServiceNow operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "create_incident",
                "description": "Create a new incident in ServiceNow for tracking IT issues, outages, or service disruptions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "short_description": {
                            "type": "string",
                            "description": "Brief summary of the incident (max 160 characters).",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the incident including symptoms, impact, and any troubleshooting already performed.",
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["1", "2", "3"],
                            "description": "Urgency level: 1 (High), 2 (Medium), 3 (Low).",
                        },
                        "impact": {
                            "type": "string",
                            "enum": ["1", "2", "3"],
                            "description": "Impact level: 1 (High - enterprise), 2 (Medium - department), 3 (Low - individual).",
                        },
                        "category": {
                            "type": "string",
                            "description": "Incident category (e.g., 'Network', 'Hardware', 'Software', 'Database').",
                        },
                        "subcategory": {
                            "type": "string",
                            "description": "Incident subcategory for more specific classification.",
                        },
                        "assignment_group": {
                            "type": "string",
                            "description": "Name of the group to assign the incident to (e.g., 'Service Desk', 'Network Operations').",
                        },
                        "caller_id": {
                            "type": "string",
                            "description": "The user ID or email of the person reporting the incident.",
                        },
                        "configuration_item": {
                            "type": "string",
                            "description": "The affected configuration item (CI) name or sys_id.",
                        },
                    },
                    "required": ["short_description"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_incidents",
                "description": "Query and search for existing incidents in ServiceNow with various filters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Free-text search query to match against incident descriptions and short descriptions.",
                        },
                        "state": {
                            "type": "string",
                            "enum": ["new", "in_progress", "on_hold", "resolved", "closed", "cancelled"],
                            "description": "Filter by incident state.",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["1", "2", "3", "4", "5"],
                            "description": "Filter by priority: 1 (Critical) to 5 (Planning).",
                        },
                        "assignment_group": {
                            "type": "string",
                            "description": "Filter by assigned group name.",
                        },
                        "caller_id": {
                            "type": "string",
                            "description": "Filter by the user who reported the incident.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default 10, max 100).",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_incident",
                "description": "Update an existing incident in ServiceNow, such as adding notes, changing state, or reassigning.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "incident_number": {
                            "type": "string",
                            "description": "The incident number (e.g., 'INC0012345') or sys_id.",
                        },
                        "state": {
                            "type": "string",
                            "enum": ["new", "in_progress", "on_hold", "resolved", "closed"],
                            "description": "Updated incident state.",
                        },
                        "work_notes": {
                            "type": "string",
                            "description": "Internal work notes to add to the incident (visible to IT staff only).",
                        },
                        "comments": {
                            "type": "string",
                            "description": "Customer-visible comments to add to the incident.",
                        },
                        "assignment_group": {
                            "type": "string",
                            "description": "Reassign to a different group.",
                        },
                        "assigned_to": {
                            "type": "string",
                            "description": "Assign to a specific individual (user ID or email).",
                        },
                        "close_code": {
                            "type": "string",
                            "description": "Resolution code when closing (e.g., 'Solved (Permanently)', 'Solved (Workaround)').",
                        },
                        "close_notes": {
                            "type": "string",
                            "description": "Resolution notes when closing the incident.",
                        },
                    },
                    "required": ["incident_number"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_service_request",
                "description": "Create a new service request (RITM) in ServiceNow for standard service catalog items like access requests, equipment orders, or software installations.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "catalog_item": {
                            "type": "string",
                            "description": "Name or sys_id of the service catalog item to request.",
                        },
                        "short_description": {
                            "type": "string",
                            "description": "Brief summary of the service request.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of what is being requested and any justification.",
                        },
                        "requested_for": {
                            "type": "string",
                            "description": "User ID or email of the person the request is for.",
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["1", "2", "3"],
                            "description": "Urgency level: 1 (High), 2 (Medium), 3 (Low).",
                        },
                        "variables": {
                            "type": "object",
                            "description": "Key-value pairs for catalog item variables (form fields specific to the catalog item).",
                        },
                    },
                    "required": ["catalog_item", "short_description"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a ServiceNow tool function."""
    handlers = {
        "create_incident": _create_incident,
        "query_incidents": _query_incidents,
        "update_incident": _update_incident,
        "create_service_request": _create_service_request,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _create_incident(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Create a new incident in ServiceNow."""
    # TODO: Implement with ServiceNow REST API (POST /api/now/table/incident)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "incident_number": None,
        "sys_id": None,
        "short_description": args.get("short_description"),
    }


async def _query_incidents(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Query incidents from ServiceNow."""
    # TODO: Implement with ServiceNow REST API (GET /api/now/table/incident)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "incidents": [],
        "total": 0,
    }


async def _update_incident(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Update an existing incident in ServiceNow."""
    # TODO: Implement with ServiceNow REST API (PATCH /api/now/table/incident/{sys_id})
    return {
        "status": "success",
        "message": "Not yet implemented",
        "incident_number": args.get("incident_number"),
    }


async def _create_service_request(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Create a service request in ServiceNow."""
    # TODO: Implement with ServiceNow Service Catalog API (POST /api/sn_sc/servicecatalog/items/{sys_id}/order_now)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "request_number": None,
        "ritm_number": None,
        "catalog_item": args.get("catalog_item"),
    }
