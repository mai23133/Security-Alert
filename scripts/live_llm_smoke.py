"""Run one real Gemini-backed sample and validate the public Pydantic contract."""
from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

from src.agents.gemini_client import generate_text
from src.inference_pipeline import run_inference
from src.rag.retriever import BaselineRetriever
from src.schemas import ATTACKInferenceResult


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE = (
    "Host WIN-SRV-04 logged 847 failed RDP authentication attempts, followed "
    "by a successful login and execution of encoded PowerShell."
)


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    successful_calls = 0

    def tracked_generate(prompt: str) -> str:
        nonlocal successful_calls
        response = generate_text(prompt)
        successful_calls += 1
        return response

    retriever = BaselineRetriever(
        PROJECT_ROOT / "data/processed/technique_candidates.json",
        PROJECT_ROOT / "data/processed/technique_ids.json",
    )
    result = run_inference(
        alert_id="live-smoke-001",
        narrative=SAMPLE,
        retriever=retriever,
        use_provider=True,
        provider_generate=tracked_generate,
    )
    if successful_calls != 3:
        raise RuntimeError(
            f"expected 3 successful Gemini calls, observed {successful_calls}"
        )
    checked = ATTACKInferenceResult.model_validate(result)
    print(json.dumps(checked.model_dump(), indent=2))


if __name__ == "__main__":
    main()
