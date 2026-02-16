"""Azure AI Foundry API routes — connection testing, model listing, agent import/deploy."""

import uuid
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AdminUser, CurrentUser
from app.core.config import settings
from app.core.public_id import generate_public_id
from app.db.session import get_db
from app.models.agent import Agent, AgentStatus, AgentType
from app.services.providers.azure_foundry import AzureFoundryProvider

router = APIRouter(prefix="/azure-foundry", tags=["Azure AI Foundry"])

_provider = AzureFoundryProvider()


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class TestConnectionRequest(BaseModel):
    endpoint: str | None = None
    api_key: str | None = None


class ImportAgentRequest(BaseModel):
    name: str
    agent_type: str = "chat"
    system_prompt: str = ""
    azure_foundry_agent_id: str
    azure_endpoint: str | None = None
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 2000


# ---------------------------------------------------------------------------
# POST /azure-foundry/test-connection
# ---------------------------------------------------------------------------


@router.post("/test-connection")
async def test_azure_connection(
    data: TestConnectionRequest,
    current_user: AdminUser,  # noqa: ARG001
) -> dict[str, Any]:
    """Test connection to Azure AI Foundry using DefaultAzureCredential or API key."""
    endpoint = data.endpoint or settings.AZURE_FOUNDRY_ENDPOINT
    if not endpoint:
        raise HTTPException(status_code=400, detail="No Azure endpoint configured")

    result = await _provider.test_connection(endpoint, data.api_key)
    return asdict(result)


# ---------------------------------------------------------------------------
# GET /azure-foundry/models
# ---------------------------------------------------------------------------


@router.get("/models")
async def list_azure_models(
    current_user: CurrentUser,  # noqa: ARG001
) -> list[dict[str, Any]]:
    """List available models from Azure AI Foundry."""
    endpoint = settings.AZURE_FOUNDRY_ENDPOINT
    if not endpoint:
        raise HTTPException(status_code=400, detail="No Azure endpoint configured")

    models = await _provider.list_models(endpoint, settings.AZURE_FOUNDRY_API_KEY)
    return [asdict(m) for m in models]


# ---------------------------------------------------------------------------
# POST /azure-foundry/import-agent
# ---------------------------------------------------------------------------


@router.post("/import-agent")
async def import_azure_agent(
    data: ImportAgentRequest,
    current_user: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Import an existing Azure Foundry agent configuration as a local agent."""
    if not current_user.organization_id:
        raise HTTPException(status_code=400, detail="User must belong to an organization")

    agent = Agent(
        user_id=current_user.id,
        organization_id=current_user.organization_id,
        name=data.name,
        description=f"Imported from Azure Foundry ({data.azure_foundry_agent_id})",
        agent_type=AgentType(data.agent_type),
        status=AgentStatus.DRAFT,
        system_prompt=data.system_prompt,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        provider_type="azure_foundry",
        provider_config={
            "azure_endpoint": data.azure_endpoint or settings.AZURE_FOUNDRY_ENDPOINT,
            "model": data.model,
        },
        agent_source="azure_foundry",
        azure_foundry_agent_id=data.azure_foundry_agent_id,
        public_id=generate_public_id("ag"),
    )
    db.add(agent)
    await db.flush()

    return {
        "id": str(agent.id),
        "name": agent.name,
        "agent_source": agent.agent_source,
        "azure_foundry_agent_id": agent.azure_foundry_agent_id,
        "status": agent.status.value if isinstance(agent.status, AgentStatus) else agent.status,
        "created_at": agent.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# POST /azure-foundry/deploy/{agent_id}
# ---------------------------------------------------------------------------


@router.post("/deploy/{agent_id}")
async def deploy_to_azure(
    agent_id: uuid.UUID,
    current_user: AdminUser,  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Deploy a local agent to Azure AI Foundry."""
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent_config = {
        "id": str(agent.id),
        "name": agent.name,
        "system_prompt": agent.system_prompt,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
    }

    environment_config = {
        "azure_endpoint": (agent.provider_config or {}).get(
            "azure_endpoint", settings.AZURE_FOUNDRY_ENDPOINT
        ),
        "azure_api_key": (agent.provider_config or {}).get(
            "azure_api_key", settings.AZURE_FOUNDRY_API_KEY
        ),
    }

    deployment = await _provider.deploy_agent(agent_config, environment_config)

    if deployment.status == "active":
        agent.agent_source = "azure_foundry"
        agent.azure_foundry_agent_id = deployment.deployment_id
        await db.flush()

    return asdict(deployment)
