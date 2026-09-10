// Parallel-load headless-Chromium E2E timing for the WEKO top page, item
// landing page and search-result list.
//
// Unlike measure_browser.mjs (one navigation at a time), this drives C browser
// pages concurrently against the same URL, reproducing the "busy site"
// condition where the web tier (uwsgi processes=2 x threads=2 =~4 concurrent)
// is contended. The per-request CPU/DB savings of the fix then show up as lower
// tail latency and higher throughput in a real browser (JS + AJAX included).
//
// Usage:
//   node measure_browser_parallel.mjs <label> [detailRecid] [totalPerUrl] [concurrency]
// Env: BASE (default https://weko3.example.org:18443), EMAIL, PASSWORD, OUTDIR
import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';

const label = process.argv[2] || 'run';
const detailRecid = process.argv[3] || '3000001';
const totalPerUrl = parseInt(process.argv[4] || '48', 10);
const CONC = parseInt(process.argv[5] || '6', 10);
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
  if (!n) return { min: NaN, med: NaN, mean: NaN, p90: NaN, p95: NaN, max: NaN, n: 0 };
  const q = (p) => a[Math.min(n - 1, Math.max(0, Math.ceil((p / 100) * n) - 1))];
  const mean = a.reduce((s, x) => s + x, 0) / n;
  return { min: a[0], med: q(50), mean, p90: q(90), p95: q(95), max: a[n - 1], n };
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
// Block external hosts so networkidle reflects the WEKO app itself.
await context.route('**/*', (route) => {
  let host = '';
  try { host = new URL(route.request().url()).hostname; } catch (e) {}
  if (host === 'weko3.example.org' || host === '127.0.0.1' || host === 'localhost') {
    route.continue();
  } else {
    route.abort();
  }
});

// login once (cookie shared across all pages in this context)
const loginPage = await context.newPage();
await loginPage.goto(`${BASE}/login/`, { waitUntil: 'domcontentloaded' });
await loginPage.fill('input[name="email"]', EMAIL);
await loginPage.fill('input[name="password"]', PASSWORD);
await Promise.all([
  loginPage.waitForNavigation({ waitUntil: 'domcontentloaded' }).catch(() => {}),
  loginPage.click('button[type="submit"], input[type="submit"]'),
]);
await loginPage.close();

// pool of concurrent pages
const pages = [];
for (let i = 0; i < CONC; i++) pages.push(await context.newPage());

async function measure(url) {
  // warm-up
  await pages[0].goto(url, { waitUntil: 'networkidle', timeout: 120000 }).catch(() => {});
  const lat = [];
  let issued = 0;
  const t0 = Date.now();
  async function worker(page) {
    while (issued < totalPerUrl) {
      issued++;
      const s = Date.now();
      await page.goto(url, { waitUntil: 'networkidle', timeout: 120000 }).catch(() => {});
      lat.push(Date.now() - s);
    }
  }
  await Promise.all(pages.map((p) => worker(p)));
  const wall = (Date.now() - t0) / 1000;
  return { s: stats(lat), rps: lat.length / wall, wall };
}

const lines = [];
lines.push(`# Parallel-load headless-Chromium E2E  label=${label}  time=${new Date().toISOString()}`);
lines.push(`# base=${BASE} detail_recid=${detailRecid} concurrency=${CONC} total_per_url=${totalPerUrl}`);
lines.push(`# metric = navigation start -> networkidle (JS + AJAX) under ${CONC} concurrent page loads, seconds`);
lines.push('');
lines.push(['URL', 'min', 'med', 'mean', 'p90', 'p95', 'max', 'rps', 'n']
  .map((s) => s.padStart(8)).join(''));

for (const name of ['top', 'detail', 'search']) {
  const { s, rps } = await measure(urls[name]);
  const row = [name, f(s.min), f(s.med), f(s.mean), f(s.p90), f(s.p95), f(s.max),
              rps.toFixed(2), String(s.n)];
  const out = row.map((x) => x.padStart(8)).join('');
  lines.push(out);
  console.log(out);
}

mkdirSync(OUTDIR, { recursive: true });
const outfile = `${OUTDIR}/${label}_browser.txt`;
writeFileSync(outfile, lines.join('\n') + '\n');
console.log('saved:', outfile);
await browser.close();
