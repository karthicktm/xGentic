"""Abstract telephony provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class CallResult:
    """Result from initiating or transferring a call."""

    call_id: str
    status: str
    details: dict[str, Any] | None = None


@dataclass
class PhoneNumberInfo:
    """Information about a phone number."""

    id: str
    number: str
    provider: str
    capabilities: list[str] | None = None


class TelephonyProvider(ABC):
    """Abstract base class for telephony providers."""

    @abstractmethod
    async def initiate_call(
        self,
        to_number: str,
        from_number: str,
        webhook_url: str,
        **kwargs: Any,
    ) -> CallResult:
        """Initiate an outbound call.

        Args:
            to_number: Destination phone number (E.164 format).
            from_number: Source phone number (E.164 format).
            webhook_url: URL for call status/instruction callbacks.
            **kwargs: Provider-specific options.

        Returns:
            CallResult with call identifier and status.
        """
        ...

    @abstractmethod
    async def end_call(self, call_id: str) -> bool:
        """End an active call.

        Args:
            call_id: Provider-specific call identifier.

        Returns:
            True if the call was successfully ended.
        """
        ...

    @abstractmethod
    async def transfer_call(self, call_id: str, to_number: str) -> CallResult:
        """Transfer an active call to another number.

        Args:
            call_id: Provider-specific call identifier.
            to_number: Destination phone number (E.164 format).

        Returns:
            CallResult with updated call information.
        """
        ...

    @abstractmethod
    async def list_phone_numbers(self) -> list[PhoneNumberInfo]:
        """List all phone numbers associated with the account.

        Returns:
            List of PhoneNumberInfo objects.
        """
        ...

    @abstractmethod
    async def get_recording(self, call_id: str) -> dict[str, Any]:
        """Retrieve recording information for a call.

        Args:
            call_id: Provider-specific call identifier.

        Returns:
            Dictionary with recording details (url, duration, etc.).
        """
        ...
