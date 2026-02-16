"""Tool registry for managing available agent tools."""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Tool registry: maps integration IDs to their tool modules
_tool_registry: dict[str, Any] = {}


def register_tool(integration_id: str, tool_module: Any) -> None:
    """Register a tool module in the registry."""
    _tool_registry[integration_id] = tool_module
    logger.info("Registered tool: %s", integration_id)


def get_tool(integration_id: str) -> Any | None:
    """Get a registered tool module."""
    return _tool_registry.get(integration_id)


def get_all_tools() -> dict[str, Any]:
    """Get all registered tools."""
    return dict(_tool_registry)


def get_tool_definitions(integration_id: str) -> list[dict[str, Any]]:
    """Get tool definitions for an integration."""
    tool = get_tool(integration_id)
    if tool and hasattr(tool, "get_tool_definitions"):
        return tool.get_tool_definitions()
    return []


async def execute_tool(
    integration_id: str,
    tool_name: str,
    arguments: dict[str, Any],
    credentials: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a tool function."""
    tool = get_tool(integration_id)
    if not tool:
        return {"error": f"Tool integration '{integration_id}' not found"}

    if not hasattr(tool, "execute_tool"):
        return {"error": f"Tool '{integration_id}' does not support execution"}

    try:
        return await tool.execute_tool(tool_name, arguments, credentials)
    except Exception as e:
        logger.exception("Tool execution failed: %s.%s", integration_id, tool_name)
        return {"error": str(e)}


# Auto-register available tools
def initialize_tools() -> None:
    """Initialize and register all available tool modules."""
    from app.services.tools import (
        call_control_tools,
        campaign_tools,
        confluence_tools,
        crm_tools,
        dynamics365_tools,
        jira_tools,
        outlook_tools,
        pagerduty_tools,
        power_automate_tools,
        rag_tools,
        salesforce_tools,
        sap_tools,
        servicenow_tools,
        sharepoint_tools,
        site_search_tools,
        sms_tools,
        teams_tools,
    )

    register_tool("crm", crm_tools)
    register_tool("rag", rag_tools)
    register_tool("servicenow", servicenow_tools)
    register_tool("jira", jira_tools)
    register_tool("salesforce", salesforce_tools)
    register_tool("confluence", confluence_tools)
    register_tool("teams", teams_tools)
    register_tool("outlook", outlook_tools)
    register_tool("sharepoint", sharepoint_tools)
    register_tool("pagerduty", pagerduty_tools)
    register_tool("sms", sms_tools)
    register_tool("site_search", site_search_tools)
    register_tool("campaign", campaign_tools)
    register_tool("call_control", call_control_tools)
    register_tool("dynamics365", dynamics365_tools)
    register_tool("power_automate", power_automate_tools)
    register_tool("sap", sap_tools)
