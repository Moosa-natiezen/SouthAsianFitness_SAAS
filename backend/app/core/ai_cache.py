"""In-memory response cache for AI meal plan generation.

Serves structurally identical generation requests from cache for a short
window instead of re-calling the LLM. The cache key is a normalized hash of
everything that materially changes the output:

- calorie target, protein target (macro split)
- cuisine type, dietary preferences, allergies
- a *coarse* prompt fingerprint (system prompt + user-prompt template
  structural version) so prompt updates invalidate old entries

Not in the key: per-user identity. Two users with identical requirements
get the same cached plan — the content is generic (no personal data beyond
the request parameters), which is exactly the cost win this module exists
for.

Degradation behavior ("variation" semantics): when a cached response is
reused beyond the *fresh* window but within the *variation* window, the
serving code appends a lightweight variation note rather than re-calling
the LLM. See ``AICache.fresh_window_seconds`` vs
``AICache.variation_window_seconds``.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from threading import Lock

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Bump when the system prompt or user-message structure changes materially
# enough that cached responses from the old prompt should not be reused.
_PROMPT_VERSION = "desi-mandate-v2"


@dataclass
class _CacheEntry:
    response: str
    created_at: float
    hit_count: int = 0
    served_as_variation: bool = False


@dataclass
class AICacheConfig:
    """Tunables (overridable via settings for ops without a deploy)."""

    # Within this window an identical request is served the cached plan as-is.
    fresh_window_seconds: int = 60 * 60  # 1 hour
    # Within this (longer) window a request is served the cached plan with a
    # variation note appended — still zero LLM tokens.
    variation_window_seconds: int = 60 * 60 * 6  # 6 hours
    # Bound memory: never keep more than this many distinct plans.
    max_entries: int = 256


class AICache:
    """Thread-safe TTL + LRU-bounded cache for completed AI responses."""

    def __init__(self, config: AICacheConfig | None = None) -> None:
        self._config = config or AICacheConfig()
        self._entries: dict[str, _CacheEntry] = {}
        self._lock = Lock()
        self._hits = 0
        self._misses = 0

    # ── Key construction ───────────────────────────────────────────────

    @staticmethod
    def build_key(
        *,
        target_calories: float | None,
        protein_g: float | None,
        cuisine_type: str | None,
        dietary_preferences: list[str] | None,
        allergies: list[str] | None,
        user_context: object | None = None,
    ) -> str:
        """Deterministic cache key from generation parameters.

        ``user_context`` participates as a *coarse* fingerprint (goals and
        preferences only) so personalization still varies the key without
        embedding volatile free-text into the hash.
        """
        normalized = {
            "v": _PROMPT_VERSION,
            "cal": round(target_calories) if target_calories is not None else None,
            "pro": round(protein_g) if protein_g is not None else None,
            "cui": (cuisine_type or "").strip().lower(),
            "pref": sorted(p.strip().lower() for p in (dietary_preferences or [])),
            "all": sorted(a.strip().lower() for a in (allergies or [])),
            "ctx": _context_fingerprint(user_context),
        }
        raw = json.dumps(normalized, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    # ── Lookup / store ─────────────────────────────────────────────────

    def get(self, key: str) -> tuple[str, bool] | None:
        """Return ``(response, served_as_variation)`` on a valid hit, else None.

        - Within the fresh window: the cached response as-is.
        - Within the variation window (but past fresh): response + variation
          marker so the caller can append a variation note.
        - Past the variation window: miss.
        """
        now = time.monotonic()
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None

            age = now - entry.created_at
            if age > self._config.variation_window_seconds:
                # Fully expired — drop it while we're here.
                self._entries.pop(key, None)
                self._misses += 1
                return None

            served_as_variation = age > self._config.fresh_window_seconds
            entry.hit_count += 1
            self._hits += 1
            return entry.response, served_as_variation

    def put(self, key: str, response: str) -> None:
        """Store a completed response, evicting the oldest entries if full."""
        now = time.monotonic()
        with self._lock:
            if key not in self._entries and len(self._entries) >= self._config.max_entries:
                # LRU-ish: evict the oldest insertion.
                oldest_key = min(self._entries, key=lambda k: self._entries[k].created_at)
                self._entries.pop(oldest_key, None)
            self._entries[key] = _CacheEntry(response=response, created_at=now)

    def clear(self, key: str | None = None) -> None:
        """Clear one key or the whole cache (tests, admin)."""
        with self._lock:
            if key is None:
                self._entries.clear()
            else:
                self._entries.pop(key, None)

    # ── Introspection (health endpoint / tests) ────────────────────────

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def size(self) -> int:
        return len(self._entries)

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                "entries": len(self._entries),
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate_pct": round(
                    (self._hits / (self._hits + self._misses)) * 100, 1
                )
                if (self._hits + self._misses)
                else 0.0,
            }


def _context_fingerprint(user_context: object | None) -> list[str] | None:
    """Coarse fingerprint of a UserAIContext for cache-key purposes.

    Deliberately structural (not free-text): goals/preferences/allergies.
    Uses duck typing so importing the context class here would create an
    import cycle (ai_context_service imports from this package level).
    """
    if user_context is None:
        return None
    goals = getattr(user_context, "goals", None)
    prefs = getattr(user_context, "preferences", None)
    allergies = getattr(user_context, "allergies", None)
    parts: list[str] = []
    if goals:
        parts.extend(str(g) for g in goals)
    if prefs:
        parts.extend(str(p) for p in prefs)
    if allergies:
        parts.extend(str(a) for a in allergies)
    return sorted(parts) if parts else None


def _read_config() -> AICacheConfig:
    """Build cache config from settings (env-overridable)."""
    return AICacheConfig(
        fresh_window_seconds=settings.ai_cache_fresh_window_seconds,
        variation_window_seconds=settings.ai_cache_variation_window_seconds,
        max_entries=settings.ai_cache_max_entries,
    )


# Process-wide singleton. Config is read lazily on first use through
# ``get_ai_cache()`` so test modules that reload settings still bind
# correctly.
_ai_cache: AICache | None = None


def get_ai_cache() -> AICache:
    global _ai_cache
    if _ai_cache is None:
        _ai_cache = AICache(_read_config())
    return _ai_cache


def reset_ai_cache() -> None:
    """Drop the singleton (tests)."""
    global _ai_cache
    _ai_cache = None
