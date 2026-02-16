"""Outlook tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for Outlook/Exchange operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "check_availability",
                "description": "Check calendar availability for one or more users to find free time slots for meetings.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of email addresses to check availability for.",
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Start of the time range to check in ISO 8601 format (e.g., '2025-01-15T09:00:00').",
                        },
                        "end_time": {
                            "type": "string",
                            "description": "End of the time range to check in ISO 8601 format (e.g., '2025-01-15T17:00:00').",
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "Desired meeting duration in minutes (default 30). Used to find available slots.",
                        },
                        "timezone": {
                            "type": "string",
                            "description": "Timezone for the availability check (e.g., 'America/New_York', 'UTC'). Default 'UTC'.",
                        },
                    },
                    "required": ["attendees", "start_time", "end_time"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Send an email via Outlook/Exchange on behalf of the authenticated user.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of recipient email addresses.",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Email body content.",
                        },
                        "body_type": {
                            "type": "string",
                            "enum": ["text", "html"],
                            "description": "Body content type: 'text' for plain text or 'html' for HTML. Default 'text'.",
                        },
                        "cc": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of CC recipient email addresses.",
                        },
                        "importance": {
                            "type": "string",
                            "enum": ["low", "normal", "high"],
                            "description": "Email importance level. Default 'normal'.",
                        },
                    },
                    "required": ["to", "subject", "body"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "schedule_meeting",
                "description": "Schedule a meeting on the Outlook calendar with specified attendees, time, and details.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "Meeting subject/title.",
                        },
                        "start_time": {
                            "type": "string",
                            "description": "Meeting start time in ISO 8601 format (e.g., '2025-01-15T14:00:00').",
                        },
                        "end_time": {
                            "type": "string",
                            "description": "Meeting end time in ISO 8601 format (e.g., '2025-01-15T15:00:00').",
                        },
                        "attendees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of attendee email addresses.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Meeting description or agenda.",
                        },
                        "location": {
                            "type": "string",
                            "description": "Meeting location (room name, address, or virtual meeting link).",
                        },
                        "timezone": {
                            "type": "string",
                            "description": "Timezone for the meeting times (e.g., 'America/New_York'). Default 'UTC'.",
                        },
                        "is_online_meeting": {
                            "type": "boolean",
                            "description": "Whether to create a Teams online meeting link. Default false.",
                        },
                        "reminder_minutes": {
                            "type": "integer",
                            "description": "Reminder time in minutes before the meeting (default 15).",
                        },
                    },
                    "required": ["subject", "start_time", "end_time", "attendees"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute an Outlook tool function."""
    handlers = {
        "check_availability": _check_availability,
        "send_email": _send_email,
        "schedule_meeting": _schedule_meeting,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _check_availability(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Check calendar availability for attendees."""
    # TODO: Implement with Microsoft Graph API (POST /me/calendar/getSchedule)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "attendees": args.get("attendees"),
        "available_slots": [],
    }


async def _send_email(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Send an email via Outlook."""
    # TODO: Implement with Microsoft Graph API (POST /me/sendMail)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "to": args.get("to"),
        "subject": args.get("subject"),
    }


async def _schedule_meeting(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Schedule a meeting on Outlook calendar."""
    # TODO: Implement with Microsoft Graph API (POST /me/events)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "event_id": None,
        "subject": args.get("subject"),
        "start_time": args.get("start_time"),
        "end_time": args.get("end_time"),
    }
