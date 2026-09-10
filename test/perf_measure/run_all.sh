#!/bin/bash
# Run curl + headless-Chromium E2E for BOTH after (current branch) and before
# (commit 3de23b2dd), switching the running web code via git checkout + uwsgi
# touch-reload. Redis is flushed before every measurement. Intended to run
# unattended (e.g. in the background).
#
# Usage: test/perf_measure/run_all.sh [curl_iter] [browser_iter]
set -u
cd /home/mhaya/weko

CURL_ITER="${1:-100}"
BROWSER_ITER="${2:-100}"
RECID=3000001
SEARCH_SIZE=100
AFTER_REF=fix/issues61802
BEFORE_REF=3de23b2dd
RESULTS=/home/mhaya/weko/test/perf_measure/results
COMPOSE="docker compose -f docker-compose.arm64.yml -p weko"

reload()  { $COMPOSE exec -T web bash -lc 'touch /home/invenio/.virtualenvs/invenio/var/instance/conf/uwsgi.ini' >/dev/null 2>&1; }
flush()   { docker exec weko-redis-1 redis-cli -n 0 FLUSHDB >/dev/null 2>&1; }
wait_up() {
  for i in $(seq 1 25); do
    c=$(curl -sk -o /dev/null -w "%{http_code}" -H "Host: weko3.example.org" \
        --max-time 30 https://127.0.0.1:18443/ 2>/dev/null)
    [ "$c" = "200" ] && return 0
    sleep 3
  done
  echo "WARN: web did not return 200 in time"
}

verify_code() { # $1 = expect_marker_count (0=before, 1=after)
  local n
  n=$(grep -c "display_control = get_search_setting" \
      modules/weko-theme/weko_theme/utils.py 2>/dev/null)
  echo "  code marker (display_control)=$n (expect $1)"
}

measure_label() { # $1 = label
  local L="$1"
  echo "  [curl] $L ..."
  flush
  OUTDIR="$RESULTS" bash test/perf_measure/measure.sh "$L" "$RECID" "$CURL_ITER" "$SEARCH_SIZE" >/dev/null
  echo "  [browser] $L ..."
  flush
  ( cd test/perf_measure/browser && \
    OUTDIR="$RESULTS" node measure_browser.mjs "$L" "$RECID" "$BROWSER_ITER" >/dev/null )
}

echo "=== AFTER ($AFTER_REF) ==="
git checkout "$AFTER_REF" >/dev/null 2>&1
reload; wait_up; verify_code 1
measure_label after

echo "=== BEFORE ($BEFORE_REF) ==="
git checkout "$BEFORE_REF" >/dev/null 2>&1
reload; wait_up; verify_code 0
measure_label before

echo "=== restore AFTER ($AFTER_REF) ==="
git checkout "$AFTER_REF" >/dev/null 2>&1
reload; wait_up; verify_code 1

echo "=== DONE. results in $RESULTS ==="
ls -1 "$RESULTS"
