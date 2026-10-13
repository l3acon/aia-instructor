import hashlib
import hmac

from .config import settings


def generate_flag(challenge: str, player_name: str) -> str:
    """Generate a deterministic per-player flag using HMAC-SHA256.

    Produces a flag like: FLAG{a4f8c2e1b3d7}
    """
    msg = f"{challenge}:{player_name}".encode()
    digest = hmac.new(
        settings.hmac_secret.encode(),
        msg,
        hashlib.sha256,
    ).hexdigest()[:12]
    return f"FLAG{{{digest}}}"
