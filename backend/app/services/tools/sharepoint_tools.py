"""SharePoint tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for SharePoint operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "search_documents",
                "description": "Search for documents across SharePoint sites and document libraries using keyword or full-text search.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find documents by name, content, or metadata.",
                        },
                        "site_id": {
                            "type": "string",
                            "description": "Optional SharePoint site ID to limit search scope.",
                        },
                        "file_type": {
                            "type": "string",
                            "description": "Filter by file extension (e.g., 'docx', 'pdf', 'xlsx', 'pptx').",
                        },
                        "modified_after": {
                            "type": "string",
                            "description": "Filter for documents modified after this date (YYYY-MM-DD format).",
                        },
                        "author": {
                            "type": "string",
                            "description": "Filter by document author name or email.",
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
                "name": "get_file",
                "description": "Retrieve metadata and download link for a specific file in SharePoint by its item ID or path.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "item_id": {
                            "type": "string",
                            "description": "The SharePoint drive item ID of the file.",
                        },
                        "site_id": {
                            "type": "string",
                            "description": "The SharePoint site ID where the file is located.",
                        },
                        "file_path": {
                            "type": "string",
                            "description": "Relative path to the file within the document library (e.g., '/Documents/Reports/Q1-2025.xlsx'). Used if item_id is not provided.",
                        },
                        "include_content": {
                            "type": "boolean",
                            "description": "Whether to include the file content as text (for supported text-based formats). Default false.",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_folder",
                "description": "List files and subfolders in a SharePoint document library folder.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "site_id": {
                            "type": "string",
                            "description": "The SharePoint site ID.",
                        },
                        "folder_path": {
                            "type": "string",
                            "description": "Path to the folder within the document library (e.g., '/Documents/Reports'). Use '/' or empty for root.",
                        },
                        "drive_id": {
                            "type": "string",
                            "description": "Optional drive ID if not using the default document library.",
                        },
                        "include_subfolders": {
                            "type": "boolean",
                            "description": "Whether to include subfolders in the listing. Default true.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of items to return (default 50, max 200).",
                        },
                    },
                    "required": ["site_id"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a SharePoint tool function."""
    handlers = {
        "search_documents": _search_documents,
        "get_file": _get_file,
        "list_folder": _list_folder,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _search_documents(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Search for documents in SharePoint."""
    # TODO: Implement with Microsoft Graph API (GET /sites/{site-id}/drive/root/search(q='{query}'))
    return {
        "status": "success",
        "message": "Not yet implemented",
        "query": args.get("query"),
        "documents": [],
        "total": 0,
    }


async def _get_file(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Retrieve a specific file from SharePoint."""
    # TODO: Implement with Microsoft Graph API (GET /sites/{site-id}/drive/items/{item-id})
    return {
        "status": "success",
        "message": "Not yet implemented",
        "item_id": args.get("item_id"),
        "file_path": args.get("file_path"),
        "name": None,
        "download_url": None,
        "content": None,
    }


async def _list_folder(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """List contents of a SharePoint folder."""
    # TODO: Implement with Microsoft Graph API (GET /sites/{site-id}/drive/root:/{path}:/children)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "site_id": args.get("site_id"),
        "folder_path": args.get("folder_path", "/"),
        "items": [],
        "total": 0,
    }
