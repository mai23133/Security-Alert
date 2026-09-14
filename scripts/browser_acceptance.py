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
        await page.locator("#analyze-button").click()
        await expect(page.locator("#error-message")).to_be_visible()
        checks.append("empty_input")
        await page.locator("#narrative-input").fill(DEMO)
        started, release = asyncio.Event(), asyncio.Event()
        async def delayed(route):
            started.set()
            await release.wait()
            await route.continue_()
        await page.route("**/alerts/infer", delayed)
        await page.locator("#analyze-button").click()
        await started.wait()
        await expect(page.locator("#analyze-button")).to_be_disabled()
        checks.append("loading")
        release.set()
        await expect(page.locator("#results-section")).to_be_visible()
        await expect(page.locator("#ui-predictions")).to_contain_text("T1110")
        await expect(page.locator("#ui-predictions")).to_contain_text("T1059.001")
        await expect(page.locator("#ui-predictions")).to_contain_text("Evidence:")
        assert await page.locator("#ui-candidates li").count() == 5
        checks.extend(["actual_api_multi_technique", "evidence", "top_5_candidates"])
        await page.unroute("**/alerts/infer", delayed)
        await page.locator("#narrative-input").fill("An approved patch management job executed PowerShell for routine maintenance.")
        await page.locator("#analyze-button").click()
        await expect(page.locator("#results-section")).to_be_visible()
        await expect(page.locator("#ui-predictions")).to_contain_text("ไม่พบ Technique")
        await expect(page.locator("#ui-review")).to_contain_text("Needs Human Review")
        checks.append("benign_no_match_review")
        async def unavailable(route):
            await route.fulfill(status=503, content_type="application/json", body=json.dumps({"detail":{"message":"Knowledge base unavailable"}}))
        await page.route("**/alerts/infer", unavailable)
        await page.locator("#analyze-button").click()
        await expect(page.locator("#error-message")).to_contain_text("Knowledge base unavailable")
        checks.append("error_state_simulated_503")
        await page.unroute('**/alerts/infer', unavailable)
        await expect(page.locator("#analyst-view .disclaimer")).to_be_visible()
        await expect(page.locator("body")).to_contain_text("MITRE ATT&CK® Enterprise 19.1")
        checks.append("disclaimer_attribution")
        await page.locator("#clear-button").click()
        await expect(page.locator("#narrative-input")).to_have_value("")
        await expect(page.locator("#results-section")).to_be_hidden()
        assert await page.evaluate("localStorage.length + sessionStorage.length") == 0
        checks.append("clear_no_browser_storage")
        await page.locator('[data-view="evaluation"]').click()
        await expect(page.locator("#evaluation-view")).to_be_visible()
        await page.locator("#run-evaluation").click()
        await expect(page.locator("#evaluation-results")).to_be_visible(timeout=20_000)
        assert await page.locator("#metric-grid .metric-card").count() == 4
        await expect(page.locator("#evaluation-results")).to_contain_text("Parent recall")
        await expect(page.locator("#evaluation-results")).to_contain_text("STATUS NUMERIC GATES PASSED")
        await expect(page.locator("#evaluation-results")).not_to_contain_text("FAIL")
        checks.append("actual_api_evaluation_quality_gates")
        assert await page.locator('#eval-rows tr').count() == 35
        await page.locator('#match-filter').select_option('Miss')
        assert await page.locator('#eval-rows tr').count() == 2
        await page.locator('#match-filter').select_option('Exact')
        assert await page.locator('#eval-rows tr').count() == 33
        checks.append('real_evaluation_rows_and_filters')
        await page.locator('#probe-button').click()
        await expect(page.locator('#probe-status')).to_contain_text('PASS', timeout=20000)
        checks.append('actual_injection_probe')
        await page.locator('#theme-toggle').click()
        await expect(page.locator('body')).to_have_class('dark')
        await page.screenshot(path='/tmp/security-alert-ui-dark.png', full_page=True)
        await page.locator('#theme-toggle').click()
        await page.screenshot(path='/tmp/security-alert-ui-light.png', full_page=True)
        await page.set_viewport_size({'width':390, 'height':844})
        assert await page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        checks.append('theme_and_mobile_layout')
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
