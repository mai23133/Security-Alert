"""
Small wrapper around the Google Gen AI SDK.
"""
import os
import re

from google import genai
from google.genai import types

GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_TIMEOUT_MS = 10_000
GEMINI_RETRY_ATTEMPTS = 3


def _api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY before calling Gemini")
    return key


def _client() -> genai.Client:
    return genai.Client(
        api_key=_api_key(),
        http_options=types.HttpOptions(
            timeout=GEMINI_TIMEOUT_MS,
            retry_options=types.HttpRetryOptions(
                attempts=GEMINI_RETRY_ATTEMPTS,
                initial_delay=0.25,
                max_delay=1.0,
                exp_base=2.0,
                jitter=0.1,
                http_status_codes=[408, 429, 500, 502, 503, 504],
            ),
        ),
    )


def generate_text(prompt: str) -> str:
    """Generate text with bounded SDK timeouts and transient-error retries."""
    if os.getenv("PROVIDER_CONSENT") != "reviewed-synthetic-only":
        raise RuntimeError("External provider disabled: explicit consent for reviewed synthetic data required")
    # Defense in depth for explicitly enabled, reviewed synthetic prompts.
    # Arbitrary secrets cannot be detected reliably; API remains offline.
    prompt = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP]", prompt)
    prompt = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", prompt)
    prompt = re.sub(r"(?i)(password|api[_-]?key|token|secret)\s*[=:]\s*[^\s,;]+", r"\1=[REDACTED]", prompt)
    client = _client()
    try:
        response = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        return response.text.strip()
    finally:
        client.close()
