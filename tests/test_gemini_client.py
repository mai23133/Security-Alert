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
