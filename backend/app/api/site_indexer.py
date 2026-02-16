"""Site indexer API -- trigger website crawling for knowledge base."""

import uuid
from typing import Annotated, Any

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.agent import Agent
from app.models.integration import UserIntegration
from app.models.user import User

logger = structlog.get_logger()

router = APIRouter(prefix="/site-indexer", tags=["site-indexer"])


class CrawlRequest(BaseModel):
    """Request body for triggering a site crawl."""

    site_url: str
    max_pages: int = 50


class CrawlResponse(BaseModel):
    """Response after triggering a crawl."""

    status: str
    message: str


async def _run_crawl_background(
    agent_id: uuid.UUID,
    site_url: str,
    max_pages: int,
    embedding_config: dict[str, Any],
) -> None:
    """Background task to crawl and index a site."""
    from app.db.session import AsyncSessionLocal
    from app.services.site_indexer import SiteIndexer

    async with AsyncSessionLocal() as db:
        try:
            indexer = SiteIndexer(db, agent_id, embedding_config=embedding_config)
            result = await indexer.crawl_and_index(site_url, max_pages=max_pages)
            await indexer.update_last_crawl_at()
            logger.info("site_crawl_background_complete", agent_id=str(agent_id), **result)
        except Exception:
            logger.exception("site_crawl_background_failed", agent_id=str(agent_id))


@router.post(
    "/agents/{agent_id}/crawl",
    response_model=CrawlResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def trigger_site_crawl(
    agent_id: uuid.UUID,
    request: CrawlRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> CrawlResponse:
    """Trigger a background crawl of a website for knowledge base indexing.

    Crawls the specified site, extracts content, and processes it through
    the RAG pipeline (chunking, embedding).
    """
    # Verify agent ownership via organization
    result = await db.execute(
        select(Agent).where(
            Agent.id == agent_id,
            Agent.organization_id == current_user.organization_id,
        )
    )
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Validate max_pages
    max_pages = min(request.max_pages, 100)

    # Get embedding credentials from user integrations
    kb_credentials: dict[str, Any] = {}
    integration_result = await db.execute(
        select(UserIntegration).where(
            UserIntegration.user_id == current_user.id,
            UserIntegration.integration_type == "knowledge_base",
            UserIntegration.is_active.is_(True),
        )
    )
    integration = integration_result.scalar_one_or_none()
    if integration:
        kb_credentials = integration.credentials or {}

    if not kb_credentials.get("api_key"):
        # Fall back to global OpenAI key
        if settings.OPENAI_API_KEY:
            kb_credentials["api_key"] = settings.OPENAI_API_KEY
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Knowledge Base not configured. Please connect a Knowledge Base integration or configure OPENAI_API_KEY.",
            )

    # Get agent-specific settings
    agent_kb_settings = agent.tool_configs.get("knowledge_base", {}) if agent.tool_configs else {}

    embedding_config: dict[str, Any] = {
        "api_key": kb_credentials.get("api_key"),
        "embedding_model": kb_credentials.get("embedding_model", "text-embedding-3-small"),
        "embedding_provider": kb_credentials.get("embedding_provider", "openai"),
    }

    # Launch background crawl
    background_tasks.add_task(
        _run_crawl_background,
        agent_id,
        request.site_url,
        max_pages,
        embedding_config,
    )

    return CrawlResponse(
        status="crawling",
        message=f"Crawl started for {request.site_url} (up to {max_pages} pages). "
        "Documents will appear in the Knowledge Base as they are processed.",
    )
