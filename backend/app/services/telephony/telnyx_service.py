"""Telnyx telephony provider implementation."""

import logging
from typing import Any

import httpx
import telnyx

from app.core.config import settings
from app.services.telephony.base import CallResult, PhoneNumberInfo, TelephonyProvider

logger = logging.getLogger(__name__)


class TelnyxTelephonyService(TelephonyProvider):
    """Telnyx implementation of the telephony provider interface."""

    def __init__(self) -> None:
        """Initialize the Telnyx client with credentials from settings."""
        self.api_key = settings.TELNYX_API_KEY or ""
        telnyx.api_key = self.api_key  # type: ignore[attr-defined]
        self._http_client: httpx.AsyncClient | None = None

    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create a reusable async HTTP client for the Telnyx REST API."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                base_url="https://api.telnyx.com/v2",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=settings.TELNYX_TIMEOUT,
            )
        return self._http_client

    async def initiate_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs: Any,
    ) -> CallResult:
        """Initiate an outbound call via the Telnyx Call Control API.

        Args:
            to_number: Destination phone number (E.164 format).
            from_number: Source phone number (E.164 format).
            webhook_url: URL for call event webhooks.
            **kwargs: Optional keys: ``connection_id``.

        Returns:
            CallResult with the Telnyx call control ID.
        """
        logger.info(
            "Initiating Telnyx call to=%s from=%s webhook=%s",
            to_number,
            from_number,
            webhook_url,
        )

        try:
            client = await self._get_http_client()
            connection_id = kwargs.get("connection_id") or await self._get_connection_id()

            payload: dict[str, Any] = {
                "to": to_number,
                "from": from_number,
                "connection_id": connection_id,
                "webhook_url": webhook_url,
            }

            response = await client.post("/calls", json=payload)
            response.raise_for_status()
            data = response.json()

            call_data = data.get("data", {})
            call_control_id = call_data.get("call_control_id", "")

            logger.info("Telnyx call initiated call_control_id=%s", call_control_id)

            return CallResult(
                call_id=call_control_id,
                status="initiated",
                details={
                    "call_leg_id": call_data.get("call_leg_id"),
                    "call_session_id": call_data.get("call_session_id"),
                },
            )
        except httpx.HTTPStatusError as e:
            logger.error(
                "Telnyx call initiation failed status=%s body=%s",
                e.response.status_code,
                e.response.text,
            )
            raise
        except Exception:
            logger.exception("Telnyx call initiation failed")
            raise

    async def end_call(self, call_id: str) -> bool:
        """End an active Telnyx call.

        Args:
            call_id: Telnyx call control ID.

        Returns:
            True if the hangup request succeeded.
        """
        logger.info("Ending Telnyx call call_control_id=%s", call_id)

        try:
            client = await self._get_http_client()
            response = await client.post(
                f"/calls/{call_id}/actions/hangup",
                json={},
            )
            response.raise_for_status()
            logger.info("Telnyx call ended call_control_id=%s", call_id)
            return True
        except Exception:
            logger.exception("Failed to end Telnyx call call_control_id=%s", call_id)
            return False

    async def transfer_call(self, call_id: str, to_number: str) -> CallResult:
        """Transfer an active Telnyx call to another number.

        Args:
            call_id: Telnyx call control ID.
            to_number: Destination phone number (E.164 format).

        Returns:
            CallResult with updated call information.
        """
        logger.info(
            "Transferring Telnyx call call_control_id=%s to=%s",
            call_id,
            to_number,
        )

        try:
            client = await self._get_http_client()
            response = await client.post(
                f"/calls/{call_id}/actions/transfer",
                json={"to": to_number},
            )
            response.raise_for_status()
            data = response.json()

            logger.info("Telnyx call transferred call_control_id=%s", call_id)

            return CallResult(
                call_id=call_id,
                status="transferred",
                details=data.get("data"),
            )
        except Exception:
            logger.exception(
                "Failed to transfer Telnyx call call_control_id=%s", call_id
            )
            raise

    async def list_phone_numbers(self) -> list[PhoneNumberInfo]:
        """List all phone numbers on the Telnyx account.

        Returns:
            List of PhoneNumberInfo objects.
        """
        logger.info("Listing Telnyx phone numbers")

        try:
            client = await self._get_http_client()
            response = await client.get("/phone_numbers")
            response.raise_for_status()
            data = response.json()

            numbers: list[PhoneNumberInfo] = []
            for number in data.get("data", []):
                capabilities = ["voice"]
                if number.get("messaging_profile_id"):
                    capabilities.append("sms")

                numbers.append(
                    PhoneNumberInfo(
                        id=number.get("id", ""),
                        number=number.get("phone_number", ""),
                        provider="telnyx",
                        capabilities=capabilities,
                    )
                )

            logger.info("Listed %d Telnyx phone numbers", len(numbers))
            return numbers
        except Exception:
            logger.exception("Failed to list Telnyx phone numbers")
            raise

    async def get_recording(self, call_id: str) -> dict[str, Any]:
        """Retrieve recording information for a Telnyx call.

        Args:
            call_id: Telnyx call control ID.

        Returns:
            Dictionary with recording URL and metadata.
        """
        logger.info("Getting Telnyx recording call_control_id=%s", call_id)

        try:
            client = await self._get_http_client()
            response = await client.get(
                "/recordings",
                params={"filter[call_control_id]": call_id},
            )
            response.raise_for_status()
            data = response.json()

            recordings = data.get("data", [])
            if not recordings:
                logger.warning(
                    "No recordings found for Telnyx call call_control_id=%s", call_id
                )
                return {"call_id": call_id, "recordings": []}

            recording = recordings[0]
            return {
                "call_id": call_id,
                "recording_id": recording.get("id", ""),
                "status": recording.get("status", ""),
                "channels": recording.get("channels", ""),
                "duration_millis": recording.get("duration_millis", 0),
                "download_url": recording.get("download_urls", {}).get("mp3", ""),
                "created_at": recording.get("created_at", ""),
                "recordings": recordings,
            }
        except Exception:
            logger.exception(
                "Failed to get Telnyx recording call_control_id=%s", call_id
            )
            raise

    async def _get_connection_id(self) -> str:
        """Get the first available credential connection ID.

        Returns:
            Connection ID string.

        Raises:
            RuntimeError: If no connections exist and creation fails.
        """
        client = await self._get_http_client()
        response = await client.get("/credential_connections")
        response.raise_for_status()
        data = response.json()

        connections = data.get("data", [])
        if connections:
            return str(connections[0].get("id", ""))

        # Create a new connection if none exists
        response = await client.post(
            "/credential_connections",
            json={
                "connection_name": "xgentic-voice-connection",
                "active": True,
            },
        )
        response.raise_for_status()
        new_data = response.json()
        return str(new_data.get("data", {}).get("id", ""))

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
