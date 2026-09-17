"""Minimal OpenRouter client for the independently selected demo provider."""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.agents.provider_safety import redact_prompt, require_provider_consent


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/free")
OPENROUTER_TIMEOUT_SECONDS = 15


class OpenRouterError(RuntimeError):
    def __init__(self, code: int | None):
        super().__init__("OpenRouter request failed")
        self.code = code


def _api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Set OPENROUTER_API_KEY before calling OpenRouter")
    return key


def generate_text(prompt: str) -> str:
    """Generate bounded JSON-oriented text without exposing provider errors."""
    require_provider_consent()
    body = json.dumps({
        "model": os.getenv("OPENROUTER_MODEL", OPENROUTER_MODEL),
        "messages": [{"role": "user", "content": redact_prompt(prompt)}],
        "temperature": 0,
        "max_tokens": 1200,
        # Router asks for an array, parser/judge for objects. Let each prompt
        # specify its JSON shape; all responses are validated by the agent.
        "provider": {"data_collection": "deny"},
    }).encode("utf-8")
    request = Request(
        OPENROUTER_URL,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost/security-alert-demo",
            "X-Title": "Security Alert ATT&CK Demo",
        },
    )
    try:
        with urlopen(request, timeout=OPENROUTER_TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        if not isinstance(text, str) or not text.strip():
            raise OpenRouterError(None)
        return text.strip()
    except HTTPError as exc:
        raise OpenRouterError(exc.code) from None
    except (URLError, TimeoutError):
        raise
    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
        raise OpenRouterError(None) from None
