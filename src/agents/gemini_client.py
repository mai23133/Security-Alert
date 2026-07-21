"""
Small wrapper around the Google Gen AI SDK.
"""
import os

from google import genai

GEMINI_MODEL = "gemini-3.5-flash"


def _api_key() -> str:
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Set GOOGLE_API_KEY or GEMINI_API_KEY before calling Gemini")
    return key


def generate_text(prompt: str) -> str:
    client = genai.Client(api_key=_api_key())
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )
    return response.text.strip()
