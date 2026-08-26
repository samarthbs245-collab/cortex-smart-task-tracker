from slowapi import Limiter
from slowapi.util import get_remote_address


# ============================================================
# CORTEX RATE LIMITER
# ============================================================

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)