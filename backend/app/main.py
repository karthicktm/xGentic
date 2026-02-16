"""xGentic API — Enterprise Multi-Agent Platform."""

# Bcrypt version workaround for passlib
import importlib
import sys

if "bcrypt" in sys.modules:
    bcrypt_module = sys.modules["bcrypt"]
else:
    bcrypt_module = importlib.import_module("bcrypt")
if not hasattr(bcrypt_module, "__about__"):
    bcrypt_module.__about__ = type("about", (), {"__version__": bcrypt_module.__version__})()

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.limiter import limiter
from app.db.redis import close_redis, get_redis
from app.db.session import engine
from app.middleware.request_tracing import RequestTracingMiddleware
from app.middleware.security import SecurityHeadersMiddleware

# Configure structured logging
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG if settings.DEBUG else logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown."""
    # Startup
    try:
        await get_redis()
        await logger.ainfo("Redis connected")
    except Exception:
        await logger.aerror("Failed to connect to Redis")
        raise

    # Initialize Sentry if configured
    if settings.SENTRY_DSN:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.SENTRY_ENVIRONMENT,
            traces_sample_rate=settings.SENTRY_TRACES_SAMPLE_RATE,
            integrations=[FastApiIntegration()],
        )
        await logger.ainfo("Sentry initialized")

    # Create super admin if configured
    if settings.SUPER_ADMIN_EMAIL and settings.SUPER_ADMIN_PASSWORD:
        from app.api.auth import hash_password
        from app.db.session import AsyncSessionLocal
        from app.models.user import AuthProvider, User, UserRole

        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.email == settings.SUPER_ADMIN_EMAIL)
            )
            if not result.scalar_one_or_none():
                admin = User(
                    email=settings.SUPER_ADMIN_EMAIL,
                    hashed_password=hash_password(settings.SUPER_ADMIN_PASSWORD),
                    full_name=settings.SUPER_ADMIN_NAME or "Super Admin",
                    provider=AuthProvider.EMAIL,
                    role=UserRole.SUPER_ADMIN,
                    email_verified=True,
                    is_active=True,
                    is_superuser=True,
                )
                session.add(admin)
                await session.commit()
                await logger.ainfo("Super admin created", email=settings.SUPER_ADMIN_EMAIL)

    await logger.ainfo("xGentic API started", version=settings.APP_VERSION)

    yield

    # Shutdown
    await close_redis()
    await engine.dispose()
    await logger.ainfo("xGentic API shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions."""
    logging.getLogger(__name__).exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        },
    )


# Middleware stack (order matters — first added = outermost)
app.add_middleware(RequestTracingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS
cors_origins: list[str] = list(settings.CORS_ORIGINS)
if settings.FRONTEND_URL and settings.FRONTEND_URL not in cors_origins:
    cors_origins.append(settings.FRONTEND_URL)
if settings.PUBLIC_URL and settings.PUBLIC_URL not in cors_origins:
    cors_origins.append(settings.PUBLIC_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# === Route Registration ===
from app.api.agent_deployments import router as agent_deployments_router
from app.api.agents import router as agents_router
from app.api.azure_foundry import router as azure_foundry_router
from app.api.documents import router as documents_router
from app.api.audit_logs import router as audit_logs_router
from app.api.auth import router as auth_router
from app.api.campaigns import router as campaigns_router
from app.api.compliance import router as compliance_router
from app.api.contacts import router as contacts_router
from app.api.departments import router as departments_router, simple_router as departments_simple_router
from app.api.embed import router as embed_router
from app.api.embed import ws_router as embed_ws_router
from app.api.environments import router as environments_router
from app.api.health import router as health_router
from app.api.hierarchy import router as hierarchy_router
from app.api.integrations import router as integrations_router
from app.api.interactions import router as interactions_router
from app.api.organizations import router as organizations_router
from app.api.projects import router as projects_router, simple_router as projects_simple_router
from app.api.settings import router as settings_router
from app.api.site_indexer import router as site_indexer_router
from app.api.units import router as units_router, simple_router as units_simple_router
from app.api.usage import router as usage_router
from app.api.users import router as users_router
from app.api.workspaces import router as workspaces_router, simple_router as workspaces_simple_router

# Health (no prefix)
app.include_router(health_router)

# Auth
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)

# Organization hierarchy
app.include_router(organizations_router, prefix=settings.API_V1_PREFIX)
app.include_router(units_router, prefix=settings.API_V1_PREFIX)
app.include_router(units_simple_router, prefix=settings.API_V1_PREFIX)  # Simplified endpoint
app.include_router(departments_router, prefix=settings.API_V1_PREFIX)
app.include_router(departments_simple_router, prefix=settings.API_V1_PREFIX)  # Simplified endpoint
app.include_router(projects_router, prefix=settings.API_V1_PREFIX)
app.include_router(projects_simple_router, prefix=settings.API_V1_PREFIX)  # Simplified endpoint
app.include_router(workspaces_router, prefix=settings.API_V1_PREFIX)
app.include_router(workspaces_simple_router, prefix=settings.API_V1_PREFIX)  # Simplified endpoint
app.include_router(hierarchy_router, prefix=settings.API_V1_PREFIX)

# Agents & environments
app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
app.include_router(agent_deployments_router, prefix=settings.API_V1_PREFIX)
app.include_router(azure_foundry_router, prefix=settings.API_V1_PREFIX)
app.include_router(environments_router, prefix=settings.API_V1_PREFIX)

# Enterprise features
app.include_router(interactions_router, prefix=settings.API_V1_PREFIX)
app.include_router(campaigns_router, prefix=settings.API_V1_PREFIX)
app.include_router(contacts_router, prefix=settings.API_V1_PREFIX)
app.include_router(integrations_router, prefix=settings.API_V1_PREFIX)

# Knowledge base
app.include_router(documents_router, prefix=settings.API_V1_PREFIX)
app.include_router(site_indexer_router, prefix=settings.API_V1_PREFIX)

# Administration
app.include_router(users_router, prefix=settings.API_V1_PREFIX)
app.include_router(settings_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_logs_router, prefix=settings.API_V1_PREFIX)
app.include_router(compliance_router, prefix=settings.API_V1_PREFIX)
app.include_router(usage_router, prefix=settings.API_V1_PREFIX)

# Public embed endpoints (no auth required)
app.include_router(embed_router, prefix=settings.API_V1_PREFIX)
app.include_router(embed_ws_router)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
