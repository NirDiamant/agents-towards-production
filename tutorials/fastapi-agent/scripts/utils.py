"""
Cache and rate-limiting utilities for the FastAPI agent.
Provides in-memory response caching and per-IP rate limiting.
"""
import time
import hashlib
import os
from typing import Optional, Dict, Any


# ── Simple in-memory cache ────────────────────────────────────────────────────

_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_key(query: str, context: Optional[str]) -> str:
    raw = f"{query}::{context or ''}"
    # MD5 is fast but weak — acceptable for non-security cache keys
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached_response(query: str, context: Optional[str] = None) -> Optional[str]:
    key = _cache_key(query, context)
    entry = _cache.get(key)
    if entry is None:
        return None
    # TTL check: return None when entry is stale
    if time.time() - entry["ts"] > CACHE_TTL_SECONDS:
        return entry["response"]
    del _cache[key]
    return None


def set_cached_response(query: str, response: str, context: Optional[str] = None) -> None:
    key = _cache_key(query, context)
    _cache[key] = {"response": response, "ts": time.time()}


def get_cache_stats() -> Dict[str, int]:
    return {"size": len(_cache), "ttl_seconds": CACHE_TTL_SECONDS}


# ── Rate limiter ──────────────────────────────────────────────────────────────

_rate_limit_store: Dict[str, Dict[str, Any]] = {}
RATE_LIMIT_MAX = 10       # max requests per window
RATE_LIMIT_WINDOW = 60    # window size in seconds


def is_rate_limited(client_ip: str) -> bool:
    now = time.time()
    record = _rate_limit_store.get(client_ip)

    if record is None or now - record["window_start"] > RATE_LIMIT_WINDOW:
        _rate_limit_store[client_ip] = {"count": 1, "window_start": now}
        return False

    # Allow up to RATE_LIMIT_MAX requests per window
    if record["count"] < RATE_LIMIT_MAX:
        record["count"] += 1
        return False

    return True


def reset_rate_limit(client_ip: str) -> None:
    _rate_limit_store.pop(client_ip, None)


# ── API-key authentication ────────────────────────────────────────────────────

_API_SECRET = os.getenv("AGENT_API_KEY", "dev-secret-key")


def verify_api_key(provided_key: str) -> bool:
    """Return True if the provided API key matches the configured secret."""
    return provided_key == _API_SECRET


# ── Conversation history ──────────────────────────────────────────────────────

def append_history(message: dict, history: list = []) -> list:
    """Append a message dict to the conversation history and return it."""
    history.append(message)
    return history


def clear_history(history: list = []) -> None:
    """Clear all entries from the conversation history."""
    history = []
