"""Campaign tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for campaign operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_campaign_context",
                "description": (
                    "Retrieve the current campaign context including campaign details, "
                    "contact information, call script, and any custom data associated "
                    "with this outbound campaign call."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "campaign_id": {
                            "type": "string",
                            "description": "The campaign ID to retrieve context for.",
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "The contact ID within the campaign to get specific context for.",
                        },
                    },
                    "required": ["campaign_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "update_disposition",
                "description": (
                    "Record the outcome/disposition of this campaign call. "
                    "Call this before ending the call to capture the result."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "campaign_id": {
                            "type": "string",
                            "description": "The campaign ID this call belongs to.",
                        },
                        "contact_id": {
                            "type": "string",
                            "description": "The contact ID for this campaign call.",
                        },
                        "disposition": {
                            "type": "string",
                            "enum": [
                                "interested",
                                "appointment_booked",
                                "sale_made",
                                "callback_requested",
                                "info_sent",
                                "voicemail_left",
                                "wrong_number",
                                "not_available",
                                "transferred",
                                "not_interested",
                                "do_not_call",
                                "hung_up",
                            ],
                            "description": "The call outcome disposition code.",
                        },
                        "notes": {
                            "type": "string",
                            "description": "Brief notes about the call outcome and any follow-up actions needed.",
                        },
                        "callback_time": {
                            "type": "string",
                            "description": "If disposition is 'callback_requested', the preferred callback time in ISO 8601 format.",
                        },
                    },
                    "required": ["campaign_id", "contact_id", "disposition"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a campaign tool function."""
    handlers = {
        "get_campaign_context": _get_campaign_context,
        "update_disposition": _update_disposition,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _get_campaign_context(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Retrieve campaign context for the current call."""
    # TODO: Implement with campaign database lookup
    return {
        "status": "success",
        "message": "Not yet implemented",
        "campaign_id": args.get("campaign_id"),
        "contact_id": args.get("contact_id"),
        "campaign_name": None,
        "script": None,
        "contact_info": None,
        "custom_data": None,
    }


async def _update_disposition(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Record the call disposition for a campaign contact."""
    # TODO: Implement with campaign database update
    return {
        "status": "success",
        "message": "Not yet implemented",
        "action": "set_disposition",
        "campaign_id": args.get("campaign_id"),
        "contact_id": args.get("contact_id"),
        "disposition": args.get("disposition"),
        "notes": args.get("notes"),
    }
