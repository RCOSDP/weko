#!/bin/bash
# Concurrent curl load test for the TOP and DETAIL pages (where common-A/B/D
# reduce per-request DB queries), for both after (current branch) and before
# (3de23b2dd). Switches code with `git checkout <ref> -- modules/` (code only,
# leaving test/perf_measure untouched) and verifies the marker per label.
# Writes results/load_<label>_<target>_c<conc>.txt.
set -u
cd /home/mhaya/weko

TOTAL="${1:-100}"
CONC="${2:-20}"
TARGETS=(top detail)
RECID=3000001
AFTER_REF=fix/issues61802
BEFORE_REF=3de23b2dd
RESULTS=/home/mhaya/weko/test/perf_measure/results
SCRATCH=/tmp/weko_loadpages_out; mkdir -p "$SCRATCH"
LT=/tmp/weko_perf_scripts/loadtest.mjs
COMPOSE="docker compose -f docker-compose.arm64.yml -p weko"

reload() { $COMPOSE exec -T web bash -lc 'touch /home/invenio/.virtualenvs/invenio/var/instance/conf/uwsgi.ini' >/dev/null 2>&1; }
flush()  { docker exec weko-redis-1 redis-cli -n 0 FLUSHDB >/dev/null 2>&1; }
wait_up(){ for i in $(seq 1 25); do c=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: weko3.example.org" --max-time 30 https://127.0.0.1:18443/ 2>/dev/null); [ "$c" = "200" ] && return; sleep 3; done; }

measure() { # $1=label $2=expected_marker
  local m
  m=$(grep -c 'display_control = get_search_setting' modules/weko-theme/weko_theme/utils.py)
  echo "  marker=$m (expect $2)"
  [ "$m" != "$2" ] && { echo "  ABORT: code not switched"; exit 1; }
  for t in "${TARGETS[@]}"; do
    flush
    # note: cache-backed getters (B/D) benefit warm; measure.sh-style warmup is in loadtest.mjs
    OUTDIR="$SCRATCH" node "$LT" "$1_${t}" "$CONC" "$TOTAL" 100 "$t" "$RECID"
    mv "$SCRATCH/load_$1_${t}.txt" "$SCRATCH/load_$1_${t}_c${CONC}.txt" 2>/dev/null || true
  done
}

echo "=== AFTER ($AFTER_REF) ==="
git checkout "$AFTER_REF" -- modules/ >/dev/null 2>&1; reload; wait_up
measure after 1

echo "=== BEFORE ($BEFORE_REF) ==="
git checkout "$BEFORE_REF" -- modules/ >/dev/null 2>&1; reload; wait_up
measure before 0

echo "=== restore AFTER ==="
git checkout "$AFTER_REF" -- modules/ >/dev/null 2>&1; reload; wait_up

for lbl in after before; do
  for t in "${TARGETS[@]}"; do
    cp "$SCRATCH/load_${lbl}_${t}_c${CONC}.txt" "$RESULTS/load_${lbl}_${t}_c${CONC}.txt" 2>/dev/null || \
    cp "$SCRATCH/load_${lbl}_${t}.txt" "$RESULTS/load_${lbl}_${t}_c${CONC}.txt" 2>/dev/null || true
  done
done
echo "DONE (results in $RESULTS)"
