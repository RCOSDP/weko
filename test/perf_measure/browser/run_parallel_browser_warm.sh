#!/bin/bash
# Parallel-load headless-Chromium E2E at a low concurrency with a WARM cache
# (no per-run flush), for both after (current branch) and before (3de23b2dd).
# Warming avoids the cold-start thundering-herd that inflates p90, so the
# before/after comparison reflects steady state.
#
# Usage: run_parallel_browser_warm.sh [total_per_url] [concurrency]
set -u
cd /home/mhaya/weko

TOTAL="${1:-100}"
CONC="${2:-5}"
RECID=3000001
AFTER_REF=fix/issues61802
BEFORE_REF=3de23b2dd
RESULTS=/home/mhaya/weko/test/perf_measure/results
SCRATCH=/tmp/weko_pbwarm_out; mkdir -p "$SCRATCH"
SCRIPT=/tmp/weko_perf_scripts/browser/measure_browser_parallel.mjs
WARM=/tmp/weko_perf_scripts/browser/measure_browser_parallel.mjs
COMPOSE="docker compose -f docker-compose.arm64.yml -p weko"

reload() { $COMPOSE exec -T web bash -lc 'touch /home/invenio/.virtualenvs/invenio/var/instance/conf/uwsgi.ini' >/dev/null 2>&1; }
wait_up(){ for i in $(seq 1 25); do c=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: weko3.example.org" --max-time 30 https://127.0.0.1:18443/ 2>/dev/null); [ "$c" = "200" ] && return; sleep 3; done; }

run_label() { # $1=label $2=expected_marker
  local m
  m=$(grep -c 'display_control = get_search_setting' modules/weko-theme/weko_theme/utils.py)
  echo "  marker=$m (expect $2)"
  [ "$m" != "$2" ] && { echo "  ABORT: code not switched"; exit 1; }
  # WARM: low-concurrency pre-pass populates all caches (no flush before measure)
  ( cd /tmp/weko_perf_scripts/browser && \
    OUTDIR="$SCRATCH" node "$WARM" "${1}_warm" "$RECID" 6 2 >/dev/null 2>&1 )
  # MEASURE at target concurrency (cache now warm)
  ( cd /tmp/weko_perf_scripts/browser && \
    OUTDIR="$SCRATCH" node "$SCRIPT" "$1" "$RECID" "$TOTAL" "$CONC" )
}

echo "=== AFTER ($AFTER_REF) ==="
git checkout "$AFTER_REF" -- modules/ >/dev/null 2>&1; reload; wait_up
run_label after 1

echo "=== BEFORE ($BEFORE_REF) ==="
git checkout "$BEFORE_REF" -- modules/ >/dev/null 2>&1; reload; wait_up
run_label before 0

echo "=== restore AFTER ==="
git checkout "$AFTER_REF" -- modules/ >/dev/null 2>&1; reload; wait_up

cp "$SCRATCH/after_browser.txt"  "$RESULTS/after_browser_c${CONC}.txt"
cp "$SCRATCH/before_browser.txt" "$RESULTS/before_browser_c${CONC}.txt"
echo "DONE (results: $RESULTS/{after,before}_browser_c${CONC}.txt)"
