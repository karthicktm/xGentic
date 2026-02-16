"""Microsoft Teams tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for Microsoft Teams operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "send_message",
                "description": "Send a message to a Microsoft Teams channel or chat.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "channel_id": {
                            "type": "string",
                            "description": "The Teams channel ID to send the message to.",
                        },
                        "team_id": {
                            "type": "string",
                            "description": "The Teams team ID that the channel belongs to.",
                        },
                        "content": {
                            "type": "string",
                            "description": "The message content. Supports plain text and basic HTML formatting.",
                        },
                        "content_type": {
                            "type": "string",
                            "enum": ["text", "html"],
                            "description": "Content format: 'text' for plain text or 'html' for HTML-formatted messages. Default 'text'.",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Optional message subject line (appears as a header in the channel).",
                        },
                        "importance": {
                            "type": "string",
                            "enum": ["normal", "high", "urgent"],
                            "description": "Message importance level. Default 'normal'.",
                        },
                    },
                    "required": ["channel_id", "team_id", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_channel",
                "description": "Create a new channel in a Microsoft Teams team.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "The Teams team ID to create the channel in.",
                        },
                        "display_name": {
                            "type": "string",
                            "description": "Display name for the new channel (max 50 characters).",
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description of the channel's purpose.",
                        },
                        "membership_type": {
                            "type": "string",
                            "enum": ["standard", "private", "shared"],
                            "description": "Channel type: 'standard' (visible to all team members), 'private' (invite-only), 'shared' (cross-team). Default 'standard'.",
                        },
                    },
                    "required": ["team_id", "display_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_channels",
                "description": "List all channels in a Microsoft Teams team.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "team_id": {
                            "type": "string",
                            "description": "The Teams team ID to list channels for.",
                        },
                        "filter": {
                            "type": "string",
                            "enum": ["all", "standard", "private", "shared"],
                            "description": "Filter channels by membership type. Default 'all'.",
                        },
                    },
                    "required": ["team_id"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a Microsoft Teams tool function."""
    handlers = {
        "send_message": _send_message,
        "create_channel": _create_channel,
        "list_channels": _list_channels,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _send_message(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Send a message to a Teams channel."""
    # TODO: Implement with Microsoft Graph API (POST /teams/{team-id}/channels/{channel-id}/messages)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "message_id": None,
        "channel_id": args.get("channel_id"),
        "team_id": args.get("team_id"),
    }


async def _create_channel(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Create a new Teams channel."""
    # TODO: Implement with Microsoft Graph API (POST /teams/{team-id}/channels)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "channel_id": None,
        "display_name": args.get("display_name"),
        "team_id": args.get("team_id"),
    }


async def _list_channels(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """List channels in a Teams team."""
    # TODO: Implement with Microsoft Graph API (GET /teams/{team-id}/channels)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "team_id": args.get("team_id"),
        "channels": [],
        "total": 0,
    }
