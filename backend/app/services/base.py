"""Base service class for external API integrations."""

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class ExternalServiceError(Exception):
    """Base exception for external service errors."""

    def __init__(self, service: str, message: str, status_code: int | None = None) -> None:
        self.service = service
        self.status_code = status_code
        super().__init__(f"{service}: {message}")


class ExternalServiceTimeoutError(ExternalServiceError):
    """Timeout error for external service calls."""


class ExternalServiceRateLimitError(ExternalServiceError):
    """Rate limit error for external service calls."""

    def __init__(self, service: str, retry_after: float | None = None) -> None:
        self.retry_after = retry_after
        super().__init__(service, "Rate limit exceeded", status_code=429)


class BaseExternalService:
    """Base class for external service integrations with retry logic."""

    service_name: str = "external"
    default_timeout: float = 30.0

    def __init__(self, timeout: float | None = None) -> None:
        self.timeout = timeout or self.default_timeout
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int | None = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """Make HTTP request with exponential backoff retry."""
        retries = max_retries or settings.MAX_RETRIES
        client = await self._get_client()

        for attempt in range(retries + 1):
            try:
                response = await client.request(method, url, **kwargs)

                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", "5"))
                    if attempt < retries:
                        logger.warning(
                            "%s rate limited, retrying after %ss (attempt %d/%d)",
                            self.service_name,
                            retry_after,
                            attempt + 1,
                            retries,
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise ExternalServiceRateLimitError(
                        self.service_name, retry_after=retry_after
                    )

                response.raise_for_status()
                return response

            except httpx.TimeoutException as exc:
                if attempt < retries:
                    wait = settings.RETRY_BACKOFF_FACTOR**attempt
                    logger.warning(
                        "%s timeout, retrying in %ss (attempt %d/%d)",
                        self.service_name,
                        wait,
                        attempt + 1,
                        retries,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise ExternalServiceTimeoutError(
                    self.service_name, "Request timed out"
                ) from exc

            except httpx.HTTPStatusError as exc:
                if attempt < retries and exc.response.status_code >= 500:
                    wait = settings.RETRY_BACKOFF_FACTOR**attempt
                    logger.warning(
                        "%s server error %d, retrying in %ss (attempt %d/%d)",
                        self.service_name,
                        exc.response.status_code,
                        wait,
                        attempt + 1,
                        retries,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise ExternalServiceError(
                    self.service_name,
                    f"HTTP {exc.response.status_code}: {exc.response.text}",
                    status_code=exc.response.status_code,
                ) from exc

        raise ExternalServiceError(self.service_name, "Max retries exceeded")
