"""SAP tools for agent function calling (placeholder)."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for SAP operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "query_materials",
                "description": "Query materials (products) from SAP Material Master with optional filters for material type, plant, and availability.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "material_number": {
                            "type": "string",
                            "description": "SAP material number to look up directly (e.g., '000000000000001234').",
                        },
                        "search_term": {
                            "type": "string",
                            "description": "Free-text search term to match against material description.",
                        },
                        "material_type": {
                            "type": "string",
                            "description": "Filter by material type code (e.g., 'FERT' for finished goods, 'ROH' for raw materials, 'HALB' for semi-finished).",
                        },
                        "plant": {
                            "type": "string",
                            "description": "Filter by plant code (e.g., '1000').",
                        },
                        "material_group": {
                            "type": "string",
                            "description": "Filter by material group code.",
                        },
                        "include_stock": {
                            "type": "boolean",
                            "description": "Whether to include current stock/inventory levels. Default false.",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of materials to return (default 10, max 100).",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_order",
                "description": "Retrieve details of a sales order, purchase order, or production order from SAP.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_number": {
                            "type": "string",
                            "description": "The SAP order number to look up.",
                        },
                        "order_type": {
                            "type": "string",
                            "enum": ["sales", "purchase", "production"],
                            "description": "Type of order to query: 'sales' (SD), 'purchase' (MM), or 'production' (PP).",
                        },
                        "include_items": {
                            "type": "boolean",
                            "description": "Whether to include individual line items in the response. Default true.",
                        },
                        "include_status": {
                            "type": "boolean",
                            "description": "Whether to include detailed status and delivery tracking. Default true.",
                        },
                    },
                    "required": ["order_number", "order_type"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a SAP tool function."""
    handlers = {
        "query_materials": _query_materials,
        "get_order": _get_order,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _query_materials(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Query materials from SAP Material Master."""
    # TODO: Implement with SAP OData API or RFC/BAPI calls
    return {
        "status": "success",
        "message": "Not yet implemented — SAP placeholder",
        "material_number": args.get("material_number"),
        "search_term": args.get("search_term"),
        "materials": [],
        "total": 0,
    }


async def _get_order(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Retrieve order details from SAP."""
    # TODO: Implement with SAP OData API or RFC/BAPI calls
    return {
        "status": "success",
        "message": "Not yet implemented — SAP placeholder",
        "order_number": args.get("order_number"),
        "order_type": args.get("order_type"),
        "order_details": None,
        "items": [],
        "status_info": None,
    }
