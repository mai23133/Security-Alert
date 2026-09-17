// Run after npm run build. Requires Playwright and an installed Edge browser.
// Starts an isolated backend with provider keys disabled; never uses live LLMs.
const assert = require('node:assert/strict');
const { spawn } = require('node:child_process');
const { once } = require('node:events');
const net = require('node:net');
const path = require('node:path');
const { mkdir } = require('node:fs/promises');
const { chromium } = require('playwright');

const root = path.resolve(__dirname, '../..');
const python = process.env.UI_TEST_PYTHON || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

(async () => {
  const socket = net.createServer().listen(0, '127.0.0.1');
  await once(socket, 'listening');
  const port = socket.address().port;
  await new Promise(resolve => socket.close(resolve));
  const base = `http://127.0.0.1:${port}`;
  const server = spawn(python, ['-m', 'uvicorn', 'src.api.main:app', '--host', '127.0.0.1', '--port', String(port)], {
    cwd: root, windowsHide: true, stdio: ['ignore', 'ignore', 'pipe'],
    env: { ...process.env, GOOGLE_API_KEY: '', GEMINI_API_KEY: '' },
  });
  let diagnostics = '';
  server.stderr.on('data', chunk => { diagnostics = (diagnostics + chunk).slice(-4000); });
  let browser;
  try {
    let ready = false;
    for (let i = 0; i < 100; i++) {
      if (server.exitCode !== null) throw new Error(`Backend exited: ${diagnostics}`);
      try { ready = (await fetch(base)).ok; } catch { /* wait for startup */ }
      if (ready) break;
      await delay(100);
    }
    assert(ready, `Backend did not start: ${diagnostics}`);
    browser = await chromium.launch({ channel: process.env.UI_TEST_BROWSER || 'msedge', headless: true });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    page.setDefaultTimeout(15000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${base}/ui`);

    // Existing analyst workflow still uses actual responses, then clears stale data.
    await page.getByRole('button', { name: /Brute-Force/ }).click();
    const inferenceResponse = page.waitForResponse(r => r.url().endsWith('/alerts/infer'));
    await page.getByRole('button', { name: /Infer ATT&CK Techniques/ }).click();
    const inference = await (await inferenceResponse).json();
    assert(Array.isArray(inference.inferred_techniques));
    for (const technique of inference.inferred_techniques) {
      await page.getByText(technique.technique_id, { exact: true }).first().waitFor();
    }
    await page.locator('textarea').fill('New narrative with no previous result');
    assert.equal(await page.getByText('NEEDS HUMAN REVIEW: TRUE', { exact: true }).count(), 0);

    await page.getByRole('button', { name: 'Eval & Guardrails' }).click();
    assert.equal(await page.getByText('NOT RUN', { exact: true }).count(), 4);
    assert.equal(await page.getByText('NOT MEASURED', { exact: true }).count(), 4);
    const pending = page.waitForResponse(r => r.url().endsWith('/evaluate'));
    await page.getByRole('button', { name: /Run Full Evaluation/ }).click();
    const response = await pending;
    assert.equal(response.status(), 200);
    assert.deepEqual(response.request().postDataJSON(), { mode: 'runtime', top_k: 5 });
    const report = await response.json();
    await page.getByRole('status').waitFor();
    const expected = [
      ['EXACT TECHNIQUE F1', report.metrics.exact_technique.f1],
      ['PARENT TECHNIQUE RECALL', report.metrics.parent_technique_recall],
      ['EVIDENCE GROUNDING RATE', report.metrics.evidence_grounding_rate],
      ['HALLUCINATED ID RATE', report.metrics.hallucinated_id_rate],
    ];
    for (const [label, rate] of expected) {
      const card = page.getByText(label, { exact: true }).locator('..');
      await card.getByText(String(Number((rate * 100).toFixed(1))), { exact: true }).waitFor();
    }
    for (const row of report.case_results) {
      const rendered = await page.getByText(row.alert_id, { exact: true }).locator('..').innerText();
      assert(rendered.includes(row.gold_technique_ids.join(', ') || 'NONE'));
      assert(rendered.includes(row.predicted_technique_ids.join(', ') || 'NONE'));
      assert(rendered.includes(row.match.toUpperCase()));
      if (row.grounded === null) assert(rendered.includes('N/A (no prediction)'));
    }
    for (const filter of ['Exact', 'Parent', 'Miss']) {
      await page.getByRole('button', { name: filter, exact: true }).click();
      for (const row of report.case_results) {
        assert.equal(await page.getByText(row.alert_id, { exact: true }).count(), row.match === filter ? 1 : 0);
      }
    }
    await page.getByRole('button', { name: 'All', exact: true }).click();
    const output = path.join(root, '.pytest_cache');
    await mkdir(output, { recursive: true });
    await page.screenshot({ path: path.join(output, 'evaluation-ui.png'), fullPage: true });

    // An API failure replaces the previous result and allows retry.
    await page.route('**/evaluate', route => route.fulfill({ status: 503, contentType: 'application/json', headers: { 'X-Request-ID': 'ui-error-check' }, body: JSON.stringify({ detail: { message: 'Evaluation unavailable' } }) }));
    await page.getByRole('button', { name: /Run Full Evaluation/ }).click();
    await page.getByRole('alert').getByText(/ui-error-check/).waitFor();
    assert.equal(await page.getByText('NOT RUN', { exact: true }).count(), 4);
    assert.equal(await page.getByText(report.case_results[0].alert_id, { exact: true }).count(), 0);
    await page.unroute('**/evaluate');

    // Malformed success responses must not render fabricated/partial reports.
    await page.route('**/evaluate', route => route.fulfill({ status: 200, contentType: 'application/json', body: '{}' }));
    await page.getByRole('button', { name: /Run Full Evaluation/ }).click();
    await page.getByRole('alert').getByText(/รายงานไม่ครบ/).waitFor();
    await page.unroute('**/evaluate');

    // Timeout and tab-unmount cancellation, with browser time advanced instead of a long wait.
    await page.clock.install();
    await page.route('**/evaluate', () => {});
    await page.getByRole('button', { name: /Run Full Evaluation/ }).click();
    await page.clock.fastForward(120001);
    await page.getByRole('alert').getByText(/หมดเวลา/).waitFor();
    await page.getByRole('button', { name: /Run Full Evaluation/ }).click();
    await page.getByRole('button', { name: 'Analyst Workspace' }).click();
    await page.getByRole('button', { name: 'Eval & Guardrails' }).click();
    assert.equal(await page.getByText('NOT RUN', { exact: true }).count(), 4);
    assert.equal(await page.getByRole('alert').count(), 0);
    await page.unrouteAll({ behavior: 'ignoreErrors' });
    assert.deepEqual(errors, []);
    console.log(JSON.stringify({ browser: 'PASS', cases: report.case_results.length, metrics: report.metrics, checks: ['inference', 'live evaluation', 'filters', 'API error', 'malformed JSON shape', 'timeout', 'unmount cancellation'], screenshot: path.join(output, 'evaluation-ui.png') }, null, 2));
  } finally {
    if (browser) await browser.close();
    server.kill();
    if (server.exitCode === null) await once(server, 'exit');
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
