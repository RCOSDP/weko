#!/usr/bin/env bash
#
# load.sh - load the "download button not shown for approved user" reproduction
#           fixture into a freshly built WEKO3 instance.
#
# PREREQUISITE
#   A normal fresh setup has already been done, i.e. install.sh
#   (populate-instance.sh + item_type3.sql + resticted_access.sql) has run and
#   the containers are up.  The fixture relies on what that setup creates:
#     - item_type 15 (デフォルトアイテムタイプ（フル）) and 31001 (利用申請)
#     - accounts_role 1..4 (System/Repository/Contributor/Community)
#     - demo accounts repoadmin@ / contributor@ / user@ / comadmin@example.org
#     - files_location id = 1
#
# WHAT IT DOES
#   1. loads fixture.sql into PostgreSQL (adds rows only - see fixture.sql)
#   2. bulk-loads es_bulk.ndjson into the Elasticsearch item index
#
# It never drops, truncates or overwrites anything outside the ID ranges the
# fixture owns.
#
# USAGE
#   ./scripts/demo/download_button_bug_repro/load.sh
#
# Override the defaults with environment variables if your compose project or
# port mapping differs:
#   PG_CONTAINER=weko-postgresql-1 PG_USER=invenio PG_DB=invenio \
#   ES_URL=http://localhost:29201 ES_INDEX=tenant1-weko-item-v1.0.0 ./load.sh
#
set -o errexit
set -o nounset
set -o pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PG_CONTAINER="${PG_CONTAINER:-weko-postgresql-1}"
PG_USER="${PG_USER:-invenio}"
PG_DB="${PG_DB:-invenio}"
ES_URL="${ES_URL:-http://localhost:29201}"
ES_INDEX="${ES_INDEX:-tenant1-weko-item-v1.0.0}"

echo "==> loading fixture.sql into ${PG_CONTAINER}:${PG_DB}"
docker exec -i "${PG_CONTAINER}" psql -U "${PG_USER}" -d "${PG_DB}" \
    < "${HERE}/fixture.sql"

echo "==> bulk loading es_bulk.ndjson into ${ES_URL}/${ES_INDEX}"
# The ndjson already carries the index name in every action line, so _bulk on
# the cluster root is enough.  A trailing newline is required by the _bulk API.
curl -sS -H 'Content-Type: application/x-ndjson' \
    -X POST "${ES_URL}/_bulk?refresh=true" \
    --data-binary "@${HERE}/es_bulk.ndjson" \
    | python3 -c 'import json,sys; r=json.load(sys.stdin); print("  errors:", r.get("errors")); [print("  ", i) for i in r.get("items", [])[:1]]'

echo
echo "==> done."
echo "    Demo item        : https://<your-host>/records/2003976"
echo "    Usage application: activity A-20260917-00001 (status F = 完了)"
echo
echo "    Optional - attach a placeholder file body (not needed to see the bug):"
echo "      docker compose exec -T web invenio shell \\"
echo "        /code/scripts/demo/download_button_bug_repro/attach_file.py"
echo
echo "    Verify the bug from the shell:"
echo "      docker compose exec -T web invenio shell \\"
echo "        /code/scripts/demo/download_button_bug_repro/verify.py"
