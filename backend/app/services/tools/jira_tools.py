"""Jira tools for agent function calling."""

from typing import Any


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return OpenAI-compatible function definitions for Jira operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "create_issue",
                "description": "Create a new issue (bug, task, story, or epic) in a Jira project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_key": {
                            "type": "string",
                            "description": "The Jira project key (e.g., 'ENG', 'SUPPORT', 'OPS').",
                        },
                        "summary": {
                            "type": "string",
                            "description": "Brief summary or title of the issue.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Detailed description of the issue including steps to reproduce, expected behavior, and actual behavior for bugs.",
                        },
                        "issue_type": {
                            "type": "string",
                            "enum": ["Bug", "Task", "Story", "Epic", "Sub-task"],
                            "description": "Type of Jira issue to create.",
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["Highest", "High", "Medium", "Low", "Lowest"],
                            "description": "Issue priority level.",
                        },
                        "assignee": {
                            "type": "string",
                            "description": "Account ID or email of the user to assign the issue to.",
                        },
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of labels to apply to the issue.",
                        },
                        "components": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of component names to associate with the issue.",
                        },
                    },
                    "required": ["project_key", "summary", "issue_type"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_issues",
                "description": "Search for Jira issues using JQL (Jira Query Language) or free-text search.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "jql": {
                            "type": "string",
                            "description": "JQL query string (e.g., 'project = ENG AND status = Open AND assignee = currentUser()').",
                        },
                        "query": {
                            "type": "string",
                            "description": "Free-text search query as an alternative to JQL. Searches summary, description, and comments.",
                        },
                        "project_key": {
                            "type": "string",
                            "description": "Optional project key to scope the search.",
                        },
                        "status": {
                            "type": "string",
                            "description": "Filter by issue status (e.g., 'Open', 'In Progress', 'Done').",
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to return (default 10, max 50).",
                        },
                    },
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "transition_issue",
                "description": "Transition a Jira issue to a new status (e.g., move from 'To Do' to 'In Progress' or 'Done').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "The Jira issue key (e.g., 'ENG-1234').",
                        },
                        "transition_name": {
                            "type": "string",
                            "description": "Name of the transition to perform (e.g., 'Start Progress', 'Resolve', 'Close', 'Reopen').",
                        },
                        "comment": {
                            "type": "string",
                            "description": "Optional comment to add when transitioning the issue.",
                        },
                        "resolution": {
                            "type": "string",
                            "description": "Resolution type when resolving/closing (e.g., 'Fixed', 'Won\\'t Fix', 'Duplicate').",
                        },
                    },
                    "required": ["issue_key", "transition_name"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "add_comment",
                "description": "Add a comment to an existing Jira issue.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "issue_key": {
                            "type": "string",
                            "description": "The Jira issue key (e.g., 'ENG-1234').",
                        },
                        "body": {
                            "type": "string",
                            "description": "The comment text to add. Supports Jira wiki markup or Atlassian Document Format.",
                        },
                        "visibility": {
                            "type": "string",
                            "enum": ["public", "internal"],
                            "description": "Comment visibility: 'public' (visible to all) or 'internal' (visible to service desk agents only).",
                        },
                    },
                    "required": ["issue_key", "body"],
                },
            },
        },
    ]


async def execute_tool(
    tool_name: str, arguments: dict[str, Any], credentials: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Execute a Jira tool function."""
    handlers = {
        "create_issue": _create_issue,
        "search_issues": _search_issues,
        "transition_issue": _transition_issue,
        "add_comment": _add_comment,
    }
    handler = handlers.get(tool_name)
    if not handler:
        return {"error": f"Unknown tool: {tool_name}"}
    return await handler(arguments, credentials)


async def _create_issue(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Create a new Jira issue."""
    # TODO: Implement with Jira REST API v3 (POST /rest/api/3/issue)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "issue_key": None,
        "issue_id": None,
        "summary": args.get("summary"),
        "project_key": args.get("project_key"),
    }


async def _search_issues(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Search for Jira issues."""
    # TODO: Implement with Jira REST API v3 (POST /rest/api/3/search)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "issues": [],
        "total": 0,
        "jql": args.get("jql"),
    }


async def _transition_issue(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Transition a Jira issue to a new status."""
    # TODO: Implement with Jira REST API v3 (POST /rest/api/3/issue/{issueIdOrKey}/transitions)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "issue_key": args.get("issue_key"),
        "transition": args.get("transition_name"),
    }


async def _add_comment(
    args: dict[str, Any], creds: dict[str, Any] | None
) -> dict[str, Any]:
    """Add a comment to a Jira issue."""
    # TODO: Implement with Jira REST API v3 (POST /rest/api/3/issue/{issueIdOrKey}/comment)
    return {
        "status": "success",
        "message": "Not yet implemented",
        "issue_key": args.get("issue_key"),
        "comment_id": None,
    }
