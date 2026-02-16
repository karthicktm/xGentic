"""Abstract base class for AI agent providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class DeploymentResult:
    """Result from deploying an agent."""

    deployment_id: str
    status: str
    endpoint_url: str | None = None
    details: dict[str, Any] | None = None


@dataclass
class ConnectionStatus:
    """Result from testing a provider connection."""

    connected: bool
    provider: str
    endpoint: str
    models_available: int = 0
    error: str | None = None


@dataclass
class ModelInfo:
    """Information about an available model."""

    id: str
    name: str
    provider: str
    capabilities: list[str] | None = None


@dataclass
class AgentResponse:
    """Response from invoking an agent."""

    content: str
    token_count: int = 0
    model: str = ""
    finish_reason: str = ""
    metadata: dict[str, Any] | None = None


class BaseAgentProvider(ABC):
    """Abstract interface for AI agent providers."""

    @abstractmethod
    async def deploy_agent(
        self,
        agent_config: dict[str, Any],
        environment_config: dict[str, Any],
    ) -> DeploymentResult:
        """Deploy an agent to the provider infrastructure."""

    @abstractmethod
    async def undeploy_agent(self, deployment_id: str) -> bool:
        """Remove an agent deployment."""

    @abstractmethod
    async def test_connection(
        self, endpoint: str, api_key: str
    ) -> ConnectionStatus:
        """Test connection to the provider."""

    @abstractmethod
    async def list_models(self, endpoint: str, api_key: str) -> list[ModelInfo]:
        """List available models from the provider."""

    @abstractmethod
    async def invoke_agent(
        self,
        deployment_config: dict[str, Any],
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> AgentResponse:
        """Invoke a deployed agent with a message."""
