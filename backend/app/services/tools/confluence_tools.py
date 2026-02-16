"""Confluence tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for Confluence operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_pages",
                "description": "Search for Confluence pages using CQL (Confluence Query Language) or free-text search across spaces.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query text to match against page titles and content.",
                        },
                        "space_key": {
                            "type": "string",
                            "description": "Optional Confluence space key to limit search scope (e.g., 'ENG', 'HR', 'IT').",
                        },
                        "label": {
                            "type": "string",
                            "description": "Optional label to filter pages by (e.g., 'runbook', 'policy', 'onboarding').",
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
        {
            "type": "function",
            "function": {
                "name": "get_page_content",
                "description": "Retrieve the full content of a specific Confluence page by its page ID or title.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "page_id": {
                            "type": "string",
                            "description": "The numeric Confluence page ID.",
                        },
                        "title": {
                            "type": "string",
                            "description": "Page title to look up (used if page_id is not provided). Must be combined with space_key.",
                        },
                        "space_key": {
                            "type": "string",
                            "description": "Space key where the page resides (required when searching by title).",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["storage", "view", "plain"],
                            "description": "Content format: 'storage' (raw), 'view' (rendered HTML), 'plain' (text only). Default 'plain'.",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_page",
                "description": "Create a new Confluence page in a specified space.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "space_key": {
                            "type": "string",
                            "description": "The Confluence space key where the page will be created.",
                        },
                        "title": {
                            "type": "string",
                            "description": "Title of the new page.",
                        },
                        "body": {
                            "type": "string",
                            "description": "Page content in Confluence storage format (XHTML) or plain text.",
                        },
                        "parent_page_id": {
                            "type": "string",
                            "description": "Optional parent page ID to nest the new page under.",
                        },
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of labels to apply to the new page.",
                        },
                    },
                    "required": ["space_key", "title", "body"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a Confluence tool function."""
    handlers = {
        "search_pages": _search_pages,
        "get_page_content": _get_page_content,
        "create_page": _create_page,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _search_pages(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Search for Confluence pages."""
    # TODO: Implement with Confluence REST API (GET /wiki/rest/api/content/search?cql=...)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "query": args.get("query"),
        "pages": [],
        "total": 0,
    }


async def _get_page_content(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Retrieve Confluence page content."""
    # TODO: Implement with Confluence REST API (GET /wiki/rest/api/content/{id}?expand=body.storage)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "page_id": args.get("page_id"),
        "title": args.get("title"),
        "content": None,
    }


async def _create_page(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Create a new Confluence page."""
    # TODO: Implement with Confluence REST API (POST /wiki/rest/api/content)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "page_id": None,
        "title": args.get("title"),
        "space_key": args.get("space_key"),
        "url": None,
    }
