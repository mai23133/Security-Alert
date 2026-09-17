"""Run actual Chromium/API acceptance locally; use synthetic alerts only."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

from playwright.async_api import async_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
DEMO = "Host WIN-SRV-04 logged 847 failed RDP authentication attempts from IP 203.0.113.44 between 02:00–04:00 UTC, followed by a successful login and execution of encoded PowerShell."


async def check(url):
    checks = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url + "/ui")
        narrative = page.locator("#narrative-input")
        analyze = page.locator("#analyze-button")
        await expect(page.get_by_role("button", name="Offline / Rules")).to_be_visible()
        await expect(page.get_by_role("button", name="Gemini 3.5 Flash-Lite")).to_be_visible()
        await expect(page.get_by_role("button", name="OpenRouter", exact=True)).to_be_visible()
        await expect(analyze).to_be_disabled()
        checks.append("mode_selector_and_empty_input_guard")
        await narrative.fill(DEMO)
        started, release = asyncio.Event(), asyncio.Event()
        async def delayed(route):
            started.set()
            await release.wait()
            await route.continue_()
        await page.route("**/alerts/infer", delayed)
        await analyze.click()
        await started.wait()
        await expect(analyze).to_be_disabled()
        checks.append("loading")
        release.set()
        await expect(page.get_by_text("T1110", exact=True)).to_be_visible(timeout=20_000)
        await expect(page.get_by_text("T1059.001", exact=True)).to_be_visible()
        await expect(page.get_by_text("Parser: not-used · offline", exact=True)).to_be_visible()
        await expect(page.get_by_text("Fallback: NO", exact=True)).to_be_visible()
        await expect(page.get_by_text("RULE SUPPORT SCORE", exact=True).first).to_be_visible()
        await expect(page.get_by_text("ไม่ใช่เปอร์เซ็นต์โอกาสที่คำตอบถูก", exact=False).first).to_be_visible()
        await page.get_by_role("button", name="View Candidates Considered").click()
        await expect(page.get_by_text("CANDIDATE RETRIEVAL — 5 CONSIDERED", exact=False)).to_be_visible()
        checks.extend(["actual_api_multi_technique", "evidence", "top_5_candidates", "offline_provider_status"])
        await page.unroute("**/alerts/infer", delayed)
        await narrative.fill("An approved patch management job executed PowerShell for routine maintenance.")
        await analyze.click()
        await expect(page.get_by_text("No techniques with sufficient evidence inferred", exact=False)).to_be_visible(timeout=20_000)
        await expect(page.get_by_text("NEEDS HUMAN REVIEW: TRUE", exact=True)).to_be_visible()
        checks.append("benign_no_match_review")
        await page.get_by_role("button", name="💉 Prompt Injection").click()
        await analyze.click()
        await expect(page.get_by_text("PROMPT INJECTION BLOCKED", exact=True)).to_be_visible(timeout=20_000)
        await expect(page.get_by_text("No techniques with sufficient evidence inferred", exact=False)).to_be_visible()
        await expect(page.get_by_text("NEEDS HUMAN REVIEW: TRUE", exact=True)).to_be_visible()
        await expect(page.get_by_text("T9999", exact=True)).to_have_count(0)
        checks.append("prompt_injection_fail_closed_before_provider")
        await page.get_by_role("button", name="Gemini 3.5 Flash-Lite").click()
        await narrative.fill("WIN-01 executed encoded PowerShell commands.")
        await analyze.click()
        await expect(page.get_by_text("Fallback: YES", exact=True)).to_be_visible(timeout=20_000)
        checks.append("gemini_safe_fallback_without_key")
        await expect(page.get_by_text("หมายเหตุ: LLM Judge ใช้งานไม่ได้", exact=False)).to_be_visible()
        await expect(page.get_by_text("ยังไม่ได้เปิดอนุญาตส่งข้อมูลจำลอง", exact=False).first).to_be_visible()
        await expect(page.get_by_text("หมายเหตุ: LLM Inferencer ใช้งานไม่ได้", exact=False)).to_be_visible()
        checks.append("judge_offline_reason_visible")
        await page.get_by_role("button", name="OpenRouter", exact=True).click()
        await analyze.click()
        await expect(page.get_by_text("หมายเหตุ: LLM Judge ใช้งานไม่ได้", exact=False)).to_be_visible(timeout=20_000)
        checks.append("openrouter_independent_mode_safe_fallback")
        # Rendering contract only: real provider execution is covered by mocked
        # pipeline/API tests. Never consume remote quota in browser acceptance.
        async def llm_response(route):
            assert route.request.post_data_json["inference_mode"] == "openrouter"
            await route.fulfill(json={
                "alert_id": "mock-llm", "inferred_techniques": [{
                    "technique_id": "T1059.001", "technique_name": "PowerShell",
                    "tactic": "execution", "confidence": 0.93,
                    "evidence_spans": ["WIN-01 executed encoded PowerShell commands."],
                    "mitre_url": "https://attack.mitre.org/techniques/T1059/001/"}],
                "candidates_considered": [], "needs_human_review": False,
                "disclaimer": "Advisory tagging only. Verify with senior analyst."},
                headers={"X-AI-Inferencer-Status": "success", "X-AI-Inferencer-Provider": "openrouter",
                         "X-AI-Inferencer-Model": "mock-model", "X-AI-Judge-Status": "success",
                         "X-AI-Confidence-Source": "llm-self-assessed", "X-AI-Fallback-Used": "false"})
        await page.route("**/alerts/infer", llm_response)
        await analyze.click()
        await expect(page.get_by_text("LLM SUPPORT SCORE", exact=True)).to_be_visible()
        await expect(page.get_by_text("93/100", exact=True)).to_be_visible()
        await expect(page.get_by_text("Inferencer: success · openrouter · mock-model", exact=True)).to_be_visible()
        await expect(page.get_by_text("หมายเหตุ: LLM Inferencer ใช้งานไม่ได้", exact=False)).to_have_count(0)
        checks.append("mock_llm_score_source_and_inferencer_status")
        await page.unroute("**/alerts/infer", llm_response)
        await expect(page.get_by_text("Advisory tagging only", exact=False).first).to_be_visible()
        await expect(page.get_by_text("MITRE ATT&CK Enterprise v19.1", exact=True).first).to_be_visible()
        checks.append("disclaimer_attribution")
        await page.get_by_role("button", name="Clear").click()
        await expect(narrative).to_have_value("")
        assert await page.evaluate("localStorage.length + sessionStorage.length") == 0
        checks.append("clear_no_browser_storage")
        await page.get_by_role("button", name="Eval & Guardrails").click()
        await page.get_by_role("button", name="Run Full Evaluation").click()
        await expect(page.get_by_text("Evaluation complete", exact=False)).to_be_visible(timeout=120_000)
        await expect(page.get_by_text("EXACT TECHNIQUE F1", exact=True)).to_be_visible()
        await expect(page.get_by_text("PARENT TECHNIQUE RECALL", exact=True)).to_be_visible()
        checks.append("actual_api_evaluation_quality_gates")
        await page.screenshot(path='/tmp/security-alert-ui-dark.png', full_page=True)
        await page.locator('button[title="Toggle Light/Dark Theme"]').click()
        await page.screenshot(path='/tmp/security-alert-ui-light.png', full_page=True)
        checks.append('theme_screenshots')
        await browser.close()
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("/tmp/security-alert-browser-report.json"))
    args = parser.parse_args()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    env = {**os.environ, "GOOGLE_API_KEY":"", "GEMINI_API_KEY":"", "PROVIDER_CONSENT":"",
           "SECURITY_ALERT_API_KEY":"", "APP_ENV":"sandbox"}
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "src.api.main:app", "--host", "127.0.0.1", "--port", str(port), "--no-access-log"], cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            try:
                with urlopen(url + "/ready", timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Acceptance server did not become ready")
        checks = asyncio.run(check(url))
        report = {"passed": True, "checks": checks, "provider_mode":"disabled", "synthetic_data_only":True}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


if __name__ == "__main__":
    main()
