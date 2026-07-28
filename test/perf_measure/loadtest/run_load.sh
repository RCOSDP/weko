#!/bin/bash
# Run the concurrent search-API load test for BOTH after (current branch) and
# before (3de23b2dd) at the given concurrency level(s), switching code via git
# checkout + uwsgi reload.
#
# Usage: run_load.sh [total] [size] [conc1 conc2 ...]
#   total : requests per (label, concurrency)   default 400
#   size  : search API size=                     default 100
#   conc* : concurrency levels                   default "4 8 16"
#
# Results are written to a scratch dir first (so a dirty tracked file can't
# block the git checkout) and copied to results/load_<label>_c<conc>.txt at the
# end. The code marker is verified before each label.
set -u
cd /home/mhaya/weko

TOTAL="${1:-400}"
SIZE="${2:-100}"
shift $(( $# > 2 ? 2 : $# ))
CONCS=("$@"); [ ${#CONCS[@]} -eq 0 ] && CONCS=(4 8 16)

AFTER_REF=fix/issues61802
BEFORE_REF=3de23b2dd
RESULTS=/home/mhaya/weko/test/perf_measure/results
SCRATCH=/tmp/weko_loadtest_out; mkdir -p "$SCRATCH"
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
  for c in "${CONCS[@]}"; do
    flush
    OUTDIR="$SCRATCH" node "$LT" "$1_c${c}" "$c" "$TOTAL" "$SIZE"
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

for c in "${CONCS[@]}"; do
  cp "$SCRATCH/load_after_c${c}.txt"  "$RESULTS/load_after_c${c}.txt"
  cp "$SCRATCH/load_before_c${c}.txt" "$RESULTS/load_before_c${c}.txt"
done
echo "DONE (results copied to $RESULTS)"
