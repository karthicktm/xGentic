"""PagerDuty tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for PagerDuty operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "create_incident",
                "description": "Create a new incident in PagerDuty to alert on-call responders about an issue requiring immediate attention.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Incident title describing the issue.",
                        },
                        "service_id": {
                            "type": "string",
                            "description": "The PagerDuty service ID to create the incident on.",
                        },
                        "urgency": {
                            "type": "string",
                            "enum": ["high", "low"],
                            "description": "Incident urgency level: 'high' triggers immediate notifications, 'low' uses low-urgency rules.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Detailed description of the incident with context, impact, and any relevant diagnostic information.",
                        },
                        "escalation_policy_id": {
                            "type": "string",
                            "description": "Optional escalation policy ID to override the service's default policy.",
                        },
                        "priority_id": {
                            "type": "string",
                            "description": "Optional priority ID (P1-P5) to set the incident priority.",
                        },
                        "incident_key": {
                            "type": "string",
                            "description": "Optional deduplication key. Incidents with the same key on the same service will be grouped.",
                        },
                    },
                    "required": ["title", "service_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "acknowledge_incident",
                "description": "Acknowledge a PagerDuty incident to indicate that someone is actively working on it.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "incident_id": {
                            "type": "string",
                            "description": "The PagerDuty incident ID to acknowledge.",
                        },
                        "acknowledger_email": {
                            "type": "string",
                            "description": "Email address of the user acknowledging the incident.",
                        },
                        "message": {
                            "type": "string",
                            "description": "Optional note to add when acknowledging (e.g., 'Investigating the issue').",
                        },
                    },
                    "required": ["incident_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "escalate_incident",
                "description": "Escalate a PagerDuty incident to the next level in the escalation policy or to a specific escalation policy.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "incident_id": {
                            "type": "string",
                            "description": "The PagerDuty incident ID to escalate.",
                        },
                        "escalation_level": {
                            "type": "integer",
                            "description": "Target escalation level number (e.g., 2 for the second level).",
                        },
                        "escalation_policy_id": {
                            "type": "string",
                            "description": "Optional escalation policy ID to reassign the incident to a different policy.",
                        },
                        "message": {
                            "type": "string",
                            "description": "Optional note explaining the reason for escalation.",
                        },
                    },
                    "required": ["incident_id"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a PagerDuty tool function."""
    handlers = {
        "create_incident": _create_incident,
        "acknowledge_incident": _acknowledge_incident,
        "escalate_incident": _escalate_incident,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _create_incident(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Create a new PagerDuty incident."""
    # TODO: Implement with PagerDuty REST API (POST /incidents)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "incident_id": None,
        "incident_number": None,
        "title": args.get("title"),
        "service_id": args.get("service_id"),
        "urgency": args.get("urgency", "high"),
    }


async def _acknowledge_incident(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Acknowledge a PagerDuty incident."""
    # TODO: Implement with PagerDuty REST API (PUT /incidents/{id} with status=acknowledged)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "incident_id": args.get("incident_id"),
        "acknowledged": True,
    }


async def _escalate_incident(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Escalate a PagerDuty incident."""
    # TODO: Implement with PagerDuty REST API (PUT /incidents/{id}/escalate)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "incident_id": args.get("incident_id"),
        "escalation_level": args.get("escalation_level"),
    }
