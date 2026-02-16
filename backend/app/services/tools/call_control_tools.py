"""Call control tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for call control operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "transfer_call",
                "description": (
                    "Transfer the current call to another phone number or department. "
                    "Inform the caller before transferring. Use this when the caller "
                    "needs to speak with a human agent, specialist, or another department."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "destination": {
                            "type": "string",
                            "description": "Phone number (E.164 format like +14155551234) or SIP URI to transfer to.",
                        },
                        "announce": {
                            "type": "string",
                            "description": "Optional message to announce to the destination before connecting the caller.",
                        },
                        "transfer_type": {
                            "type": "string",
                            "enum": ["blind", "warm"],
                            "description": "Transfer type: 'blind' (immediate transfer) or 'warm' (announce first). Default 'blind'.",
                        },
                    },
                    "required": ["destination"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "end_call",
                "description": (
                    "End the current phone call. Always say a brief farewell before calling "
                    "this function. Use when the conversation is complete, the caller wants "
                    "to hang up, or you have said goodbye."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": (
                                "Brief reason for ending the call (e.g., 'conversation_complete', "
                                "'caller_requested', 'no_response', 'transferred', 'escalated')."
                            ),
                        },
                    },
                    "required": ["reason"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "mute_call",
                "description": (
                    "Mute or unmute the agent's microphone during the call. Use this when "
                    "the agent needs to temporarily stop sending audio, for example during "
                    "a hold period or while processing a request."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "muted": {
                            "type": "boolean",
                            "description": "True to mute the agent microphone, false to unmute.",
                        },
                        "play_hold_music": {
                            "type": "boolean",
                            "description": "Whether to play hold music while muted. Default false.",
                        },
                    },
                    "required": ["muted"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a call control tool function."""
    handlers = {
        "transfer_call": _transfer_call,
        "end_call": _end_call,
        "mute_call": _mute_call,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _transfer_call(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Transfer the call to another destination."""
    # TODO: Implement with telephony provider API (Telnyx/Twilio)
    destination = args.get("destination", "")
    if not destination:
        return {"status": "error", "message": "Destination is required for transfer"}
    return {
        "status": "success",
        "message": "Not yet implemented",
        "action": "transfer_call",
        "destination": destination,
        "transfer_type": args.get("transfer_type", "blind"),
        "announce": args.get("announce"),
    }


async def _end_call(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """End the current call."""
    # TODO: Implement with telephony provider API (Telnyx/Twilio)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "action": "end_call",
        "reason": args.get("reason", "conversation_complete"),
    }


async def _mute_call(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Mute or unmute the agent microphone."""
    # TODO: Implement with telephony provider API (Telnyx/Twilio)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "action": "mute_call",
        "muted": args.get("muted", True),
        "play_hold_music": args.get("play_hold_music", False),
    }
