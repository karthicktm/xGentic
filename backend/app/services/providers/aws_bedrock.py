"""AWS Bedrock provider — placeholder stub."""

from typing import Any

from app.services.providers.base_provider import (
    AgentResponse,
    BaseAgentProvider,
    ConnectionStatus,
    DeploymentResult,
    ModelInfo,
)


class AWSBedrockProvider(BaseAgentProvider):
    """AWS Bedrock provider stub — not yet implemented."""

    async def deploy_agent(
        self, agent_config: dict[str, Any], environment_config: dict[str, Any]
    ) -> DeploymentResult:
        return DeploymentResult(deployment_id="", status="not_implemented")

    async def undeploy_agent(self, deployment_id: str) -> bool:
        return False

    async def test_connection(self, endpoint: str, api_key: str) -> ConnectionStatus:
        return ConnectionStatus(connected=False, provider="aws_bedrock", endpoint=endpoint, error="Not implemented")

    async def list_models(self, endpoint: str, api_key: str) -> list[ModelInfo]:
        return []

    async def invoke_agent(
        self, deployment_config: dict[str, Any], message: str, history: list[dict[str, str]] | None = None
    ) -> AgentResponse:
        return AgentResponse(content="AWS Bedrock provider not yet implemented", token_count=0)
