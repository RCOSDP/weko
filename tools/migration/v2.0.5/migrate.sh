#!/bin/bash
#
# Upgrades the data of a WEKO site running the feature/a11y (v0.9.20 based)
# code to v2.0.5: PostgreSQL, Elasticsearch and static files.
#
# The commands reach the site through prefixes given in environment
# variables, so the same script works with docker compose and kubectl:
#
#   WEKO_MIG_WEB          command prefix that runs a command in the web
#                         container with stdin attached
#                         e.g. "docker compose -f docker-compose2.yml exec -T web"
#                              "kubectl exec -i -n weko3 <pod> -c web --"
#   WEKO_MIG_PSQL         psql connected to the site database, reading SQL
#                         from stdin. Use the primary (writable) server.
#                         e.g. "docker compose -f docker-compose2.yml exec -T postgresql psql -U invenio invenio"
#                              "kubectl exec -i -n weko3pg <primary pod> -- psql -U invenio <db>"
#   WEKO_MIG_INDEX_PREFIX value of SEARCH_INDEX_PREFIX of the site (needed by es)
#   WEKO_MIG_ES_URL       Elasticsearch URL as seen from the web container
#                         (default: http://elasticsearch:9200)
#   WEKO_MIG_CODE         v2.0.5 checkout on this host (default: the
#                         repository this script is in)
#   WEKO_MIG_LOG_DIR      where logs go (default: ./weko-upgrade-v2.0.5-logs)
#   WEKO_MIG_RESTRICTED_ITEM_TYPE_ID  argument of update_W2025-29.py (default: 30015)
#   WEKO_MIG_BATCH_SIZE   batch size of update_W2025-29.py (default: 500)
#
# Usage: migrate.sh [--dry-run] COMMAND
#
#   preflight  read-only checks; run before stopping the old site
#   drain      run with the OLD code: process the queued stats events and
#              aggregations and the indexer queue before the switch
#   db         PostgreSQL migration (run with the v2.0.5 code)
#   es         Elasticsearch migration and reindex (after db)
#   assets     build and collect the static files
#   verify     read-only checks after the upgrade
#   status     list the applied steps
#
# Steps that must run only once are recorded in the table
# weko_upgrade_v205_steps and skipped on a rerun, so a failed run can be
# started again from the beginning after fixing the cause.

