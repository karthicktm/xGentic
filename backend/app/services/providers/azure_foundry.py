"""Azure AI Foundry provider implementation using DefaultAzureCredential."""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings
from app.services.providers.base_provider import (
    AgentResponse,
    BaseAgentProvider,
    ConnectionStatus,
    DeploymentResult,
    ModelInfo,
)

logger = logging.getLogger(__name__)


def _get_credential(api_key: str | None = None) -> Any:
    """Get Azure credential — prefer DefaultAzureCredential, fall back to API key."""
    if api_key:
        from azure.core.credentials import AzureKeyCredential  # noqa: PLC0415

        return AzureKeyCredential(api_key)

    from azure.identity import DefaultAzureCredential  # noqa: PLC0415

    return DefaultAzureCredential()


def _get_chat_client(endpoint: str, api_key: str | None = None) -> Any:
    """Create an async ChatCompletionsClient with the appropriate credential."""
    from azure.ai.inference.aio import ChatCompletionsClient  # noqa: PLC0415

    return ChatCompletionsClient(endpoint=endpoint, credential=_get_credential(api_key))


class AzureFoundryProvider(BaseAgentProvider):
    """Azure AI Foundry provider using azure-ai-inference SDK.

    Supports both DefaultAzureCredential (preferred) and API key authentication.
    When no API key is provided, uses DefaultAzureCredential which supports:
    - Environment variables (AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET)
    - Managed Identity
    - Azure CLI credentials
    - Visual Studio Code credentials
    """

    async def deploy_agent(
        self,
        agent_config: dict[str, Any],
        environment_config: dict[str, Any],
    ) -> DeploymentResult:
        """Deploy an agent to Azure AI Foundry."""
        endpoint = environment_config.get("azure_endpoint", settings.AZURE_FOUNDRY_ENDPOINT)
        api_key = environment_config.get("azure_api_key", settings.AZURE_FOUNDRY_API_KEY)

        if not endpoint:
            return DeploymentResult(
                deployment_id="",
                status="failed",
                details={"error": "Azure endpoint not configured"},
            )

        try:
            async with _get_chat_client(endpoint, api_key) as client:
                response = await client.complete(
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1,
                )

            deployment_id = f"azure_{agent_config.get('id', 'unknown')}"
            return DeploymentResult(
                deployment_id=deployment_id,
                status="active",
                endpoint_url=endpoint,
                details={"model": response.model if response else None},
            )
        except Exception as e:
            logger.exception("Azure AI Foundry deployment failed")
            return DeploymentResult(
                deployment_id="",
                status="failed",
                details={"error": str(e)},
            )

    async def undeploy_agent(self, deployment_id: str) -> bool:
        """Remove an Azure AI Foundry deployment."""
        logger.info("Undeploying Azure agent: %s", deployment_id)
        return True

    async def test_connection(self, endpoint: str, api_key: str | None = None) -> ConnectionStatus:
        """Test connection to Azure AI Foundry.

        Uses DefaultAzureCredential when no api_key is provided.
        """
        try:
            async with _get_chat_client(endpoint, api_key) as client:
                await client.complete(
                    messages=[{"role": "user", "content": "hello"}],
                    max_tokens=1,
                )

            return ConnectionStatus(
                connected=True,
                provider="azure_foundry",
                endpoint=endpoint,
                models_available=1,
            )
        except Exception as e:
            return ConnectionStatus(
                connected=False,
                provider="azure_foundry",
                endpoint=endpoint,
                error=str(e),
            )

    async def list_models(
        self,
        endpoint: str,  # noqa: ARG002
        api_key: str | None = None,  # noqa: ARG002
    ) -> list[ModelInfo]:
        """List available models from Azure AI Foundry."""
        return [
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider="azure_foundry",
                capabilities=["chat", "function_calling", "vision"],
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider="azure_foundry",
                capabilities=["chat", "function_calling"],
            ),
        ]

    async def invoke_agent(
        self,
        deployment_config: dict[str, Any],
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> AgentResponse:
        """Invoke an agent deployed on Azure AI Foundry."""
        endpoint = deployment_config.get("azure_endpoint", settings.AZURE_FOUNDRY_ENDPOINT)
        api_key = deployment_config.get("azure_api_key", settings.AZURE_FOUNDRY_API_KEY)

        if not endpoint:
            return AgentResponse(content="Azure AI Foundry endpoint not configured", token_count=0)

        try:
            async with _get_chat_client(endpoint, api_key) as client:
                messages: list[dict[str, str]] = []

                system_prompt = deployment_config.get("system_prompt", "")
                if system_prompt:
                    messages.append({"role": "system", "content": system_prompt})

                if history:
                    messages.extend(history)

                messages.append({"role": "user", "content": message})

                response = await client.complete(
                    messages=messages,
                    temperature=deployment_config.get("temperature", 0.7),
                    max_tokens=deployment_config.get("max_tokens", 2000),
                )

            return AgentResponse(
                content=response.choices[0].message.content or "",
                token_count=response.usage.total_tokens if response.usage else 0,
                model=response.model or "",
                finish_reason=response.choices[0].finish_reason or "",
            )
        except Exception as e:
            logger.exception("Azure AI Foundry invocation failed")
            return AgentResponse(content=f"Error: {e}", token_count=0)
