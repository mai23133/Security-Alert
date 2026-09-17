"""Request-scoped selected provider with offline fallback."""
from __future__ import annotations

from collections.abc import Callable
import os
import httpx
from urllib.error import URLError

from src.agents import gemini_client, openrouter_client


TextGenerator = Callable[[str], str]


def _reason(exc: Exception) -> str:
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 429:
        return "rate-limited"
    if code in {408, 504} or isinstance(exc, (TimeoutError, httpx.TimeoutException)):
        return "timeout"
    if isinstance(exc, (URLError, httpx.NetworkError)):
        return "network-error"
    if code in {500, 502, 503}:
        return "temporary-error"
    if code in {400, 401, 403, 404}:
        return "configuration-error"
    if isinstance(exc, RuntimeError) and "API_KEY" in str(exc):
        return "missing-key"
    if isinstance(exc, RuntimeError) and "explicit consent" in str(exc):
        return "consent-required"
    return "provider-error"


class ProviderChain:
    """Use one circuit breaker across parser, router, and judge calls."""

    def __init__(self, *, provider: str = "gemini", gemini_generate: TextGenerator | None = None,
                 openrouter_generate: TextGenerator | None = None):
        if provider not in {"gemini", "openrouter"}:
            raise ValueError("Unknown provider")
        self.provider = provider
        self._gemini_generate = gemini_generate or gemini_client.generate_text
        self._openrouter_generate = openrouter_generate or openrouter_client.generate_text
        self._disabled_reason: str | None = None

    def generate_text(self, prompt: str, *, trace: dict | None = None) -> str:
        fallback_reason = self._disabled_reason
        if fallback_reason is None:
            try:
                generate = self._gemini_generate if self.provider == "gemini" else self._openrouter_generate
                result = generate(prompt)
                if trace is not None:
                    trace.update(provider=self.provider, model=(gemini_client.GEMINI_MODEL
                                 if self.provider == "gemini" else os.getenv("OPENROUTER_MODEL", openrouter_client.OPENROUTER_MODEL)),
                                 fallback_used=False, fallback_reason="none")
                return result
            except Exception as exc:
                fallback_reason = _reason(exc)
                self._disabled_reason = fallback_reason
        if trace is not None:
            trace.update(provider="offline", model="none", fallback_used=True,
                         fallback_reason=fallback_reason)
        raise RuntimeError("Selected provider unavailable") from None


def generate_text(prompt: str) -> str:
    """Compatibility entry point for standalone agent calls."""
    return ProviderChain().generate_text(prompt)
