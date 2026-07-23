// Concurrent load test for the WEKO search REST API.
//
// The web tier runs uwsgi with processes=2 x threads=2 (=~4 concurrent
// requests). Under concurrency > that, each request's own CPU/DB cost turns
// into queueing latency, so a heavier per-request path (before the fix) shows
// up as lower throughput and higher tail latency. This is the production
// "busy site" condition where the optimisation is meant to help.
//
// Usage: node loadtest.mjs <label> [concurrency] [totalRequests] [size]
// Env: BASE (default https://127.0.0.1:18443), HOSTHDR, EMAIL, PASSWORD, OUTDIR
import { writeFileSync, mkdirSync } from 'fs';
import https from 'https';

const label = process.argv[2] || 'run';
const CONC = parseInt(process.argv[3] || '16', 10);
const TOTAL = parseInt(process.argv[4] || '400', 10);
const SIZE = parseInt(process.argv[5] || '100', 10);
const BASE = process.env.BASE || 'https://127.0.0.1:18443';
const HOSTHDR = process.env.HOSTHDR || 'weko3.example.org';
const EMAIL = process.env.EMAIL || 'wekosoftware@nii.ac.jp';
const PASSWORD = process.env.PASSWORD || 'uspass123';
const OUTDIR = process.env.OUTDIR || new URL('../results', import.meta.url).pathname;
const PATH = `/search?search_type=0&size=${SIZE}&q=`; // API is served under /search too via api? use REST:
const API_PATH = `/api/records/?search_type=0&size=${SIZE}&page=1&q=`;

const agent = new https.Agent({ rejectUnauthorized: false, keepAlive: true, maxSockets: CONC + 4 });
const base = new URL(BASE);

function raw(method, path, { headers = {}, body = null } = {}) {
  return new Promise((resolve, reject) => {
    const req = https.request({
      hostname: base.hostname, port: base.port, path, method, agent,
      headers: { Host: HOSTHDR, ...headers },
    }, (res) => {
      let data = '';
      res.on('data', (c) => (data += c));
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

function cookiesFrom(res, jar) {
  const sc = res.headers['set-cookie'] || [];
  for (const c of sc) {
    const [kv] = c.split(';');
    const i = kv.indexOf('=');
    jar[kv.slice(0, i).trim()] = kv.slice(i + 1).trim();
  }
}
const cookieHeader = (jar) => Object.entries(jar).map(([k, v]) => `${k}=${v}`).join('; ');

async function login() {
  const jar = {};
  const g = await raw('GET', '/login/');
  cookiesFrom(g, jar);
  const m = g.body.match(/name="csrf_token"[^>]*value="([^"]+)"/);
  const csrf = m ? m[1] : '';
  const form = `csrf_token=${encodeURIComponent(csrf)}&email=${encodeURIComponent(EMAIL)}` +
               `&password=${encodeURIComponent(PASSWORD)}&submit=Log+In`;
  const p = await raw('POST', '/login/', {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'Content-Length': Buffer.byteLength(form),
      Cookie: cookieHeader(jar),
    },
    body: form,
  });
  cookiesFrom(p, jar);
  return jar;
}

function pct(sorted, p) {
  if (!sorted.length) return NaN;
  const i = Math.min(sorted.length - 1, Math.ceil((p / 100) * sorted.length) - 1);
  return sorted[Math.max(0, i)];
}

async function run() {
  const jar = await login();
  const cookie = cookieHeader(jar);
  // warm-up
  await raw('GET', API_PATH, { headers: { Cookie: cookie } });

  const lat = [];
  let issued = 0, ok = 0, bad = 0;
  const t0 = Date.now();

  async function worker() {
    while (issued < TOTAL) {
      issued++;
      const s = Date.now();
      try {
        const r = await raw('GET', API_PATH, { headers: { Cookie: cookie } });
        (r.status === 200 ? ok++ : bad++);
      } catch (e) { bad++; }
      lat.push(Date.now() - s);
    }
  }
  await Promise.all(Array.from({ length: CONC }, worker));

  const wall = (Date.now() - t0) / 1000;
  lat.sort((a, b) => a - b);
  const mean = lat.reduce((s, x) => s + x, 0) / lat.length;
  const out = {
    label, concurrency: CONC, total: TOTAL, size: SIZE,
    ok, bad, wall_s: wall.toFixed(2),
    throughput_rps: (ok / wall).toFixed(2),
    p50_ms: pct(lat, 50), p90_ms: pct(lat, 90), p95_ms: pct(lat, 95),
    p99_ms: pct(lat, 99), min_ms: lat[0], max_ms: lat[lat.length - 1],
    mean_ms: mean.toFixed(1),
  };
  const line =
    `label=${label} conc=${CONC} n=${ok}/${TOTAL} wall=${out.wall_s}s ` +
    `rps=${out.throughput_rps} p50=${out.p50_ms} p90=${out.p90_ms} ` +
    `p95=${out.p95_ms} p99=${out.p99_ms} max=${out.max_ms} mean=${out.mean_ms}ms`;
  console.log(line);
  mkdirSync(OUTDIR, { recursive: true });
  writeFileSync(`${OUTDIR}/load_${label}.txt`,
    `# concurrent load test (search REST API)\n${JSON.stringify(out, null, 2)}\n${line}\n`);
}
run().catch((e) => { console.error(e); process.exit(1); });
