"""Webhook signature validation for telephony providers."""

import hashlib
import hmac
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


def validate_telnyx_signature(
    payload: bytes,
    signature: str,
    timestamp: str,
) -> bool:
    """Validate Telnyx webhook signature."""
    if not settings.TELNYX_PUBLIC_KEY:
        logger.warning("Telnyx public key not configured")
        return False

    try:
        # Telnyx uses Ed25519 signatures
        from telnyx.util import verify_webhook_signature

        verify_webhook_signature(payload.decode(), signature, timestamp)
        return True
    except Exception:
        logger.exception("Telnyx signature validation failed")
        return False


def verify_twilio_webhook(
    url: str,
    params: dict[str, Any],
    signature: str,
) -> bool:
    """Verify Twilio webhook request signature."""
    if not settings.TWILIO_AUTH_TOKEN:
        logger.warning("Twilio auth token not configured")
        return False

    try:
        from twilio.request_validator import RequestValidator

        # Use PUBLIC_URL if behind a reverse proxy
        if settings.PUBLIC_URL:
            url = url.replace("http://localhost:8000", settings.PUBLIC_URL)

        validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
        return validator.validate(url, params, signature)
    except Exception:
        logger.exception("Twilio signature validation failed")
        return False


def verify_vonage_webhook(
    payload: bytes,
    signature: str,
) -> bool:
    """Verify Vonage webhook request signature."""
    if not settings.VONAGE_API_SECRET:
        logger.warning("Vonage API secret not configured")
        return False

    try:
        expected = hmac.new(
            settings.VONAGE_API_SECRET.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        logger.exception("Vonage signature validation failed")
        return False
