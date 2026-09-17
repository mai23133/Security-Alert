"""Shared outbound-provider consent and prompt minimization controls."""
import os
import re


def require_provider_consent() -> None:
    if os.getenv("PROVIDER_CONSENT") != "reviewed-synthetic-only":
        raise RuntimeError(
            "External provider disabled: explicit consent for reviewed synthetic data required"
        )


def redact_prompt(prompt: str) -> str:
    prompt = re.sub(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", "[IP]", prompt)
    prompt = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[EMAIL]", prompt)
    return re.sub(
        r"(?i)(password|api[_-]?key|token|secret)\s*[=:]\s*[^\s,;]+",
        r"\1=[REDACTED]",
        prompt,
    )
