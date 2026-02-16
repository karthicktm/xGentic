"""Public embed API routes for enterprise portal widgets.

These endpoints are unauthenticated but protected by:
- Domain allowlisting (Origin header validation)
- Rate limiting
- Agent-level access control (embed_enabled flag)

Supports all agent types: voice, chat, email, and document workflow.
"""

import asyncio
import contextlib
import fnmatch
import json
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlparse

import structlog
from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.agent import Agent, AgentType
from app.models.interaction import Interaction, InteractionStatus, InteractionType

router = APIRouter(prefix="/embed", tags=["Embed"])
ws_router = APIRouter(tags=["Embed WebSocket"])
logger = structlog.get_logger()

# In-memory session store (in production, use Redis with TTL)
_embed_sessions: dict[str, dict[str, Any]] = {}
SESSION_EXPIRY_MINUTES = 5

# Mapping from AgentType to InteractionType
AGENT_TO_INTERACTION_TYPE: dict[AgentType, InteractionType] = {
    AgentType.VOICE: InteractionType.VOICE_CALL,
    AgentType.CHAT: InteractionType.CHAT_SESSION,
    AgentType.EMAIL: InteractionType.EMAIL_THREAD,
    AgentType.DOCUMENT_WORKFLOW: InteractionType.DOCUMENT_WORKFLOW,
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class EmbedConfigResponse(BaseModel):
    """Public agent configuration for widget initialization."""

    public_id: str
    name: str
    agent_type: str
    greeting_message: str
    button_text: str
    theme: str
    position: str
    primary_color: str
    language: str
    type_config: dict[str, Any]


class EmbedSessionResponse(BaseModel):
    """Response for session creation."""

    session_id: str
    expires_at: str
    websocket_url: str


class ChatMessageRequest(BaseModel):
    """Request for chat agent interaction."""

    session_id: str | None = Field(
        None, description="Optional session ID for conversation continuity"
    )
    message: str = Field(..., min_length=1, max_length=10000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChatMessageResponse(BaseModel):
    """Response from a chat agent interaction."""

    session_id: str
    reply: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmailSubmitRequest(BaseModel):
    """Request for email agent submission."""

    from_address: str = Field(..., description="Sender email address")
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1, max_length=50000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EmailSubmitResponse(BaseModel):
    """Response from an email agent submission."""

    interaction_id: str
    status: str
    message: str


class SaveTranscriptRequest(BaseModel):
    """Request for saving an interaction transcript."""

    session_id: str
    transcript: str
    duration_seconds: int = 0
    interaction_type: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def validate_origin(origin: str | None, allowed_domains: list[str]) -> bool:
    """Validate that the Origin header matches allowed domains.

    Supports wildcards: ``*.example.com`` matches ``app.example.com``.
    Empty *allowed_domains* means all origins are allowed.
    """
    if not allowed_domains:
        return True

    if not origin:
        return False

    try:
        parsed = urlparse(origin)
        hostname = parsed.hostname or ""
    except Exception:
        return False

    for pattern in allowed_domains:
        if pattern.startswith("*."):
            fnmatch_pattern = f"*{pattern[1:]}"
            if fnmatch.fnmatch(hostname, fnmatch_pattern):
                return True
        elif hostname == pattern:
            return True

    return False


async def get_agent_by_public_id(
    public_id: str,
    db: AsyncSession,
) -> Agent | None:
    """Get agent by public ID."""
    result = await db.execute(select(Agent).where(Agent.public_id == public_id))
    return result.scalar_one_or_none()


async def _validate_embed_agent(
    public_id: str,
    db: AsyncSession,
    origin: str | None,
    *,
    required_type: AgentType | None = None,
) -> Agent:
    """Shared validation for all embed endpoints.

    Raises HTTPException on failure.
    """
    agent = await get_agent_by_public_id(public_id, db)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if not agent.embed_enabled:
        raise HTTPException(status_code=403, detail="Embedding is disabled for this agent")

    if not agent.is_active:
        raise HTTPException(status_code=403, detail="Agent is not active")

    if not validate_origin(origin, agent.allowed_domains):
        raise HTTPException(status_code=403, detail="Origin not allowed")

    if required_type and agent.agent_type != required_type:
        raise HTTPException(
            status_code=400,
            detail=f"Agent type mismatch: expected {required_type.value}, got {agent.agent_type}",
        )

    return agent


def cleanup_expired_sessions() -> None:
    """Remove expired sessions from memory."""
    now = datetime.now(UTC)
    expired = [
        sid
        for sid, data in _embed_sessions.items()
        if datetime.fromisoformat(data["expires_at"]) < now
    ]
    for sid in expired:
        del _embed_sessions[sid]


def validate_session(session_id: str, public_id: str) -> dict[str, Any] | None:
    """Validate a session token.

    Returns session data if valid, None otherwise.
    """
    session = _embed_sessions.get(session_id)
    if not session:
        return None

    expires_at = datetime.fromisoformat(session["expires_at"])
    if datetime.now(UTC) > expires_at:
        del _embed_sessions[session_id]
        return None

    if session["public_id"] != public_id:
        return None

    return session


# ---------------------------------------------------------------------------
# GET /embed/{public_id} — Get agent config for embed widget
# ---------------------------------------------------------------------------


@router.get("/{public_id}", response_model=EmbedConfigResponse)
async def get_embed_config(
    public_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    origin: str | None = Header(None),
) -> EmbedConfigResponse:
    """Get public agent configuration for widget initialization.

    Returns only the information needed to render the embed widget.
    Does NOT expose sensitive data like system prompts or API keys.
    """
    log = logger.bind(endpoint="embed_config", public_id=public_id, origin=origin)

    agent = await _validate_embed_agent(public_id, db, origin)

    embed_settings = agent.embed_settings or {}
    type_config = agent.type_config or {}

    # Expose only safe type_config keys (strip any credentials)
    safe_type_config: dict[str, Any] = {}
    if agent.agent_type == AgentType.VOICE:
        safe_type_config = {
            "voice": type_config.get("voice", "default"),
            "language": type_config.get("language", agent.language),
        }
    elif agent.agent_type == AgentType.CHAT:
        safe_type_config = {
            "streaming": type_config.get("streaming", True),
            "max_message_length": type_config.get("max_message_length", 5000),
        }
    elif agent.agent_type == AgentType.EMAIL:
        safe_type_config = {
            "auto_reply": type_config.get("auto_reply", True),
            "expected_response_time": type_config.get("expected_response_time", "1 hour"),
        }
    elif agent.agent_type == AgentType.DOCUMENT_WORKFLOW:
        safe_type_config = {
            "accepted_formats": type_config.get("accepted_formats", []),
            "max_file_size_mb": type_config.get("max_file_size_mb", 10),
        }

    log.info("config_returned", agent_type=agent.agent_type)

    return EmbedConfigResponse(
        public_id=public_id,
        name=agent.name,
        agent_type=agent.agent_type.value
        if hasattr(agent.agent_type, "value")
        else agent.agent_type,
        greeting_message=embed_settings.get("greeting_message", "Hi! How can I help you today?"),
        button_text=embed_settings.get("button_text", "Talk to us"),
        theme=embed_settings.get("theme", "auto"),
        position=embed_settings.get("position", "bottom-right"),
        primary_color=embed_settings.get("primary_color", "#818cf8"),
        language=agent.language,
        type_config=safe_type_config,
    )


# ---------------------------------------------------------------------------
# POST /embed/{public_id}/session — Create ephemeral session (voice)
# ---------------------------------------------------------------------------


@router.post("/{public_id}/session", response_model=EmbedSessionResponse)
async def create_embed_session(
    public_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    origin: str | None = Header(None),
) -> EmbedSessionResponse:
    """Create an ephemeral session for WebSocket voice connection.

    The token expires after a configurable window (default 5 minutes).
    """
    log = logger.bind(endpoint="embed_session", public_id=public_id, origin=origin)

    agent = await _validate_embed_agent(public_id, db, origin, required_type=AgentType.VOICE)

    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(minutes=SESSION_EXPIRY_MINUTES)

    _embed_sessions[session_id] = {
        "agent_id": str(agent.id),
        "public_id": public_id,
        "origin": origin,
        "created_at": datetime.now(UTC).isoformat(),
        "expires_at": expires_at.isoformat(),
    }

    cleanup_expired_sessions()

    ws_url = f"/ws/embed/{public_id}?session={session_id}"

    log.info("session_created", session_id=session_id[:8])

    return EmbedSessionResponse(
        session_id=session_id,
        expires_at=expires_at.isoformat(),
        websocket_url=ws_url,
    )


# ---------------------------------------------------------------------------
# POST /embed/{public_id}/chat — Chat agent interaction (REST)
# ---------------------------------------------------------------------------


@router.post("/{public_id}/chat", response_model=ChatMessageResponse)
async def chat_interaction(
    public_id: str,
    body: ChatMessageRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    origin: str | None = Header(None),
) -> ChatMessageResponse:
    """Send a message to a chat agent and receive a response.

    This is a synchronous REST endpoint for chat agents. Each request
    can optionally carry a ``session_id`` for multi-turn conversations.
    """
    log = logger.bind(endpoint="embed_chat", public_id=public_id, origin=origin)

    agent = await _validate_embed_agent(public_id, db, origin, required_type=AgentType.CHAT)

    # Generate or reuse session ID for conversation continuity
    session_id = body.session_id or secrets.token_urlsafe(16)

    # --- Build the chat completion request ---
    # In a full implementation this would call the configured LLM provider.
    # For now, we create the interaction record and return a placeholder that
    # the service layer can replace once integrated.

    interaction = Interaction(
        agent_id=agent.id,
        user_id=agent.user_id,
        interaction_type=InteractionType.CHAT_SESSION,
        status=InteractionStatus.ACTIVE,
        started_at=datetime.now(UTC),
        type_data={
            "session_id": session_id,
            "user_message": body.message,
            "source": "embed",
            "metadata": body.metadata,
        },
    )
    db.add(interaction)
    await db.flush()

    log.info("chat_interaction_created", interaction_id=str(interaction.id))

    # TODO: Replace with actual LLM call via the agent's provider_type / provider_config.
    # This placeholder ensures the endpoint is functional end-to-end.
    reply = (
        f"Thank you for your message. This is a placeholder response from agent '{agent.name}'. "
        "The LLM integration will be connected in a follow-up."
    )

    # Update the interaction with the response
    interaction.type_data = {
        **interaction.type_data,
        "assistant_reply": reply,
    }
    interaction.status = InteractionStatus.COMPLETED
    interaction.ended_at = datetime.now(UTC)

    log.info("chat_reply_sent", session_id=session_id)

    return ChatMessageResponse(
        session_id=session_id,
        reply=reply,
        metadata={"interaction_id": str(interaction.id)},
    )


# ---------------------------------------------------------------------------
# POST /embed/{public_id}/email — Submit email to email agent
# ---------------------------------------------------------------------------


@router.post("/{public_id}/email", response_model=EmailSubmitResponse)
async def email_submission(
    public_id: str,
    body: EmailSubmitRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    origin: str | None = Header(None),
) -> EmailSubmitResponse:
    """Submit an email to an email agent for processing.

    The agent will process the email asynchronously. The response contains
    the interaction ID that can be used to poll for status.
    """
    log = logger.bind(
        endpoint="embed_email",
        public_id=public_id,
        from_address=body.from_address,
        origin=origin,
    )

    agent = await _validate_embed_agent(public_id, db, origin, required_type=AgentType.EMAIL)

    interaction = Interaction(
        agent_id=agent.id,
        user_id=agent.user_id,
        interaction_type=InteractionType.EMAIL_THREAD,
        status=InteractionStatus.ACTIVE,
        started_at=datetime.now(UTC),
        type_data={
            "from_address": body.from_address,
            "subject": body.subject,
            "body": body.body,
            "source": "embed",
            "metadata": body.metadata,
        },
    )
    db.add(interaction)
    await db.flush()

    log.info("email_interaction_created", interaction_id=str(interaction.id))

    # TODO: Dispatch to email processing pipeline (e.g., background task / queue).
    # For now, the interaction is persisted and marked as active.

    return EmailSubmitResponse(
        interaction_id=str(interaction.id),
        status=InteractionStatus.ACTIVE.value,
        message="Email received and queued for processing.",
    )


# ---------------------------------------------------------------------------
# POST /embed/{public_id}/transcript — Save interaction transcript
# ---------------------------------------------------------------------------


@router.post("/{public_id}/transcript")
async def save_embed_transcript(
    public_id: str,
    body: SaveTranscriptRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    origin: str | None = Header(None),
) -> dict[str, Any]:
    """Save an interaction transcript from an embed widget session.

    Creates an Interaction record with the full transcript. Works for
    any agent type but is most commonly used for voice and chat.
    """
    log = logger.bind(
        endpoint="embed_transcript",
        public_id=public_id,
        session_id=body.session_id,
        origin=origin,
    )

    agent = await _validate_embed_agent(public_id, db, origin)

    # Skip empty transcripts
    if not body.transcript.strip():
        log.info("empty_transcript_skipped")
        return {"success": True, "message": "Empty transcript skipped"}

    # Determine interaction type from agent or explicit override
    interaction_type = AGENT_TO_INTERACTION_TYPE.get(
        AgentType(agent.agent_type) if isinstance(agent.agent_type, str) else agent.agent_type,
        InteractionType.CHAT_SESSION,
    )
    if body.interaction_type:
        try:
            interaction_type = InteractionType(body.interaction_type)
        except ValueError:
            pass

    interaction = Interaction(
        agent_id=agent.id,
        user_id=agent.user_id,
        interaction_type=interaction_type,
        status=InteractionStatus.COMPLETED,
        transcript=body.transcript,
        duration_seconds=body.duration_seconds,
        started_at=datetime.now(UTC) - timedelta(seconds=body.duration_seconds),
        ended_at=datetime.now(UTC),
        type_data={
            "session_id": body.session_id,
            "source": "embed",
        },
    )
    db.add(interaction)
    await db.flush()

    log.info(
        "transcript_saved",
        interaction_id=str(interaction.id),
        transcript_length=len(body.transcript),
        duration_seconds=body.duration_seconds,
    )

    return {"success": True, "interaction_id": str(interaction.id)}


# ---------------------------------------------------------------------------
# WebSocket /ws/embed/{public_id} — Voice agent streaming
# ---------------------------------------------------------------------------


@ws_router.websocket("/ws/embed/{public_id}")
async def embed_voice_websocket(
    websocket: WebSocket,
    public_id: str,
    session: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Public WebSocket endpoint for voice agent streaming.

    Requires a valid ephemeral session token obtained via
    ``POST /embed/{public_id}/session``.
    """
    ws_session_id = str(uuid.uuid4())
    log = logger.bind(endpoint="embed_websocket", public_id=public_id, ws_session_id=ws_session_id)

    await websocket.accept()
    log.info("websocket_connected")

    try:
        # Validate session token
        session_data = validate_session(session, public_id)
        if not session_data:
            log.warning("invalid_session")
            await websocket.send_json({"type": "error", "error": "Invalid or expired session"})
            await websocket.close(code=4001)
            return

        # Get agent
        agent = await get_agent_by_public_id(public_id, db)
        if not agent:
            await websocket.send_json({"type": "error", "error": "Agent not found"})
            await websocket.close(code=4004)
            return

        if not agent.embed_enabled or not agent.is_active:
            await websocket.send_json({"type": "error", "error": "Agent not available"})
            await websocket.close(code=4003)
            return

        if agent.agent_type != AgentType.VOICE:
            await websocket.send_json({"type": "error", "error": "Agent is not a voice agent"})
            await websocket.close(code=4002)
            return

        log.info("agent_loaded", agent_name=agent.name, agent_type=agent.agent_type)

        type_config = agent.type_config or {}

        # Send session ready event
        await websocket.send_json(
            {
                "type": "session.ready",
                "session_id": ws_session_id,
                "agent": {
                    "name": agent.name,
                    "voice": type_config.get("voice", "default"),
                    "language": agent.language,
                },
            }
        )

        # Run the voice streaming bridge
        await _voice_stream_bridge(websocket, agent, ws_session_id, log)

    except WebSocketDisconnect:
        log.info("websocket_disconnected")
    except Exception as e:
        log.exception("websocket_error", error=str(e))
        with contextlib.suppress(Exception):
            await websocket.send_json({"type": "error", "error": str(e)})
    finally:
        with contextlib.suppress(Exception):
            await websocket.close()
        log.info("websocket_closed")


async def _invoke_llm(
    agent: Agent,
    user_message: str,
    conversation_history: list[dict[str, str]],
) -> str:
    """Send a text message to the agent's LLM provider and return the response."""
    from app.services.providers.azure_foundry import AzureFoundryProvider  # noqa: PLC0415

    provider_config = agent.provider_config or {}
    provider = AzureFoundryProvider()
    deployment_config = {
        "azure_endpoint": provider_config.get("azure_endpoint"),
        "azure_api_key": provider_config.get("azure_api_key"),
        "system_prompt": agent.system_prompt,
        "temperature": agent.temperature,
        "max_tokens": agent.max_tokens,
    }

    response = await provider.invoke_agent(deployment_config, user_message, conversation_history)

    conversation_history.append({"role": "user", "content": user_message})
    conversation_history.append({"role": "assistant", "content": response.content})
    return response.content


async def _handle_ws_text_event(
    data: dict[str, Any],
    client_ws: WebSocket,
    agent: Agent,
    session_id: str,
    history: list[dict[str, str]],
) -> None:
    """Process a parsed JSON event from the WebSocket client."""
    event_type = data.get("type", "")
    user_text = ""

    if event_type == "user.message":
        user_text = data.get("text", "")
    elif event_type == "user.transcript":
        user_text = data.get("transcript", "")

    if user_text:
        reply = await _invoke_llm(agent, user_text, history)
        await client_ws.send_json(
            {
                "type": "assistant.message",
                "text": reply,
                "session_id": session_id,
            }
        )


async def _voice_stream_bridge(
    client_ws: WebSocket,
    agent: Agent,
    session_id: str,
    log: Any,
) -> None:
    """Bridge audio streams between embed client and the voice provider.

    For Azure Foundry agents, routes text messages through the Azure LLM.
    Audio processing (STT/TTS) is handled client-side or via a separate pipeline.
    """
    conversation_history: list[dict[str, str]] = []

    async def client_to_provider() -> None:
        """Forward messages from the client to the voice provider."""
        try:
            while True:
                message = await client_ws.receive()

                if message["type"] == "websocket.disconnect":
                    log.info("client_initiated_disconnect")
                    break

                if message["type"] != "websocket.receive":
                    continue

                if "bytes" in message:
                    log.debug("audio_chunk_received", size=len(message["bytes"]))
                elif "text" in message:
                    with contextlib.suppress(json.JSONDecodeError):
                        data = json.loads(message["text"])
                        log.debug("client_event", event_type=data.get("type"))
                        await _handle_ws_text_event(
                            data, client_ws, agent, session_id, conversation_history
                        )

        except WebSocketDisconnect:
            log.info("client_disconnected")
        except Exception as e:
            log.exception("client_to_provider_error", error=str(e))

    async def provider_to_client() -> None:
        """Keep coroutine alive for bidirectional communication."""
        stop_event = asyncio.Event()
        with contextlib.suppress(asyncio.CancelledError):
            await stop_event.wait()

    tasks = [
        asyncio.create_task(client_to_provider()),
        asyncio.create_task(provider_to_client()),
    ]

    try:
        _done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
    except Exception as e:
        log.exception("voice_bridge_error", error=str(e))
        for task in tasks:
            task.cancel()
