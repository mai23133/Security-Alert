import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const uiRoot = fileURLToPath(new URL('../', import.meta.url));
const dist = path.join(uiRoot, 'dist');
let html = await readFile(path.join(dist, 'index.html'), 'utf8');
const scripts = [...html.matchAll(/<script\b[^>]*src="([^"]+)"[^>]*><\/script>/g)];
const styles = [...html.matchAll(/<link\b[^>]*rel="stylesheet"[^>]*href="([^"]+)"[^>]*>/g)];
if (scripts.length !== 1 || styles.length !== 1) {
  throw new Error('Expected one JavaScript bundle and one stylesheet. Review standalone packaging.');
}
async function readAsset(url) {
  return readFile(path.join(dist, 'assets', path.posix.basename(url)), 'utf8');
}
const js = await readAsset(scripts[0][1]);
const css = await readAsset(styles[0][1]);
html = html.replace(scripts[0][0], '');
html = html.replace(styles[0][0], () => `<style>${css.replace(/<\/style/gi, '<\\/style')}</style>`);
html = html.replace('</body>', () => `<script type="module">${js.replace(/<\/script/gi, '<\\/script')}</script>\n</body>`);
await writeFile(path.join(uiRoot, 'เปิดหน้า-UI.html'), html, 'utf8');
console.log('Created ui/เปิดหน้า-UI.html — open directly in a browser.');