set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SQL_DIR="${SCRIPT_DIR}/sql"
CODE_DIR=${WEKO_MIG_CODE:-$(cd "${SCRIPT_DIR}/../../.." && pwd)}
LOG_DIR=${WEKO_MIG_LOG_DIR:-./weko-upgrade-v2.0.5-logs}
ES_URL=${WEKO_MIG_ES_URL:-http://elasticsearch:9200}
RESTRICTED_ITEM_TYPE_ID=${WEKO_MIG_RESTRICTED_ITEM_TYPE_ID:-30015}
BATCH_SIZE=${WEKO_MIG_BATCH_SIZE:-500}
STATS_EVENTS=(celery-task item-create top-view record-view file-download file-preview search)
DRY_RUN=0

log() { echo "[$(date '+%F %T')] $*" | tee -a "${LOG_DIR}/migrate.log" >&2; }
die() { log "ERROR: $*"; exit 1; }

require() {
    local name
    for name in "$@"; do
        [ -n "${!name:-}" ] || die "${name} is not set"
    done
}

split_prefixes() {
    require WEKO_MIG_WEB WEKO_MIG_PSQL
    read -r -a WEB <<< "${WEKO_MIG_WEB}"
    read -r -a PSQL <<< "${WEKO_MIG_PSQL}"
}

# Runs a command, or prints it with --dry-run.
run() {
    if [ "${DRY_RUN}" = 1 ]; then
        echo "+ $*" >&2
        return 0
    fi
    "$@"
}

# Runs an SQL file and stops at the first error.
psql_file() {
    local file=$1
    log "psql < ${file}"
    [ -f "${file}" ] || die "${file} not found"
    if [ "${DRY_RUN}" = 1 ]; then
        echo "+ ${PSQL[*]} -v ON_ERROR_STOP=1 < ${file}" >&2
        return 0
    fi
    "${PSQL[@]}" -v ON_ERROR_STOP=1 < "${file}" 2>&1 | tee -a "${LOG_DIR}/psql.log"
}

# Runs one SQL statement and prints the result without decoration.
psql_value() {
    echo "$1" | "${PSQL[@]}" -v ON_ERROR_STOP=1 -tAq
}

# Runs "invenio ARGS..." in the web container. The scripts run through
# "invenio shell" log errors and exit 0, so a traceback in the output is
# also treated as a failure.
invenio() {
    local out="${LOG_DIR}/invenio.log" last="${LOG_DIR}/invenio.last"
    log "invenio $*"
    if [ "${DRY_RUN}" = 1 ]; then
        echo "+ ${WEB[*]} invenio $*" >&2
        return 0
    fi
    local rc=0
    "${WEB[@]}" invenio "$@" < /dev/null > "${last}" 2>&1 || rc=$?
    cat "${last}"
    cat "${last}" >> "${out}"
    [ "${rc}" = 0 ] || die "invenio $* failed with exit status ${rc} (see ${out})"
    if grep -q -E '^Traceback |\[ERROR\]' "${last}"; then
        die "invenio $* reported an error (see ${out})"
    fi
}

# es METHOD PATH [BODY] — calls Elasticsearch from the web container.
es() {
    local method=$1 path=$2 body=${3:-}
    log "es ${method} ${path}"
    if [ "${DRY_RUN}" = 1 ]; then
        echo "+ ${WEB[*]} curl -sS -X ${method} ${ES_URL}${path} ${body:+-d '${body}'}" >&2
        return 0
    fi
    local res
    if [ -n "${body}" ]; then
        res=$(printf '%s' "${body}" | "${WEB[@]}" curl -sS -X "${method}" "${ES_URL}${path}" \
            -H 'Content-Type: application/json' --data-binary @-)
    else
        res=$("${WEB[@]}" curl -sS -X "${method}" "${ES_URL}${path}" < /dev/null)
    fi
    echo "${res}" >> "${LOG_DIR}/es.log"
    if echo "${res}" | grep -q '"error"'; then
        die "es ${method} ${path}: ${res}"
    fi
    echo "${res}"
}

# Prints the HTTP status of HEAD PATH.
es_status() {
    "${WEB[@]}" curl -s -o /dev/null -w '%{http_code}' -I "${ES_URL}$1" < /dev/null
}

step_done() {
    [ "${DRY_RUN}" = 1 ] && return 1
    [ "$(psql_value "SELECT count(*) FROM weko_upgrade_v205_steps WHERE step = '$1';")" = 1 ]
}

mark_done() {
    [ "${DRY_RUN}" = 1 ] && return 0
    psql_value "INSERT INTO weko_upgrade_v205_steps (step) VALUES ('$1') ON CONFLICT (step) DO NOTHING;" > /dev/null
}

# step NAME FUNCTION — runs FUNCTION once and records NAME.
step() {
    local name=$1 func=$2
    if step_done "${name}"; then
        log "skip ${name} (already applied)"
        return 0
    fi
    log "begin ${name}"
    "${func}"
    mark_done "${name}"
    log "end ${name}"
}

# ---------------------------------------------------------------- preflight

cmd_preflight() {
    psql_file "${SQL_DIR}/preflight.sql" | tee "${LOG_DIR}/preflight-$(date +%Y%m%d%H%M%S).txt"
}

# ---------------------------------------------------------------- drain

cmd_drain() {
    # Run with the old code, after the site is closed to users.
    invenio stats events process --eager
    invenio stats aggregations process --eager --update-bookmark
    invenio index run
    invenio stats aggregations list-bookmarks --limit 1 | tee "${LOG_DIR}/bookmarks.txt"
    log "Check that every RabbitMQ queue is empty before stopping the old site:"
    log "  rabbitmqctl list_queues name messages"
}

# ---------------------------------------------------------------- db

db_before_v0927() { psql_file "${SQL_DIR}/10_before_v0927.sql"; }
db_oai_schema() { invenio shell scripts/demo/register_oai_schema.py overwrite_all; }
db_v0927() {
    psql_file "${CODE_DIR}/postgresql/ddl/v0.9.27.sql"
    if [ "${DRY_RUN}" = 0 ]; then
        echo "SELECT update_v0927();" | "${PSQL[@]}" -v ON_ERROR_STOP=1 2>&1 | tee -a "${LOG_DIR}/psql.log"
    fi
}
db_properties() { invenio shell scripts/demo/register_properties.py only_specified; }
db_itemtype_full() { invenio shell scripts/demo/update_itemtype_full.py; }
db_renew_itemtypes() { invenio shell scripts/demo/renew_all_item_types.py; }
db_jpcoar_v2_mapping() { invenio shell scripts/demo/addjpcoar_v2_mapping.py; }
db_fix_45614() {
    psql_file "${CODE_DIR}/postgresql/ddl/fix_itemtype_issue_45614.sql"
    if [ "${DRY_RUN}" = 0 ]; then
        echo "SELECT fix_itemtype_issue_45614();" | "${PSQL[@]}" -v ON_ERROR_STOP=1 2>&1 | tee -a "${LOG_DIR}/psql.log"
    fi
}
db_v107a2() { psql_file "${CODE_DIR}/postgresql/update/v1_0_7a2.sql"; }
db_before_w2025_29() { psql_file "${SQL_DIR}/20_before_w2025_29.sql"; }

# W2025-29.sql inserts jsonld_mappings for the item types 30001 and 30002
# without checking that they exist; a site without them would fail the
# whole transaction. Those INSERTs are dropped for missing item types.
db_w2025_29() {
    local src="${CODE_DIR}/postgresql/ddl/W2025-29.sql"
    local dst="${LOG_DIR}/W2025-29.applied.sql"
    [ -f "${src}" ] || die "${src} not found"
    cp "${src}" "${dst}"
    local id
    for id in 30001 30002; do
        if [ "${DRY_RUN}" = 1 ] || \
           [ "$(psql_value "SELECT count(*) FROM item_type WHERE id = ${id};")" = 0 ]; then
            log "item_type ${id} does not exist; its default jsonld mapping is not created"
            sed -i -E "/^INSERT INTO jsonld_mappings\(.*VALUES \('[^']*', '[^']*', ${id},/d" "${dst}"
        fi
    done
    psql_file "${dst}"
}
db_after_w2025_29() { psql_file "${SQL_DIR}/40_after_w2025_29.sql"; }
db_stats_partition() { psql_file "${SQL_DIR}/30_stats_partition.sql"; }
db_partitions() {
    local year
    year=$(date +%Y)
    invenio stats partition create "${year}"
    invenio stats partition create "$((year + 1))"
    invenio logging partition create "${year}"
    invenio logging partition create "$((year + 1))"
}
db_update_w2025_29_py() {
    invenio shell scripts/demo/update_W2025-29.py "${RESTRICTED_ITEM_TYPE_ID}" "${BATCH_SIZE}"
    if [ "${DRY_RUN}" = 0 ] && \
       ! grep -q 'All updates completed successfully' "${LOG_DIR}/invenio.last"; then
        die "update_W2025-29.py did not complete (see ${LOG_DIR}/invenio.log)"
    fi
}

cmd_db() {
    psql_file "${SQL_DIR}/00_steps.sql"
    # Up to v1.0.8 (tools/update/v0.9.27.bash and the v1.0.7 procedures)
    step db.10-before-v0927 db_before_v0927
    step db.20-oai-schema db_oai_schema
    step db.21-v0927 db_v0927
    step db.22-properties db_properties
    step db.23-itemtype-full db_itemtype_full
    step db.24-renew-itemtypes db_renew_itemtypes
    step db.25-jpcoar-v2-mapping db_jpcoar_v2_mapping
    step db.30-fix-45614 db_fix_45614
    step db.31-v107a2 db_v107a2
    # v1.0.8 to v2.0
    step db.40-before-w2025-29 db_before_w2025_29
    step db.41-w2025-29 db_w2025_29
    step db.42-after-w2025-29 db_after_w2025_29
    step db.50-stats-partition db_stats_partition
    step db.51-partitions db_partitions
    step db.60-update-w2025-29-py db_update_w2025_29_py
}

# ---------------------------------------------------------------- es

require_prefix() {
    require WEKO_MIG_INDEX_PREFIX
    P=${WEKO_MIG_INDEX_PREFIX%-}
}

es_cluster_settings() {
    es PUT /_cluster/settings '{"persistent":{"indices.mapping.dynamic_timeout":"600s"}}' > /dev/null
}

es_ilm_policy() {
    es PUT /_ilm/policy/weko_stats_policy \
        '{"policy":{"phases":{"hot":{"actions":{"rollover":{"max_size":"50gb"}}}}}}' > /dev/null
}

# Creates the indices that are missing and overwrites the templates
# (stats templates now carry the ILM settings).
es_index_init() { invenio index init --force; }

# v2.0.5 writes stats to the aliases, so each alias needs a write index.
# The yearly indices of the old code stay readable through the same alias.
es_stats_write_indices() {
    local e kind name alias
    for e in "${STATS_EVENTS[@]}"; do
        for kind in events-stats stats; do
            alias="${P}-${kind}-${e}"
            name="${alias}-000001"
            if [ "${DRY_RUN}" = 0 ] && [ "$(es_status "/${name}")" = 200 ]; then
                log "${name} exists"
                continue
            fi
            es PUT "/${name}" "{\"aliases\":{\"${alias}\":{\"is_write_index\":true}}}" > /dev/null
        done
    done
}

# The authors mapping gained communityIds; rebuild the index from the DB.
es_authors() {
    if [ "${DRY_RUN}" = 1 ] || [ "$(es_status "/${P}-authors-author-v1.0.0")" = 200 ]; then
        es DELETE "/${P}-authors-author-v1.0.0" > /dev/null
    fi
    invenio index init --force
    invenio authors reindex --yes-i-know
}

# Item documents changed (weko_shared_ids, Tika full text), so every record
# is indexed again from the DB.
es_records() {
    invenio index queue init
    invenio index reindex --pid-type recid --yes-i-know
    invenio index run --raise-on-error False --chunk-size 50
}

cmd_es() {
    require_prefix
    step es.10-cluster-settings es_cluster_settings
    step es.11-ilm-policy es_ilm_policy
    step es.12-index-init es_index_init
    step es.13-stats-write-indices es_stats_write_indices
    step es.20-authors es_authors
    step es.30-records es_records
    invenio queues declare
}

# ---------------------------------------------------------------- assets

cmd_assets() {
    invenio assets build
    invenio collect -v
}

# ---------------------------------------------------------------- verify

cmd_verify() {
    psql_file "${SQL_DIR}/verify.sql" | tee "${LOG_DIR}/verify-$(date +%Y%m%d%H%M%S).txt"
    if [ -n "${WEKO_MIG_INDEX_PREFIX:-}" ]; then
        require_prefix
        log "records in ES (${P}-weko): $(es GET "/${P}-weko/_count")"
        es GET "/_cat/aliases/${P}-*stats*?v" | tee -a "${LOG_DIR}/verify-aliases.txt"
    fi
}

cmd_status() {
    psql_value "SELECT step || '  ' || done_at FROM weko_upgrade_v205_steps ORDER BY done_at;"
}

main() {
    if [ "${1:-}" = "--dry-run" ]; then
        DRY_RUN=1
        shift
    fi
    local cmd=${1:-}
    mkdir -p "${LOG_DIR}"
    split_prefixes
    case "${cmd}" in
        preflight|drain|db|es|assets|verify|status) "cmd_${cmd}" ;;
        *) sed -n '2,40p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
    esac
}

main "$@"
