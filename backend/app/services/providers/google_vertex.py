"""Google Vertex AI provider — placeholder stub."""

from typing import Any

from app.services.providers.base_provider import (
    AgentResponse,
    BaseAgentProvider,
    ConnectionStatus,
    DeploymentResult,
    ModelInfo,
)


class GoogleVertexProvider(BaseAgentProvider):
    """Google Vertex AI provider stub — not yet implemented."""

    async def deploy_agent(
        self, agent_config: dict[str, Any], environment_config: dict[str, Any]
    ) -> DeploymentResult:
        return DeploymentResult(deployment_id="", status="not_implemented")

    async def undeploy_agent(self, deployment_id: str) -> bool:
        return False

    async def test_connection(self, endpoint: str, api_key: str) -> ConnectionStatus:
        return ConnectionStatus(connected=False, provider="google_vertex", endpoint=endpoint, error="Not implemented")

    async def list_models(self, endpoint: str, api_key: str) -> list[ModelInfo]:
        return []

    async def invoke_agent(
        self, deployment_config: dict[str, Any], message: str, history: list[dict[str, str]] | None = None
    ) -> AgentResponse:
        return AgentResponse(content="Google Vertex provider not yet implemented", token_count=0)
