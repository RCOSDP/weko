#!/bin/bash
# E2E response-time measurement for the WEKO top page, item landing page and
# search-result list. Logs in (item detail / search results require auth in
# this instance), hits the running compose stack through nginx, and reports
# per-URL timing statistics into results/<label>.txt.
#
# Usage:
#   perf_measure/measure.sh <label> [detail_recid] [iterations] [search_size]
#
#   label        : tag written into the output (e.g. before / after)
#   detail_recid : recid used for the item landing page (default 3000001)
#   iterations   : warm requests per URL (default 30)
#   search_size  : hits requested from the search API (default 100)
#
# Env overrides:
#   BASE_URL (default https://127.0.0.1:18443)
#   HOSTHDR  (default weko3.example.org)
#   EMAIL / PASSWORD (default admin from docker-compose.arm64.yml)
#   OUTDIR   (default perf_measure/results)
set -u

LABEL="${1:-run}"
DETAIL_RECID="${2:-3000001}"
ITER="${3:-30}"
SEARCH_SIZE="${4:-100}"
BASE_URL="${BASE_URL:-https://127.0.0.1:18443}"
HOSTHDR="${HOSTHDR:-weko3.example.org}"
EMAIL="${EMAIL:-wekosoftware@nii.ac.jp}"
PASSWORD="${PASSWORD:-uspass123}"
OUTDIR="${OUTDIR:-test/perf_measure/results}"
mkdir -p "$OUTDIR"
CJ="$(mktemp)"

req() { # $1=path [extra curl args...] -> prints "http_code time_total"
  local path="$1"; shift
  curl -sk -b "$CJ" -c "$CJ" -o /dev/null -w "%{http_code} %{time_total}" \
       -H "Host: ${HOSTHDR}" "$@" "${BASE_URL}${path}" 2>/dev/null
}

# --- login (session cookie) ---
curl -sk -c "$CJ" -H "Host: ${HOSTHDR}" "${BASE_URL}/login/" -o "$CJ.html" 2>/dev/null
CSRF=$(grep -oE 'name="csrf_token"[^>]*value="[^"]+"' "$CJ.html" \
        | grep -oE 'value="[^"]+"' | head -1 | sed 's/value="//;s/"//')
LOGIN_CODE=$(curl -sk -c "$CJ" -b "$CJ" -H "Host: ${HOSTHDR}" \
  -d "csrf_token=${CSRF}" -d "email=${EMAIL}" -d "password=${PASSWORD}" \
  -d "submit=Log+In" -o /dev/null -w "%{http_code}" "${BASE_URL}/login/" 2>/dev/null)
echo "login: HTTP ${LOGIN_CODE}"

declare -A URLS=(
  [top]="/"
  [detail]="/records/${DETAIL_RECID}"
  [search]="/api/records/?search_type=0&size=${SEARCH_SIZE}&page=1&q="
)

stats() { # numbers on stdin -> "min median mean p90 max n"
  sort -n | awk '{a[NR]=$1; s+=$1} END{
    if(NR==0){print "NA NA NA NA NA 0"; exit}
    n=NR; med=(n%2)?a[(n+1)/2]:(a[n/2]+a[n/2+1])/2;
    idx=int((n*0.9)+0.999); if(idx<1)idx=1; if(idx>n)idx=n;
    printf "%.3f %.3f %.3f %.3f %.3f %d", a[1], med, s/n, a[idx], a[n], n}'
}

TS=$(date '+%Y-%m-%d %H:%M:%S')
RESULT="${OUTDIR}/${LABEL}.txt"
{
  echo "# E2E measurement  label=${LABEL}  time=${TS}"
  echo "# base=${BASE_URL} host=${HOSTHDR} detail_recid=${DETAIL_RECID} iterations=${ITER} search_size=${SEARCH_SIZE}"
  echo "# search URL is the REST API (/api/records/) where per-hit serialization runs"
  echo ""
  printf "%-8s %-6s %8s %8s %8s %8s %8s %5s\n" URL HTTP min med mean p90 max n
} > "$RESULT"

for name in top detail search; do
  path="${URLS[$name]}"
  read code _ < <(req "$path")          # warm-up
  tmp="$(mktemp)"
  for i in $(seq 1 "$ITER"); do
    read code t < <(req "$path")
    echo "$t" >> "$tmp"
  done
  read mn md mean p90 mx n < <(stats < "$tmp")
  rm -f "$tmp"
  printf "%-8s %-6s %8s %8s %8s %8s %8s %5s\n" \
    "$name" "$code" "$mn" "$md" "$mean" "$p90" "$mx" "$n" | tee -a "$RESULT"
done

rm -f "$CJ" "$CJ.html"
echo ""
echo "saved: $RESULT"
