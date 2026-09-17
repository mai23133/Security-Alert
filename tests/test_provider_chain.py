import pytest

from src.agents.provider_chain import ProviderChain


def error(code):
    return type("ProviderFailure", (RuntimeError,), {"code": code})("failed")


def test_chain_uses_gemini_when_available():
    trace = {}
    chain = ProviderChain(gemini_generate=lambda _prompt: "gemini-result",
                          openrouter_generate=lambda _prompt: pytest.fail("fallback called"))

    assert chain.generate_text("prompt", trace=trace) == "gemini-result"
    assert trace["provider"] == "gemini"
    assert trace["fallback_used"] is False


def test_chain_falls_back_offline_and_never_calls_other_provider():
    calls = {"gemini": 0, "openrouter": 0}
    def gemini(_prompt):
        calls["gemini"] += 1
        raise error(429)
    def openrouter(_prompt):
        calls["openrouter"] += 1
        return "openrouter-result"
    chain = ProviderChain(gemini_generate=gemini, openrouter_generate=openrouter)
    first_trace, second_trace = {}, {}

    with pytest.raises(RuntimeError):
        chain.generate_text("one", trace=first_trace)
    with pytest.raises(RuntimeError):
        chain.generate_text("two", trace=second_trace)

    assert calls == {"gemini": 1, "openrouter": 0}
    assert first_trace["provider"] == "offline"
    assert first_trace["fallback_reason"] == "rate-limited"
    assert second_trace["provider"] == "offline"


def test_chain_preserves_selected_provider_failure():
    trace = {}
    chain = ProviderChain(
        gemini_generate=lambda _prompt: (_ for _ in ()).throw(error(503)),
        openrouter_generate=lambda _prompt: (_ for _ in ()).throw(error(429)),
    )

    with pytest.raises(RuntimeError, match="provider unavailable"):
        chain.generate_text("prompt", trace=trace)

    assert trace == {
        "provider": "offline", "model": "none", "fallback_used": True,
        "fallback_reason": "temporary-error",
    }


def test_openrouter_selection_does_not_call_gemini():
    trace = {}
    chain = ProviderChain(provider="openrouter",
                          gemini_generate=lambda _: pytest.fail("Gemini called"),
                          openrouter_generate=lambda _: "result")
    assert chain.generate_text("prompt", trace=trace) == "result"
    assert trace["provider"] == "openrouter"
    assert not trace["fallback_used"]
