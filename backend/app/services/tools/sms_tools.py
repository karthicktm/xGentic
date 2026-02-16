"""SMS tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for SMS operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "send_sms",
                "description": "Send an SMS text message to a phone number.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "Recipient phone number in E.164 format (e.g., +14155551234).",
                        },
                        "body": {
                            "type": "string",
                            "description": "Message content (max 1600 characters for SMS, longer messages will be split).",
                        },
                        "from_number": {
                            "type": "string",
                            "description": "Optional sender phone number to override the default. Must be a provisioned number.",
                        },
                        "media_url": {
                            "type": "string",
                            "description": "Optional URL of a media file to send as MMS (image, video, etc.).",
                        },
                    },
                    "required": ["to", "body"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "send_bulk_sms",
                "description": "Send the same SMS message to multiple recipients at once.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "recipients": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of recipient phone numbers in E.164 format.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Message content to send to all recipients.",
                        },
                        "from_number": {
                            "type": "string",
                            "description": "Optional sender phone number to override the default.",
                        },
                    },
                    "required": ["recipients", "body"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute an SMS tool function."""
    handlers = {
        "send_sms": _send_sms,
        "send_bulk_sms": _send_bulk_sms,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _send_sms(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Send a single SMS message."""
    # TODO: Implement with Twilio/Telnyx SMS API
    return {
        "status": "success",
        "message": "Not yet implemented",
        "message_id": None,
        "to": args.get("to"),
        "body_length": len(args.get("body", "")),
    }


async def _send_bulk_sms(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Send SMS to multiple recipients."""
    # TODO: Implement with Twilio/Telnyx SMS API (batch send)
    recipients = args.get("recipients", [])
    return {
        "status": "success",
        "message": "Not yet implemented",
        "recipient_count": len(recipients),
        "results": [],
    }
