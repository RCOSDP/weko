#!/bin/bash
# Run the concurrent search-API load test for BOTH after (current branch) and
# before (3de23b2dd) at several concurrency levels, switching code via git
# checkout + uwsgi reload. Results -> results/load_<label>_c<conc>.txt
set -u
cd /home/mhaya/weko

TOTAL="${1:-400}"
SIZE="${2:-100}"
CONCS=(4 8 16)
AFTER_REF=fix/issues61802
BEFORE_REF=3de23b2dd
RESULTS=/home/mhaya/weko/test/perf_measure/results
LT=/home/mhaya/weko/test/perf_measure/loadtest/loadtest.mjs
COMPOSE="docker compose -f docker-compose.arm64.yml -p weko"

reload() { $COMPOSE exec -T web bash -lc 'touch /home/invenio/.virtualenvs/invenio/var/instance/conf/uwsgi.ini' >/dev/null 2>&1; }
flush()  { docker exec weko-redis-1 redis-cli -n 0 FLUSHDB >/dev/null 2>&1; }
wait_up(){ for i in $(seq 1 25); do c=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: weko3.example.org" --max-time 30 https://127.0.0.1:18443/ 2>/dev/null); [ "$c" = "200" ] && return; sleep 3; done; }

measure() { # $1=label
  local L="$1"
  for c in "${CONCS[@]}"; do
    flush
    OUTDIR="$RESULTS" node "$LT" "${L}_c${c}" "$c" "$TOTAL" "$SIZE"
    # rename to stable file name
    mv "$RESULTS/load_${L}_c${c}.txt" "$RESULTS/load_${L}_c${c}.txt" 2>/dev/null
  done
}

echo "=== AFTER ($AFTER_REF) ==="
git checkout "$AFTER_REF" >/dev/null 2>&1; reload; wait_up
echo "  marker=$(grep -c 'display_control = get_search_setting' modules/weko-theme/weko_theme/utils.py) (expect 1)"
measure after

echo "=== BEFORE ($BEFORE_REF) ==="
git checkout "$BEFORE_REF" >/dev/null 2>&1; reload; wait_up
echo "  marker=$(grep -c 'display_control = get_search_setting' modules/weko-theme/weko_theme/utils.py) (expect 0)"
measure before

echo "=== restore AFTER ==="
git checkout "$AFTER_REF" >/dev/null 2>&1; reload; wait_up
echo "DONE"
