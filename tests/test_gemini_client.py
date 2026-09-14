import pytest

from src.agents import gemini_client


def test_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY"):
        gemini_client._client()


def test_client_configures_timeout_and_retries(monkeypatch):
    captured = {}

    def fake_client(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setattr(gemini_client.genai, "Client", fake_client)

    gemini_client._client()

    options = captured["http_options"]
    assert options.timeout == gemini_client.GEMINI_TIMEOUT_MS
    assert options.retry_options.attempts == gemini_client.GEMINI_RETRY_ATTEMPTS
    assert 429 in options.retry_options.http_status_codes


def test_provider_requires_consent_even_with_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.delenv("PROVIDER_CONSENT", raising=False)
    monkeypatch.setattr(gemini_client, "_client", lambda: pytest.fail("provider called"))
    with pytest.raises(RuntimeError, match="consent"):
        gemini_client.generate_text("synthetic alert")


def test_opt_in_redacts_sensitive_fields_and_closes_client(monkeypatch):
    from types import SimpleNamespace
    captured = {}
    def generate(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(text="result")
    fake = SimpleNamespace(models=SimpleNamespace(generate_content=generate), close=lambda: captured.update(closed=True))
    monkeypatch.setenv("PROVIDER_CONSENT", "reviewed-synthetic-only")
    monkeypatch.setattr(gemini_client, "_client", lambda: fake)
    assert gemini_client.generate_text("203.0.113.9 user@example.test token=secretvalue") == "result"
    assert all(secret not in captured["contents"] for secret in ("203.0.113.9", "user@example.test", "secretvalue"))
    assert captured["closed"] is True
