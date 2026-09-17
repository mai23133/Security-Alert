import json

import pytest

from src.agents import openrouter_client


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self):
        return json.dumps({"choices": [{"message": {"content": '{"ok":true}'}}]}).encode()


def test_openrouter_requires_key_and_consent(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("PROVIDER_CONSENT", "reviewed-synthetic-only")
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        openrouter_client.generate_text("synthetic")


def test_openrouter_redacts_and_denies_data_collection(monkeypatch):
    captured = {}
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("PROVIDER_CONSENT", "reviewed-synthetic-only")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)

    def fake_urlopen(request, timeout):
        captured["body"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(openrouter_client, "urlopen", fake_urlopen)
    result = openrouter_client.generate_text(
        "203.0.113.9 user@example.test token=secretvalue"
    )

    content = captured["body"]["messages"][0]["content"]
    assert result == '{"ok":true}'
    assert all(value not in content for value in
               ("203.0.113.9", "user@example.test", "secretvalue"))
    assert captured["body"]["provider"] == {"data_collection": "deny"}
    assert captured["body"]["model"] == "openrouter/free"
    assert captured["timeout"] == openrouter_client.OPENROUTER_TIMEOUT_SECONDS
