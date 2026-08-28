#!/bin/bash
#
# feature/restricted_v1.0.7 -> v2.0.3 アップデート補助スクリプト (docker-compose 版)
#
# 手順書: weko-document/docs/operation/restricted_v1.0.7_to_v2.0.3.md
# 基準  : weko-document/docs/operation/v1.0.8b_v2.0.0.md (v1.0.8b -> v2.0.0 正規手順)
#
# 前提:
#   - weko リポジトリのルートで実行する
#   - 制限公開(利用申請)機能は有効のまま継続する
#
# 使い方:
#   ./tools/upgrade_restricted_v1.0.7_to_v2.0.3.sh <step>
#
#   check    3章 事前調査(サービス稼働中に実行可・更新なし)
#   backup   5章 DB/設定のバックアップ
#   config   6-3 instance.cfg の制限公開フラグを True にする
#   build    6-4 イメージビルド + postgresql のみ起動
#   migrate  7章 DB マイグレーション (W2025-29.sql ほか)
#   data     8-1,8-2 全サービス起動と update_W2025-29.py
#   reindex  8-3〜8-5 ES マッピング更新 / dynamic timeout / 再インデックス
#   assets   8-6 assets build / collect / invenio.cfg 再生成
#   verify   7-3 / 9章 の機械的確認
#
# 環境変数:
#   COMPOSE_FILE_NAME            既定 docker-compose2.yml
#   WORK_DIR                     既定 ./upgrade_work  (ログ/バックアップ。全ステップで共有する)
#   RESTRICTED_ACCESS_PROPERTY   既定 30015  (item_type_property.id)
#   BATCH_SIZE                   既定 500    (update_W2025-29.py の第2引数)
#   REINDEX_CHUNK_SIZE           既定 50     (invenio index run --chunk-size)
#   APPLY_V1_0_7A2 / APPLY_FIX45092 / APPLY_61660
#                                yes/no。未指定なら migrate 時に DB を見て自動判定する
#                                (postgresql/update/v1.0.7b.sql は構文エラーかつ対象0件のため扱わない)
#
set -uo pipefail

COMPOSE_FILE_NAME="${COMPOSE_FILE_NAME:-docker-compose2.yml}"
WORK_DIR="${WORK_DIR:-$(pwd)/upgrade_work}"   # 全ステップで同じディレクトリを使う
RESTRICTED_ACCESS_PROPERTY="${RESTRICTED_ACCESS_PROPERTY:-30015}"
BATCH_SIZE="${BATCH_SIZE:-500}"
REINDEX_CHUNK_SIZE="${REINDEX_CHUNK_SIZE:-50}"
TARGET_TAG="${TARGET_TAG:-v2.0.3}"

if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose -f ${COMPOSE_FILE_NAME}"
else
    COMPOSE="docker-compose -f ${COMPOSE_FILE_NAME}"
fi

log()  { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${WORK_DIR}/upgrade.log" ; }
die()  { log "ERROR: $*" ; exit 1 ; }

confirm() {
    local msg="$1"
    read -r -p "${msg} [y/N]: " ans
    case "${ans}" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) log "中断しました" ; exit 1 ;;
    esac
}

psql_q() {  # 値だけを取り出す(改行・空白を除去)
    ${COMPOSE} exec -T postgresql psql -U invenio -d invenio -qtAX -c "$1" 2>/dev/null \
        | tr -d '\r' | head -1 | tr -d '[:space:]'
}

psql_count() {  # 数値が取れなければ die する
    local v
    v=$(psql_q "$1")
    case "${v}" in
        ''|*[!0-9]*) die "SQL の結果が数値ではありません: $1 -> '${v}'" ;;
    esac
    echo "${v}"
}

psql_show() {
    ${COMPOSE} exec -T postgresql psql -U invenio -d invenio -c "$1"
}

