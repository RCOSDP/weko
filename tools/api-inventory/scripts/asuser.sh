#!/bin/bash
# asuser.sh <email> <method> <path> [curl-extra...]
S=/tmp/claude-1000/-home-mhaya-wekov2/a8119b60-023e-4882-84ac-a0edcfb5627e/scratchpad/api
H='Host: weko3.example.org'; B=https://localhost:8443
jar=$(mktemp)
curl -sk -c "$jar" -o /dev/null --max-time 10 -H "$H" -X POST "$B/api/v1/login" -H 'Content-Type: application/json' -d "{\"email\":\"$1\",\"password\":\"Passw0rd!123\"}"
m=$2; p=$3; shift 3
curl -sk -b "$jar" -o /dev/null -w '%{http_code}' --max-time 12 -H "$H" -X "$m" "$@" "$B$p"
rm -f "$jar"
