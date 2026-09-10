// Headless-Chromium E2E timing for the WEKO top page, item landing page and
// search-result list. Unlike the curl script this drives a real browser, so it
// includes JS execution and the AJAX calls that actually render the search list
// and page widgets ("perceived" load time until the network goes idle).
//
// Usage:
//   node measure_browser.mjs <label> [detailRecid] [iterations] [searchQuery]
//
// Env: BASE (default https://weko3.example.org:18443)
//      EMAIL / PASSWORD (default admin from docker-compose.arm64.yml)
//      OUTDIR (default ../results)
import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';

const label = process.argv[2] || 'run';
const detailRecid = process.argv[3] || '3000001';
const iterations = parseInt(process.argv[4] || '15', 10);
const BASE = process.env.BASE || 'https://weko3.example.org:18443';
const EMAIL = process.env.EMAIL || 'wekosoftware@nii.ac.jp';
const PASSWORD = process.env.PASSWORD || 'uspass123';
const OUTDIR = process.env.OUTDIR || new URL('../results', import.meta.url).pathname;

const urls = {
  top: `${BASE}/`,
  detail: `${BASE}/records/${detailRecid}`,
  search: `${BASE}/search?search_type=0&q=`,
};

function stats(a) {
  a = a.slice().sort((x, y) => x - y);
  const n = a.length;
  if (!n) return { min: NaN, med: NaN, mean: NaN, p90: NaN, max: NaN, n: 0 };
  const med = n % 2 ? a[(n - 1) / 2] : (a[n / 2 - 1] + a[n / 2]) / 2;
  const p90 = a[Math.min(n - 1, Math.ceil(n * 0.9) - 1)];
  const mean = a.reduce((s, x) => s + x, 0) / n;
  return { min: a[0], med, mean, p90, max: a[n - 1], n };
}
const f = (x) => (Number.isFinite(x) ? (x / 1000).toFixed(3) : 'NA');

const browser = await chromium.launch({
  args: [
    '--host-resolver-rules=MAP weko3.example.org 127.0.0.1',
    '--ignore-certificate-errors',
    '--no-sandbox',
  ],
});
const context = await browser.newContext({ ignoreHTTPSErrors: true });

// Block requests to external hosts (Google Analytics, fonts, etc.) so that
// "networkidle" reflects the WEKO app itself and is not skewed by third-party
// beacons that hang or time out. Only the local instance is allowed.
await context.route('**/*', (route) => {
  let host = '';
  try { host = new URL(route.request().url()).hostname; } catch (e) {}
  if (host === 'weko3.example.org' || host === '127.0.0.1' || host === 'localhost') {
    route.continue();
  } else {
    route.abort();
  }
});

const page = await context.newPage();

// --- login (session cookie shared in the context) ---
await page.goto(`${BASE}/login/`, { waitUntil: 'domcontentloaded' });
await page.fill('input[name="email"]', EMAIL);
await page.fill('input[name="password"]', PASSWORD);
await Promise.all([
  page.waitForNavigation({ waitUntil: 'domcontentloaded' }).catch(() => {}),
  page.click('button[type="submit"], input[type="submit"]'),
]);

async function measure(url) {
  const times = [];
  // warm-up
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
  for (let i = 0; i < iterations; i++) {
    const t0 = Date.now();
    await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 }).catch(() => {});
    times.push(Date.now() - t0);
  }
  return times;
}

const lines = [];
lines.push(`# Headless-Chromium E2E  label=${label}  time=${new Date().toISOString()}`);
lines.push(`# base=${BASE} detail_recid=${detailRecid} iterations=${iterations}`);
lines.push(`# metric = navigation start -> networkidle (includes JS + AJAX render), seconds`);
lines.push('');
lines.push(['URL', 'min', 'med', 'mean', 'p90', 'max', 'n'].map((s) => s.padStart(8)).join(''));

for (const name of ['top', 'detail', 'search']) {
  const s = stats(await measure(urls[name]));
  const row = [name, f(s.min), f(s.med), f(s.mean), f(s.p90), f(s.max), String(s.n)];
  const out = row.map((x) => x.padStart(8)).join('');
  lines.push(out);
  console.log(out);
}

mkdirSync(OUTDIR, { recursive: true });
const outfile = `${OUTDIR}/${label}_browser.txt`;
writeFileSync(outfile, lines.join('\n') + '\n');
console.log('saved:', outfile);

await browser.close();