apply_sql() {  # apply_sql <path>
    local f="$1" base
    base="$(basename "${f}")"
    [ -f "${f}" ] || die "SQL が見つかりません: ${f}"
    log "apply: ${f}"
    docker cp "${f}" "$(${COMPOSE} ps -q postgresql)":"/tmp/${base}" || die "docker cp 失敗: ${f}"
    ${COMPOSE} exec -T postgresql psql -U invenio -d invenio -v ON_ERROR_STOP=1 \
        -f "/tmp/${base}" 2>&1 | tee -a "${WORK_DIR}/${base}.log"
    local rc=${PIPESTATUS[0]}
    [ "${rc}" -eq 0 ] || die "SQL 適用に失敗: ${f} (ログ: ${WORK_DIR}/${base}.log)"
    log "done : ${f}"
}

mkdir -p "${WORK_DIR}"

# ---------------------------------------------------------------- check
step_check() {
    log "=== 3章 事前調査 ==="
    log "compose  : ${COMPOSE}"
    log "work dir : ${WORK_DIR}"

    log "--- 3-1 現在のリビジョン ---"
    git rev-parse --abbrev-ref HEAD | tee -a "${WORK_DIR}/upgrade.log"
    git rev-parse HEAD              | tee -a "${WORK_DIR}/upgrade.log"

    log "--- 3-2 制限公開プロパティ ID の候補 ---"
    psql_show "SELECT id, name FROM item_type_property
               WHERE schema::text LIKE '%termsDescription%' ORDER BY id;" \
        | tee -a "${WORK_DIR}/upgrade.log"
    log "  -> RESTRICTED_ACCESS_PROPERTY の現在値: ${RESTRICTED_ACCESS_PROPERTY}"

    log "--- 3-3 未適用パッチの判定 ---"
    local erad_r aid aff_ror rec_name ro_col
    erad_r=$(psql_count "SELECT count(*) FROM authors_prefix_settings WHERE scheme='e-Rad_Researcher';")
    aid=$(psql_count "SELECT count(*) FROM authors_prefix_settings WHERE scheme='AID';")
    aff_ror=$(psql_count "SELECT count(*) FROM authors_affiliation_settings WHERE scheme='ROR';")
    rec_name=$(psql_count "SELECT count(*) FROM item_type WHERE schema::text LIKE '%subitem_record_name%';")
    ro_col=$(psql_count "SELECT count(*) FROM information_schema.columns
                     WHERE table_name='files_location' AND column_name LIKE 'readonly%';")

    log "  prefix 'e-Rad_Researcher'          : ${erad_r}"
    log "  prefix 'AID'                       : ${aid}"
    log "  affiliation 'ROR'                  : ${aff_ror}"
    log "    -> いずれかが 0 なら v1_0_7a2.sql を適用"
    log "    ※ prefix の 'ROR' は v1.0.7 の初期データに元から存在するため判定に使わない"
    log "    ※ 'e-Rad' は v1.0.7 の初期データに無く、v1.0.7b.sql は構文エラーのため適用しない"
    log "  item_type に subitem_record_name   : ${rec_name}  (>0 なら fix_issue45092.sql を適用)"
    log "  files_location の readonly* 列     : ${ro_col}    (0 かつ S3 利用なら 61660.sql を適用)"
    log "  ※ fix_itemtype_issue_45614.sql は新規構築機関向け。移行機関は適用しないこと"

    log "--- 参考: 現在の authors_prefix / affiliation ---"
    psql_show "SELECT scheme FROM authors_prefix_settings ORDER BY id;" \
        | tee -a "${WORK_DIR}/upgrade.log"
    psql_show "SELECT scheme FROM authors_affiliation_settings ORDER BY id;" \
        | tee -a "${WORK_DIR}/upgrade.log"

    log "--- 3-4 instance.cfg の差分抽出 ---"
    cp scripts/instance.cfg "${WORK_DIR}/instance.cfg.current"
    ${COMPOSE} exec -T web cat /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg \
        > "${WORK_DIR}/invenio.cfg.current" 2>/dev/null \
        || log "  (web コンテナ停止中のため invenio.cfg は取得できませんでした)"
    git show "${TARGET_TAG}:scripts/instance.cfg" > "${WORK_DIR}/instance.cfg.${TARGET_TAG}" 2>/dev/null \
        || log "  (${TARGET_TAG} が取得できません。git fetch origin --tags を実行してください)"
    if [ -s "${WORK_DIR}/instance.cfg.${TARGET_TAG}" ]; then
        diff -u "${WORK_DIR}/instance.cfg.current" "${WORK_DIR}/instance.cfg.${TARGET_TAG}" \
            > "${WORK_DIR}/instance.cfg.diff" ; :
        log "  差分: ${WORK_DIR}/instance.cfg.diff"
        if grep -q 'S3_SECRECT_ACCESS_KEY' "${WORK_DIR}/instance.cfg.current"; then
            log "  !! S3_SECRECT_ACCESS_KEY を検出。v2.0.3 では S3_SECRET_ACCESS_KEY にリネームされています"
        fi
    fi

    log "--- 3-5 データ量 ---"
    psql_show "SELECT (SELECT count(*) FROM records_metadata) AS records,
                      (SELECT count(*) FROM item_metadata)   AS items,
                      (SELECT count(*) FROM item_type)       AS item_types,
                      (SELECT count(*) FROM authors)         AS authors;" \
        | tee -a "${WORK_DIR}/upgrade.log"

    log "=== check 完了。結果は ${WORK_DIR} を参照 ==="
}

# ---------------------------------------------------------------- backup
step_backup() {
    log "=== 5章 バックアップ ==="
    local dump="${WORK_DIR}/invenio_$(date +%Y%m%d%H%M).dump"
    log "pg_dump -> ${dump}"
    ${COMPOSE} exec -T postgresql pg_dump -U invenio -d invenio -Fc > "${dump}" \
        || die "pg_dump に失敗しました"
    ls -lh "${dump}" | tee -a "${WORK_DIR}/upgrade.log"

    cp scripts/instance.cfg "${WORK_DIR}/instance.cfg.bak"
    ${COMPOSE} exec -T web cat /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg \
        > "${WORK_DIR}/invenio.cfg.bak" 2>/dev/null || true
    docker volume ls | tee -a "${WORK_DIR}/upgrade.log"
    log "=== backup 完了 ==="
}

# ---------------------------------------------------------------- config
step_config() {
    log "=== 6-3 instance.cfg の制限公開フラグ設定 ==="
    local f=scripts/instance.cfg
    [ -f "${f}" ] || die "${f} が見つかりません"
    cp "${f}" "${f}.$(date +%Y%m%d%H%M).bak"

    set_flag() {   # set_flag <KEY> <VALUE>
        local key="$1" val="$2"
        if grep -qE "^${key} *= *" "${f}"; then
            sed -i -E "s|^${key} *= *.*$|${key} = ${val}|" "${f}"
            log "  update: ${key} = ${val}"
        else
            echo "${key} = ${val}" >> "${f}"
            log "  append: ${key} = ${val}"
        fi
    }

    set_flag WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG  True
    set_flag WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS     True
    set_flag WEKO_RECORDS_UI_RESTRICTED_API             True
    set_flag WEKO_ITEMS_UI_PROXY_POSTING                True
    set_flag WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED    True
    set_flag WEKO_INDEX_TREE_SHOW_MODAL                 True
    set_flag WEKO_USERPROFILES_CUSTOMIZE_ENABLED        True
    set_flag INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED True

    if grep -q 'S3_SECRECT_ACCESS_KEY' "${f}"; then
        log "  !! S3_SECRECT_ACCESS_KEY が残っています。S3_SECRET_ACCESS_KEY へ手で移してください"
    fi
    log "  機関固有のカスタマイズは ${WORK_DIR}/instance.cfg.diff を見て手でマージすること"
    log "=== config 完了 ==="
}

# ---------------------------------------------------------------- build
step_build() {
    log "=== 6-4 イメージビルド ==="
    git rev-parse --abbrev-ref HEAD | tee -a "${WORK_DIR}/upgrade.log"
    confirm "現在のブランチで ${COMPOSE} down してビルドします。よろしいですか"

    ${COMPOSE} down || die "down に失敗しました"
    DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 ${COMPOSE} build --no-cache --force-rm 2>&1 \
        | tee -a "${WORK_DIR}/build.log"
    [ "${PIPESTATUS[0]}" -eq 0 ] || die "ビルドに失敗しました (ログ: ${WORK_DIR}/build.log)"

    log "--- postgresql のみ起動 ---"
    ${COMPOSE} up -d postgresql || die "postgresql の起動に失敗しました"
    for i in $(seq 1 30); do
        ${COMPOSE} exec -T postgresql pg_isready -U invenio >/dev/null 2>&1 && break
        sleep 2
    done
    ${COMPOSE} exec -T postgresql pg_isready -U invenio || die "postgresql が起動しません"
    log "=== build 完了 ==="
}

# ---------------------------------------------------------------- migrate
step_migrate() {
    log "=== 7章 DB マイグレーション ==="

    local erad_r aid aff_ror rec_name ro_col
    erad_r=$(psql_count   "SELECT count(*) FROM authors_prefix_settings WHERE scheme='e-Rad_Researcher';")
    aid=$(psql_count      "SELECT count(*) FROM authors_prefix_settings WHERE scheme='AID';")
    aff_ror=$(psql_count  "SELECT count(*) FROM authors_affiliation_settings WHERE scheme='ROR';")
    rec_name=$(psql_count "SELECT count(*) FROM item_type WHERE schema::text LIKE '%subitem_record_name%';")
    ro_col=$(psql_count   "SELECT count(*) FROM information_schema.columns
                       WHERE table_name='files_location' AND column_name LIKE 'readonly%';")

    local a2="${APPLY_V1_0_7A2:-}" f45="${APPLY_FIX45092:-}" s3="${APPLY_61660:-}"
    if [ -z "${a2}" ]; then
        # prefix の e-Rad_Researcher / AID、affiliation の ROR が W2025-29.sql で未カバー
        if [ "${erad_r}" -eq 0 ] || [ "${aid}" -eq 0 ] || [ "${aff_ror}" -eq 0 ]; then
            a2=yes
        else
            a2=no
        fi
    fi
    [ -n "${f45}" ] || { [ "${rec_name}" -gt 0 ] && f45=yes || f45=no ; }
    [ -n "${s3}" ]  || { s3=no ; }   # S3 利用時のみ明示指定

    log "--- 7-1 未適用パッチ ---"
    log "  v1_0_7a2.sql       : ${a2}   (e-Rad_Researcher=${erad_r} AID=${aid} affiliation ROR=${aff_ror})"
    log "  fix_issue45092.sql : ${f45}  (subitem_record_name=${rec_name})"
    log "  61660.sql          : ${s3}   (S3 利用時のみ APPLY_61660=yes を指定。readonly列=${ro_col})"
    log "  ※ v1.0.7b.sql は構文エラーかつ対象0件のため適用しない"
    confirm "上記の判定で進めます。よろしいですか"

    [ "${a2}"  = yes ] && apply_sql postgresql/update/v1_0_7a2.sql
    [ "${f45}" = yes ] && apply_sql postgresql/update/fix_issue45092.sql
    [ "${s3}"  = yes ] && [ "${ro_col}" -eq 0 ] && apply_sql postgresql/ddl/61660.sql

    log "--- 7-2 W2025-29.sql ---"
    log "  単一トランザクションです。時間がかかります"
    apply_sql postgresql/ddl/W2025-29.sql

    if grep -q 'End execution: Migration W2025-29.sql' "${WORK_DIR}/W2025-29.sql.log"; then
        log "  OK: 'End execution: Migration W2025-29.sql' を確認"
    else
        die "W2025-29.sql が最後まで到達していません (ログ: ${WORK_DIR}/W2025-29.sql.log)"
    fi
    grep -iE '^(ERROR|FATAL)' "${WORK_DIR}/W2025-29.sql.log" && die "W2025-29.sql にエラーがあります"
    log "=== migrate 完了。verify を実行して確認してください ==="
}

# ---------------------------------------------------------------- data
step_data() {
    log "=== 8-1〜8-3 データマイグレーション ==="
    log "--- 全サービス起動 ---"
    ${COMPOSE} up -d || die "起動に失敗しました"
    ${COMPOSE} ps | tee -a "${WORK_DIR}/upgrade.log"
    log "  inbox / mongo が Up であることを確認してください"

    log "--- 8-2 update_W2025-29.py ---"
    log "  RESTRICTED_ACCESS_PROPERTY=${RESTRICTED_ACCESS_PROPERTY} BATCH_SIZE=${BATCH_SIZE}"
    confirm "update_W2025-29.py を実行します。よろしいですか"

    ${COMPOSE} exec -T web invenio shell scripts/demo/update_W2025-29.py \
        "${RESTRICTED_ACCESS_PROPERTY}" "${BATCH_SIZE}" 2>&1 \
        | tee "${WORK_DIR}/update_W2025-29.log"

    # main() は例外を握り潰すため、終了コードではなくログで判定する
    if grep -q 'All updates completed successfully' "${WORK_DIR}/update_W2025-29.log"; then
        log "  OK: All updates completed successfully"
    else
        log "  !! 'All updates completed successfully' が出力されていません"
        grep -iE 'error|traceback|not found' "${WORK_DIR}/update_W2025-29.log" | head -40
        die "update_W2025-29.py が正常終了していません (ログ: ${WORK_DIR}/update_W2025-29.log)"
    fi

    log "=== data 完了。次は reindex を実行してください ==="
}

# ---------------------------------------------------------------- assets
step_assets() {
    log "=== 8-6 静的リソースの再生成 ==="
    ${COMPOSE} exec -T web invenio assets build 2>&1 | tee -a "${WORK_DIR}/assets.log"
    ${COMPOSE} exec -T web invenio collect -v    2>&1 | tee -a "${WORK_DIR}/assets.log"
    ${COMPOSE} exec -T web bash -c \
        "jinja2 /code/scripts/instance.cfg > /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg" \
        || die "invenio.cfg の生成に失敗しました"
    ${COMPOSE} restart web worker
    log "=== assets 完了 ==="
}

# ---------------------------------------------------------------- reindex
step_reindex() {
    log "=== 8-3〜8-5 ES マッピング更新と再インデックス ==="

    log "--- 8-3 著者インデックスへの communityIds 追加 ---"
    # 実インデックス名は <SEARCH_INDEX_PREFIX>-authors-author-v1.0.0
    # (WEKO_AUTHORS_ES_INDEX_NAME = "<prefix>-authors" はエイリアス)
    local authors_index
    authors_index=$(${COMPOSE} exec -T elasticsearch \
        curl -s "http://localhost:9200/_cat/indices/*authors*?h=index" 2>/dev/null \
        | tr -d '\r' | grep -v '^$' | head -1)
    if [ -z "${authors_index}" ] && [ -n "${SEARCH_INDEX_PREFIX:-}" ]; then
        authors_index="${SEARCH_INDEX_PREFIX}-authors-author-v1.0.0"
    fi
    [ -n "${authors_index}" ] || die "著者インデックスが見つかりません。手動で実施してください"
    log "  authors index: ${authors_index}"

    ${COMPOSE} exec -T elasticsearch curl -s -XPUT \
        "http://localhost:9200/${authors_index}/_mapping/author-v1.0.0?pretty" \
        -H 'Content-Type: application/json' \
        -d '{"properties":{"communityIds":{"type":"keyword"}}}' \
        2>&1 | tee -a "${WORK_DIR}/es_mapping.log"

    if ${COMPOSE} exec -T elasticsearch \
        curl -s "http://localhost:9200/${authors_index}/_mapping" | grep -q communityIds; then
        log "  OK: communityIds を確認"
    else
        die "communityIds のマッピング追加に失敗しました"
    fi

    log "--- 8-4 dynamic mapping timeout を 600s に変更 ---"
    ${COMPOSE} exec -T elasticsearch curl -s -XPUT \
        "http://localhost:9200/_cluster/settings" \
        -H 'Content-Type: application/json' \
        -d '{"persistent": {"indices.mapping.dynamic_timeout": "600s"}}' \
        2>&1 | tee -a "${WORK_DIR}/es_mapping.log"

    log "--- 8-5 再インデックス ---"
    log "  ※ invenio index destroy は実行しないこと(統計インデックスが失われます)"
    confirm "全件再インデックスを開始します。よろしいですか"

    ${COMPOSE} exec -T web invenio index reindex --pid-type recid --yes-i-know 2>&1 \
        | tee "${WORK_DIR}/reindex.log"
    ${COMPOSE} exec -T web invenio index run \
        --raise-on-error False --chunk-size "${REINDEX_CHUNK_SIZE}" 2>&1 \
        | tee -a "${WORK_DIR}/reindex.log"
    ${COMPOSE} exec -T web invenio authors reindex --yes-i-know 2>&1 \
        | tee "${WORK_DIR}/reindex_authors.log"

    ${COMPOSE} exec -T elasticsearch curl -s "http://localhost:9200/_cluster/health?pretty" \
        | tee -a "${WORK_DIR}/reindex.log"
    log "=== reindex 完了。次は assets を実行してください ==="
}

# ---------------------------------------------------------------- verify
step_verify() {
    log "=== 7-3 / 9章 機械的確認 ==="

    log "--- v2.0 で追加されるテーブル ---"
    psql_show "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN
      ('mail_templates','mail_template_genres','mail_template_users','jsonld_mappings',
       'oa_status','user_activity_logs','notifications_user_settings','sword_clients',
       'workspace_default_conditions','workspace_status_management',
       'author_community_relations','file_onetime_download','file_secret_download')
      ORDER BY tablename;" | tee -a "${WORK_DIR}/verify.log"

    log "--- records_metadata の変換 ---"
    local old new
    old=$(psql_count "SELECT count(*) FROM records_metadata WHERE json ? 'weko_shared_id';")
    new=$(psql_count "SELECT count(*) FROM records_metadata WHERE json ? 'owners';")
    log "  weko_shared_id が残っている件数: ${old}  (0 であること)"
    log "  owners を持つ件数              : ${new}"
    [ "${old}" -eq 0 ] || log "  !! weko_shared_id -> weko_shared_ids の変換が未完了です"

    log "--- 監査ログのパーティション ---"
    psql_show "SELECT tablename FROM pg_tables WHERE tablename LIKE 'user_activity_logs_%'
               ORDER BY 1;" | tee -a "${WORK_DIR}/verify.log"

    log "--- 制限公開プロパティ ---"
    psql_show "SELECT id, name FROM item_type_property WHERE id=${RESTRICTED_ACCESS_PROPERTY};" \
        | tee -a "${WORK_DIR}/verify.log"

    log "--- authors_prefix_settings ---"
    psql_show "SELECT scheme FROM authors_prefix_settings ORDER BY id;" \
        | tee -a "${WORK_DIR}/verify.log"

    log "--- 件数照合 (DB / ES) ---"
    psql_q "SELECT count(*) FROM pidstore_pid WHERE pid_type='recid' AND status='R';" \
        | tee -a "${WORK_DIR}/verify.log"
    ${COMPOSE} exec -T elasticsearch curl -s "http://localhost:9200/_cat/indices?v" \
        | tee -a "${WORK_DIR}/verify.log"

    log "--- コンテナのログ ---"
    ${COMPOSE} logs --tail=50 web worker 2>&1 | grep -iE 'error|traceback' | head -30 \
        | tee -a "${WORK_DIR}/verify.log"

    log "=== verify 完了。手動チェックは手順書 9章 を参照 ==="
}

case "${1:-}" in
    check)   step_check ;;
    backup)  step_backup ;;
    config)  step_config ;;
    build)   step_build ;;
    migrate) step_migrate ;;
    data)    step_data ;;
    reindex) step_reindex ;;
    assets)  step_assets ;;
    verify)  step_verify ;;
    *)
        sed -n '2,33p' "$0"
        exit 1
        ;;
esac
