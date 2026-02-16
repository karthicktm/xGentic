"""Twilio telephony provider implementation."""

import asyncio
import logging
from typing import Any

from twilio.rest import Client

from app.core.config import settings
from app.services.telephony.base import CallResult, PhoneNumberInfo, TelephonyProvider

logger = logging.getLogger(__name__)


class TwilioTelephonyService(TelephonyProvider):
    """Twilio implementation of the telephony provider interface."""

    def __init__(self) -> None:
        """Initialize the Twilio client with credentials from settings."""
        self.account_sid = settings.TWILIO_ACCOUNT_SID or ""
        self.auth_token = settings.TWILIO_AUTH_TOKEN or ""
        self.client = Client(self.account_sid, self.auth_token)

    async def initiate_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs: Any,
    ) -> CallResult:
        """Initiate an outbound call via the Twilio REST API.

        Args:
            to_number: Destination phone number (E.164 format).
            from_number: Source phone number (E.164 format).
            webhook_url: URL for TwiML instructions when the call connects.
            **kwargs: Optional keys: ``status_callback``, ``record``.

        Returns:
            CallResult with the Twilio Call SID.
        """
        logger.info(
            "Initiating Twilio call to=%s from=%s webhook=%s",
            to_number,
            from_number,
            webhook_url,
        )

        try:
            status_callback = kwargs.get(
                "status_callback",
                webhook_url.replace("/answer", "/status"),
            )
            record = kwargs.get("record", False)

            call = await asyncio.to_thread(
                self.client.calls.create,
                to=to_number,
                from_=from_number,
                url=webhook_url,
                status_callback=status_callback,
                status_callback_event=["initiated", "ringing", "answered", "completed"],
                status_callback_method="POST",
                record=record,
            )

            logger.info("Twilio call initiated call_sid=%s", call.sid)

            return CallResult(
                call_id=call.sid,
                status="initiated",
                details={
                    "account_sid": call.account_sid,
                    "direction": call.direction,
                },
            )
        except Exception:
            logger.exception("Twilio call initiation failed")
            raise

    async def end_call(self, call_id: str) -> bool:
        """End an active Twilio call.

        Args:
            call_id: Twilio Call SID.

        Returns:
            True if the call was successfully ended.
        """
        logger.info("Ending Twilio call call_sid=%s", call_id)

        try:
            await asyncio.to_thread(
                self.client.calls(call_id).update,
                status="completed",
            )
            logger.info("Twilio call ended call_sid=%s", call_id)
            return True
        except Exception:
            logger.exception("Failed to end Twilio call call_sid=%s", call_id)
            return False

    async def transfer_call(self, call_id: str, to_number: str) -> CallResult:
        """Transfer an active Twilio call to another number.

        Uses TwiML <Dial> to redirect the in-progress call to a new number.

        Args:
            call_id: Twilio Call SID.
            to_number: Destination phone number (E.164 format).

        Returns:
            CallResult with the updated call information.
        """
        logger.info(
            "Transferring Twilio call call_sid=%s to=%s",
            call_id,
            to_number,
        )

        try:
            # Update the call with TwiML that dials the transfer target
            twiml = f'<Response><Dial>{to_number}</Dial></Response>'

            await asyncio.to_thread(
                self.client.calls(call_id).update,
                twiml=twiml,
            )

            logger.info("Twilio call transferred call_sid=%s", call_id)

            return CallResult(
                call_id=call_id,
                status="transferred",
                details={"transferred_to": to_number},
            )
        except Exception:
            logger.exception(
                "Failed to transfer Twilio call call_sid=%s", call_id
            )
            raise

    async def list_phone_numbers(self) -> list[PhoneNumberInfo]:
        """List all phone numbers on the Twilio account.

        Returns:
            List of PhoneNumberInfo objects.
        """
        logger.info("Listing Twilio phone numbers")

        try:
            raw_numbers = await asyncio.to_thread(
                self.client.incoming_phone_numbers.list,
            )

            numbers: list[PhoneNumberInfo] = []
            for number in raw_numbers:
                capabilities_dict = number.capabilities or {}
                caps: list[str] = []
                if capabilities_dict.get("voice"):
                    caps.append("voice")
                if capabilities_dict.get("sms"):
                    caps.append("sms")
                if capabilities_dict.get("mms"):
                    caps.append("mms")

                numbers.append(
                    PhoneNumberInfo(
                        id=number.sid,
                        number=number.phone_number,
                        provider="twilio",
                        capabilities=caps,
                    )
                )

            logger.info("Listed %d Twilio phone numbers", len(numbers))
            return numbers
        except Exception:
            logger.exception("Failed to list Twilio phone numbers")
            raise

    async def get_recording(self, call_id: str) -> dict[str, Any]:
        """Retrieve recording information for a Twilio call.

        Args:
            call_id: Twilio Call SID.

        Returns:
            Dictionary with recording URL and metadata.
        """
        logger.info("Getting Twilio recording call_sid=%s", call_id)

        try:
            recordings = await asyncio.to_thread(
                self.client.recordings.list,
                call_sid=call_id,
            )

            if not recordings:
                logger.warning(
                    "No recordings found for Twilio call call_sid=%s", call_id
                )
                return {"call_id": call_id, "recordings": []}

            recording = recordings[0]
            recording_url = (
                f"https://api.twilio.com/2010-04-01/Accounts/"
                f"{self.account_sid}/Recordings/{recording.sid}.mp3"
            )

            return {
                "call_id": call_id,
                "recording_sid": recording.sid,
                "status": recording.status,
                "duration": recording.duration,
                "download_url": recording_url,
                "date_created": str(recording.date_created) if recording.date_created else "",
                "recordings": [
                    {
                        "sid": r.sid,
                        "duration": r.duration,
                        "status": r.status,
                    }
                    for r in recordings
                ],
            }
        except Exception:
            logger.exception(
                "Failed to get Twilio recording call_sid=%s", call_id
            )
            raise
