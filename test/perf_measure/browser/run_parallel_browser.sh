#!/bin/bash
# Run the PARALLEL-load headless-Chromium E2E for both after (current branch)
# and before (3de23b2dd), switching code via git checkout + uwsgi reload.
# Writes results/<label>_browser.txt (overwrites the sequential ones; those are
# backed up under results/sequential_browser/).
set -u
cd /home/mhaya/weko

TOTAL="${1:-48}"
CONC="${2:-6}"
RECID=3000001
AFTER_REF=fix/issues61802
BEFORE_REF=3de23b2dd
RESULTS=/home/mhaya/weko/test/perf_measure/results
# Write to a scratch dir NOT tracked by git so writing results does not make the
# working tree dirty and block the git checkout that switches before/after code.
SCRATCH=/tmp/weko_parallel_browser_out
mkdir -p "$SCRATCH"
SCRIPT=/tmp/weko_perf_scripts/browser/measure_browser_parallel.mjs
COMPOSE="docker compose -f docker-compose.arm64.yml -p weko"

reload() { $COMPOSE exec -T web bash -lc 'touch /home/invenio/.virtualenvs/invenio/var/instance/conf/uwsgi.ini' >/dev/null 2>&1; }
flush()  { docker exec weko-redis-1 redis-cli -n 0 FLUSHDB >/dev/null 2>&1; }
wait_up(){ for i in $(seq 1 25); do c=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: weko3.example.org" --max-time 30 https://127.0.0.1:18443/ 2>/dev/null); [ "$c" = "200" ] && return; sleep 3; done; }

run_label() { # $1=label $2=expected_marker
  local m
  m=$(grep -c 'display_control = get_search_setting' modules/weko-theme/weko_theme/utils.py)
  echo "  marker=$m (expect $2)"
  if [ "$m" != "$2" ]; then echo "  ABORT: code not switched as expected"; exit 1; fi
  flush
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

# publish scratch results into the tracked results dir now that switching is done
cp "$SCRATCH/after_browser.txt" "$RESULTS/after_browser.txt"
cp "$SCRATCH/before_browser.txt" "$RESULTS/before_browser.txt"
echo "DONE (results copied to $RESULTS)"
