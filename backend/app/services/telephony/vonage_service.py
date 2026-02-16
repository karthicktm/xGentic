"""Vonage telephony provider implementation."""

import asyncio
import logging
from typing import Any

import vonage

from app.core.config import settings
from app.services.telephony.base import CallResult, PhoneNumberInfo, TelephonyProvider

logger = logging.getLogger(__name__)


class VonageTelephonyService(TelephonyProvider):
    """Vonage implementation of the telephony provider interface.

    Uses the Vonage Voice API with NCCO (Nexmo Call Control Objects) for call
    flow control and the Vonage Numbers API for phone number management.
    """

    def __init__(self) -> None:
        """Initialize the Vonage client with credentials from settings."""
        self.application_id = settings.VONAGE_APPLICATION_ID or ""
        self.private_key = settings.VONAGE_PRIVATE_KEY or ""
        self.api_key = settings.VONAGE_API_KEY or ""
        self.api_secret = settings.VONAGE_API_SECRET or ""

        self.client = vonage.Client(
            application_id=self.application_id,
            private_key=self.private_key,
        )
        self.voice = vonage.Voice(self.client)

        # Numbers API uses api_key/api_secret authentication
        self.numbers_client = vonage.Client(
            key=self.api_key,
            secret=self.api_secret,
        )
        self.numbers = vonage.Numbers(self.numbers_client)

    async def initiate_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs: Any,
    ) -> CallResult:
        """Initiate an outbound call via the Vonage Voice API with NCCO.

        The NCCO (Nexmo Call Control Object) defines the call flow. By default
        a ``connect`` action is used that forwards the call to the provided
        webhook URL for further instructions.

        Args:
            to_number: Destination phone number (E.164 format).
            from_number: Source phone number (E.164 format).
            webhook_url: Event/answer URL for the call.
            **kwargs: Optional keys: ``ncco`` (list of NCCO actions to
                override the default connect action), ``event_url``.

        Returns:
            CallResult with the Vonage call UUID.
        """
        logger.info(
            "Initiating Vonage call to=%s from=%s webhook=%s",
            to_number,
            from_number,
            webhook_url,
        )

        try:
            # Strip leading '+' for Vonage number format
            to_clean = to_number.lstrip("+")
            from_clean = from_number.lstrip("+")

            ncco = kwargs.get("ncco") or [
                {
                    "action": "connect",
                    "endpoint": [
                        {
                            "type": "phone",
                            "number": to_clean,
                        }
                    ],
                }
            ]

            event_url = kwargs.get("event_url", webhook_url)

            payload: dict[str, Any] = {
                "to": [{"type": "phone", "number": to_clean}],
                "from": {"type": "phone", "number": from_clean},
                "ncco": ncco,
                "event_url": [event_url],
            }

            response = await asyncio.to_thread(
                self.voice.create_call,
                payload,
            )

            call_uuid = response.get("uuid", "")
            status = response.get("status", "unknown")

            logger.info(
                "Vonage call initiated uuid=%s status=%s",
                call_uuid,
                status,
            )

            return CallResult(
                call_id=call_uuid,
                status=status,
                details={
                    "conversation_uuid": response.get("conversation_uuid"),
                    "direction": response.get("direction"),
                },
            )
        except Exception:
            logger.exception("Vonage call initiation failed")
            raise

    async def end_call(self, call_id: str) -> bool:
        """End an active Vonage call.

        Args:
            call_id: Vonage call UUID.

        Returns:
            True if the call was successfully ended.
        """
        logger.info("Ending Vonage call uuid=%s", call_id)

        try:
            await asyncio.to_thread(
                self.voice.update_call,
                call_id,
                {"action": "hangup"},
            )
            logger.info("Vonage call ended uuid=%s", call_id)
            return True
        except Exception:
            logger.exception("Failed to end Vonage call uuid=%s", call_id)
            return False

    async def transfer_call(self, call_id: str, to_number: str) -> CallResult:
        """Transfer an active Vonage call using an NCCO transfer action.

        Sends an NCCO ``transfer`` action that connects the existing call leg
        to a new phone number endpoint.

        Args:
            call_id: Vonage call UUID.
            to_number: Destination phone number (E.164 format).

        Returns:
            CallResult with the updated call information.
        """
        logger.info(
            "Transferring Vonage call uuid=%s to=%s",
            call_id,
            to_number,
        )

        try:
            to_clean = to_number.lstrip("+")

            transfer_ncco: dict[str, Any] = {
                "action": "transfer",
                "destination": {
                    "type": "ncco",
                    "ncco": [
                        {
                            "action": "connect",
                            "endpoint": [
                                {
                                    "type": "phone",
                                    "number": to_clean,
                                }
                            ],
                        }
                    ],
                },
            }

            await asyncio.to_thread(
                self.voice.update_call,
                call_id,
                transfer_ncco,
            )

            logger.info("Vonage call transferred uuid=%s", call_id)

            return CallResult(
                call_id=call_id,
                status="transferred",
                details={"transferred_to": to_number},
            )
        except Exception:
            logger.exception(
                "Failed to transfer Vonage call uuid=%s", call_id
            )
            raise

    async def list_phone_numbers(self) -> list[PhoneNumberInfo]:
        """List all phone numbers on the Vonage account via the Numbers API.

        Returns:
            List of PhoneNumberInfo objects.
        """
        logger.info("Listing Vonage phone numbers")

        try:
            response = await asyncio.to_thread(
                self.numbers.list_owned,
            )

            numbers_data = response.get("numbers", [])
            numbers: list[PhoneNumberInfo] = []

            for number in numbers_data:
                features = number.get("features", [])
                capabilities: list[str] = []
                if "VOICE" in features:
                    capabilities.append("voice")
                if "SMS" in features:
                    capabilities.append("sms")
                if "MMS" in features:
                    capabilities.append("mms")

                country = number.get("country", "")
                msisdn = number.get("msisdn", "")

                numbers.append(
                    PhoneNumberInfo(
                        id=f"{country}-{msisdn}",
                        number=f"+{msisdn}",
                        provider="vonage",
                        capabilities=capabilities,
                    )
                )

            logger.info("Listed %d Vonage phone numbers", len(numbers))
            return numbers
        except Exception:
            logger.exception("Failed to list Vonage phone numbers")
            raise

    async def get_recording(self, call_id: str) -> dict[str, Any]:
        """Retrieve recording information for a Vonage call.

        Vonage stores recordings that can be fetched by the recording URL
        received via webhooks. This method retrieves call details which may
        contain recording references.

        Args:
            call_id: Vonage call UUID.

        Returns:
            Dictionary with recording URL and metadata.
        """
        logger.info("Getting Vonage recording uuid=%s", call_id)

        try:
            call_details = await asyncio.to_thread(
                self.voice.get_call,
                call_id,
            )

            recording_url = call_details.get("recording_url", "")
            duration = call_details.get("duration", 0)
            status = call_details.get("status", "")

            result: dict[str, Any] = {
                "call_id": call_id,
                "status": status,
                "duration": duration,
                "download_url": recording_url,
                "conversation_uuid": call_details.get("conversation_uuid", ""),
            }

            # If a recording URL is present, attempt to fetch the binary content
            # reference; callers can use the URL to download directly.
            if recording_url:
                logger.info(
                    "Vonage recording available uuid=%s url=%s",
                    call_id,
                    recording_url,
                )
            else:
                logger.warning(
                    "No recording URL found for Vonage call uuid=%s", call_id
                )

            return result
        except Exception:
            logger.exception(
                "Failed to get Vonage recording uuid=%s", call_id
            )
            raise
