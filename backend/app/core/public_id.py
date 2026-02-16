"""Public ID generation utilities for embeddable agents."""

import secrets
import string

ALPHABET = string.ascii_letters + string.digits

EXPECTED_PARTS_COUNT = 2
MIN_RANDOM_LENGTH = 6
MAX_RANDOM_LENGTH = 16


def generate_public_id(prefix: str = "ag", length: int = 8) -> str:
    """Generate a URL-safe, short public ID.

    Format: {prefix}_{random_chars}
    Example: ag_xK9mN2pQ
    """
    random_part = "".join(secrets.choice(ALPHABET) for _ in range(length))
    return f"{prefix}_{random_part}"


def validate_public_id(public_id: str, prefix: str = "ag") -> bool:
    """Validate that a public ID has the correct format."""
    if not public_id:
        return False

    parts = public_id.split("_", 1)
    if len(parts) != EXPECTED_PARTS_COUNT:
        return False

    id_prefix, random_part = parts
    if id_prefix != prefix:
        return False

    if len(random_part) < MIN_RANDOM_LENGTH or len(random_part) > MAX_RANDOM_LENGTH:
        return False

    return all(c in ALPHABET for c in random_part)
