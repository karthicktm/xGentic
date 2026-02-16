"""Request tracing middleware with correlation IDs."""

import logging
import time
import uuid

from starlette.types import ASGIApp, Receive, Scope, Send

logger = logging.getLogger(__name__)


class RequestTracingMiddleware:
    """Add correlation IDs and request logging to all HTTP requests."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract or generate correlation ID
        headers = dict(scope.get("headers", []))
        correlation_id = headers.get(b"x-correlation-id", b"").decode() or str(uuid.uuid4())

        # Extract client IP (with proxy support)
        forwarded_for = headers.get(b"x-forwarded-for", b"").decode()
        client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else ""
        if not client_ip and scope.get("client"):
            client_ip = scope["client"][0]

        # Log request start
        path = scope.get("path", "")
        method = scope.get("method", "")
        start_time = time.monotonic()

        logger.info(
            "Request started",
            extra={
                "correlation_id": correlation_id,
                "method": method,
                "path": path,
                "client_ip": client_ip,
            },
        )

        async def send_with_tracing(message: dict) -> None:  # type: ignore[type-arg]
            if message["type"] == "http.response.start":
                # Add correlation ID to response headers
                response_headers = list(message.get("headers", []))
                response_headers.append(
                    (b"x-correlation-id", correlation_id.encode())
                )
                message["headers"] = response_headers

                # Log request completion
                duration = time.monotonic() - start_time
                status_code = message.get("status", 0)
                logger.info(
                    "Request completed",
                    extra={
                        "correlation_id": correlation_id,
                        "method": method,
                        "path": path,
                        "status_code": status_code,
                        "duration_ms": round(duration * 1000, 2),
                    },
                )

            await send(message)

        await self.app(scope, receive, send_with_tracing)
