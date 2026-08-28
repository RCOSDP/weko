#!/usr/bin/env bash
#
# feature/jgss-pre -> v2.0.3 アップデート補助スクリプト（docker-compose 版）
#
# 起点は v0.9.21 相当（+ W2023-21/22/23 + JGSS カスタマイズ）である。
# 手順書: weko-document/docs/operation/jgss-pre_to_v2.0.3.md
#
#   check     4章    段階1〜7の未適用判定（DB を更新しない）
#   backup    6章    DB/設定のバックアップ
#   config    7-3    制限公開フラグ + JGSS節のコメント解除
#   build     7-6,7-7 ビルド + postgresql 起動
#   stage1    8-1    v0.9.22相当  pr873 / pr1025 / pr1274 / fix_issue_37699（冪等版）
#   stage2    8-2    v0.9.26相当  sp65〜sp72 / v0.9.15_search_management（不足分を一覧表示）
#   stage3    8-3    v0.9.27相当  v0.9.27.sql -> SELECT update_v0927()
#   stage4    8-4    v1.0.6相当   update_jpcoar_2_0.py only_specified / register_oai_schema
#   stage5    8-5    v1.0.7a2相当 v1_0_7a2.sql
#   stage6    8-6    v2.0.0相当   fix_issue45092.sql -> W2025-29.sql
#   stage7    8-7    v2.0.3相当   61660.sql（S3利用時）
#   data      9-1,9-2 起動 + update_W2025-29.py
#   reindex   9-3〜9-5 mapping + timeout + reindex
#   assets    9-6    assets build / collect
#   verify    8-8/10章 の機械的確認
#
# 環境変数:
#   WEKO_DIR / COMPOSE / WORK_DIR / PGUSER / PGDB / BATCH_SIZE / USAGE_REPORT_NAME
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEKO_DIR="${WEKO_DIR:-$(cd "${SCRIPT_DIR}/.." && pwd)}"
COMPOSE="${COMPOSE:-docker compose -f docker-compose2.yml}"
WORK_DIR="${WORK_DIR:-${WEKO_DIR}/upgrade_work}"
PGUSER="${PGUSER:-invenio}"
PGDB="${PGDB:-invenio}"
BATCH_SIZE="${BATCH_SIZE:-500}"
DECISIONS="${WORK_DIR}/decisions.env"

mkdir -p "${WORK_DIR}"
cd "${WEKO_DIR}"

log()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*" | tee -a "${WORK_DIR}/upgrade.log" ; }
info() { printf '    %s\n' "$*" | tee -a "${WORK_DIR}/upgrade.log" ; }
warn() { printf '\033[1;33m[WARN] %s\033[0m\n' "$*" | tee -a "${WORK_DIR}/upgrade.log" ; }
die()  { printf '\033[1;31m[FAIL] %s\033[0m\n' "$*" | tee -a "${WORK_DIR}/upgrade.log" >&2 ; exit 1 ; }

dc()   { ${COMPOSE} "$@" ; }
q()    { dc exec -T postgresql psql -U "${PGUSER}" -d "${PGDB}" -qtAX -c "$1" | tr -d '\r' ; }
qt()   { dc exec -T postgresql psql -U "${PGUSER}" -d "${PGDB}" -c "$1" ; }
qf()   {
  local f="$1" name; name="$(basename "$f")"
  [ -f "$f" ] || die "SQL が見つからない: $f"
  docker cp "$f" "$(dc ps -q postgresql)":/tmp/"${name}"
  dc exec -T postgresql psql -U "${PGUSER}" -d "${PGDB}" -v ON_ERROR_STOP=1 -f /tmp/"${name}" \
    2>&1 | tee "${WORK_DIR}/${name}.log"
}
dump_stage() {
  local tag="$1"
  log "段階前ダンプ: ${WORK_DIR}/pre_${tag}.dump"
  dc exec -T postgresql pg_dump -U "${PGUSER}" -d "${PGDB}" -Fc > "${WORK_DIR}/pre_${tag}.dump"
}
require_decisions() {
  [ -f "${DECISIONS}" ] || die "先に 'check' を実行すること（${DECISIONS} が無い）"
  # shellcheck disable=SC1090
  . "${DECISIONS}"
}

# ================================================================= 4章 check
step_check() {
  log "4章 事前調査（DB は更新しない）"
  git rev-parse --abbrev-ref HEAD | tee "${WORK_DIR}/current_branch.txt"
  git rev-parse HEAD              | tee "${WORK_DIR}/current_revision.txt"

  # ---------------- 段階 1: v0.9.22 相当
  log "段階1 v0.9.22相当（pr873 / pr1025 / pr1274 / fix_issue_37699）"
  local facet files_cols wac esettings mailhost eppn
  facet="$(q "SELECT count(*) FROM information_schema.columns
              WHERE table_name='facet_search_setting'
                AND column_name IN ('is_open','ui_type','display_number');")"
  files_cols="$(q "SELECT count(*) FROM information_schema.columns
                   WHERE table_name='files_location'
                     AND column_name IN ('s3_endpoint_url','s3_send_file_directly');")"
  wac="$(q "SELECT count(*) FROM information_schema.tables
            WHERE table_schema='public' AND table_name='workflow_activity_count';")"
  esettings="$(q "SELECT count(*) FROM admin_settings WHERE name='elastic_reindex_settings';")"
  mailhost="$(q "SELECT count(*) FROM information_schema.columns
                 WHERE table_name='mail_config' AND column_name='mail_local_hostname';")"
  eppn="$(q "SELECT COALESCE(character_maximum_length,0) FROM information_schema.columns
             WHERE table_name='shibboleth_user' AND column_name='shib_eppn';")"
  info "facet_search_setting 追加列=${facet}/3  files_location 追加列=${files_cols}/2"
  info "workflow_activity_count=${wac}/1  elastic_reindex_settings=${esettings}"
  info "mail_config.mail_local_hostname=${mailhost}/1  shib_eppn 桁=${eppn}（期待 2310）"
  local s1=no
  if [ "${facet}" != "3" ] || [ "${files_cols}" != "2" ] || [ "${wac}" != "1" ] \
     || [ "${esettings}" = "0" ] || [ "${mailhost}" != "1" ] \
     || { [ "${eppn}" != "0" ] && [ "${eppn}" -lt 2310 ] ; }; then s1=yes; fi
  info "=> 段階1: ${s1}"

  local authors_str aj=no
  authors_str="$(q "SELECT count(*) FROM authors WHERE jsonb_typeof(json)='string';")"
  if [ "${authors_str}" != "0" ]; then aj=yes; fi
  info "authors.json 二重エンコード=${authors_str} => 修復: ${aj}"

  # ---------------- 段階 2: v0.9.26 相当
  log "段階2 v0.9.26相当（sp65〜sp72 / v0.9.15_search_management）"
  local missing2=""
  chk_tbl() { [ "$(q "SELECT count(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='$1';")" = "1" ] ; }
  chk_col() { [ "$(q "SELECT count(*) FROM information_schema.columns WHERE table_name='$1' AND column_name='$2';")" = "1" ] ; }
  chk_tbl authors_affiliation_settings || missing2="${missing2} sp72-CreateAuthersAffiliation"
  chk_tbl resync_indexes               || missing2="${missing2} sp70-resync"
  chk_col workflow_activity location_id || missing2="${missing2} sp70-workflow_location"
  chk_tbl oaiserver_set                || missing2="${missing2} sp71-oaiset"
  chk_tbl index_style                  || missing2="${missing2} sp70-enhancedSiteInformationScreen"
  local s2=no
  if [ -n "${missing2}" ]; then s2=yes; warn "不足の可能性:${missing2}"; else info "不足なし"; fi
  info "=> 段階2: ${s2}"

  # ---------------- 段階 3: v0.9.27 相当
  log "段階3 v0.9.27相当（v0.9.27.sql）"
  local old_subitem old_prop s3=no
  old_subitem="$(q "SELECT count(*) FROM item_type WHERE schema::text LIKE '%subitem_1587693279322%';")"
  old_prop="$(q "SELECT count(*) FROM item_type_property WHERE id IN (121,122,124,132);")"
  info "旧 subitem 残存 item_type=${old_subitem}  旧プロパティ(121/122/124/132)=${old_prop}"
  if [ "${old_subitem}" != "0" ] || [ "${old_prop}" != "0" ]; then s3=yes; fi
  info "=> 段階3: ${s3}"
  if [ "${s3}" = "yes" ]; then warn "update_v0927() はプロパティ削除とメタデータ一括置換を行う。手順書 12章 の 3 を確認すること"; fi

  # ---------------- 段階 4: v1.0.6 相当（JPCOAR 2.0）
  log "段階4 v1.0.6相当（JPCOAR 2.0）"
  local jp_prop jp_schema s4=no
  jp_prop="$(q "SELECT count(*) FROM item_type_property
                WHERE name IN ('カタログ','データセットシリーズ','保持者','フォーマット','大きさ',
                               '原文の言語','巻号年月次','版','日付（リテラル）','出版者情報');")"
  jp_schema="$(q "SELECT count(*) FROM oaiserver_schema WHERE schema_name='jpcoar_v2_mapping';")"
  info "JPCOAR2.0 プロパティ=${jp_prop}  jpcoar_v2_mapping スキーマ=${jp_schema}"
  if [ "${jp_prop}" = "0" ] || [ "${jp_schema}" = "0" ]; then s4=yes; fi
  info "=> 段階4: ${s4}"

  # ---------------- 段階 5: v1.0.7a2 相当
  log "段階5 v1.0.7a2相当（v1_0_7a2.sql）"
  qt "SELECT scheme FROM authors_prefix_settings ORDER BY id;"
  qt "SELECT scheme FROM authors_affiliation_settings ORDER BY id;" 2>/dev/null || true
  local erad aid aff_ror s5=no
  erad="$(q "SELECT count(*) FROM authors_prefix_settings WHERE scheme='e-Rad_Researcher';")"
  aid="$(q  "SELECT count(*) FROM authors_prefix_settings WHERE scheme='AID';")"
  aff_ror="$(q "SELECT count(*) FROM authors_affiliation_settings WHERE scheme='ROR';" 2>/dev/null || echo 0)"
  if [ "${erad}" = "0" ] || [ "${aid}" = "0" ] || [ "${aff_ror}" = "0" ]; then s5=yes; fi
  info "e-Rad_Researcher=${erad} AID=${aid} affiliation ROR=${aff_ror} => 段階5: ${s5}"
  info "（prefix 側の ROR は初期データに含まれるため判定に使わない）"

  # ---------------- 段階 6: v2.0.0 相当
  log "段階6 v2.0.0相当（fix_issue45092.sql / W2025-29.sql）"
  local rec_name f45092=no
  rec_name="$(q "SELECT count(*) FROM item_type WHERE schema::text LIKE '%subitem_record_name%';")"
  if [ "${rec_name}" != "0" ]; then f45092=yes; fi
  info "subitem_record_name 残存=${rec_name} => fix_issue45092.sql: ${f45092}"
  info "W2025-29.sql は常に適用する"

  # ---------------- 段階 7: v2.0.3 相当
  log "段階7 v2.0.3相当（61660.sql / S3利用時）"
  local ro s3loc s7=no
  ro="$(q "SELECT count(*) FROM information_schema.columns
           WHERE table_name='files_location' AND column_name LIKE 'readonly%';")"
  s3loc="$(q "SELECT count(*) FROM files_location WHERE type LIKE 's3%';" 2>/dev/null || echo 0)"
  if [ "${ro}" = "0" ] && [ "${s3loc}" != "0" ]; then s7=yes; fi
  info "readonly 列=${ro}  s3 ロケーション=${s3loc} => 段階7: ${s7}"

  # ---------------- 制限公開プロパティ ID
  log "4-4 制限公開プロパティ ID"
  qt "SELECT id, name FROM item_type_property WHERE schema::text LIKE '%termsDescription%' ORDER BY id;"
  local prop propcnt
  prop="$(q "SELECT id FROM item_type_property WHERE schema::text LIKE '%termsDescription%' ORDER BY id LIMIT 1;")"
  propcnt="$(q "SELECT count(*) FROM item_type_property WHERE schema::text LIKE '%termsDescription%';")"
  [ -n "${prop}" ] || { warn "制限公開プロパティが見つからない。既定 30015 を使う"; prop=30015; }
  [ "${propcnt}" = "1" ] || warn "候補が ${propcnt} 件。NII に確認すること"
  info "RESTRICTED_ACCESS_PROPERTY=${prop}"

  # ---------------- アイテムタイプ名
  log "4-5 アイテムタイプ名"
  qt "SELECT itn.id, itn.name, count(it.id) AS versions
        FROM item_type_name itn LEFT JOIN item_type it ON it.name_id = itn.id
       GROUP BY itn.id, itn.name ORDER BY itn.id;"
  local ur1 ur2
  ur1="$(q "SELECT count(*) FROM item_type_name WHERE name='利用報告';")"
  ur2="$(q "SELECT count(*) FROM item_type_name WHERE name='利用報告-Data Usage Report';")"
  if [ "${ur1}" != "0" ]; then
    warn "DB は '利用報告'。config 実行時に USAGE_REPORT_NAME='利用報告' を指定すること"
  elif [ "${ur2}" != "0" ]; then
    info "DB は '利用報告-Data Usage Report'。v2.0.3 既定のままでよい"
  else
    warn "'利用報告' 系のアイテムタイプが見つからない。4-5 を手で確認すること"
  fi

  # ---------------- スキーマ照合用の出力
  log "4-3 スキーマ照合用のカラム一覧を出力"
  q "SELECT table_name||'.'||column_name FROM information_schema.columns
      WHERE table_schema='public' ORDER BY 1;" | sort > "${WORK_DIR}/cols.jgss-pre.txt"
  info "=> ${WORK_DIR}/cols.jgss-pre.txt（$(wc -l < "${WORK_DIR}/cols.jgss-pre.txt") 行）"
  warn "クリーンな v2.0.3 環境で同じクエリを流し cols.v2.0.3.txt を作り、comm -13 で差分を確認すること"

  # ---------------- instance.cfg 差分
  log "4-6 instance.cfg の差分"
  cp scripts/instance.cfg "${WORK_DIR}/instance.cfg.jgss-pre"
  dc exec -T web cat /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg \
    > "${WORK_DIR}/invenio.cfg.current" 2>/dev/null || warn "web から invenio.cfg を取得できなかった"
  git show v2.0.3:scripts/instance.cfg > "${WORK_DIR}/instance.cfg.v2.0.3" \
    || die "v2.0.3 が fetch されていない。git fetch origin --tags を実行すること"
  diff -u "${WORK_DIR}/instance.cfg.jgss-pre" "${WORK_DIR}/instance.cfg.v2.0.3" \
    > "${WORK_DIR}/instance.cfg.diff" || true
  info "=> ${WORK_DIR}/instance.cfg.diff"

  log "4-7 件数"
  qt "SELECT (SELECT count(*) FROM records_metadata) AS records,
             (SELECT count(*) FROM item_metadata)   AS items,
             (SELECT count(*) FROM item_type)       AS item_types,
             (SELECT count(*) FROM authors)         AS authors;"

  cat > "${DECISIONS}" <<EOF
# generated by upgrade_jgss-pre_to_v2.0.3.sh check at $(date -Iseconds)
RESTRICTED_ACCESS_PROPERTY=${prop}
APPLY_STAGE1=${s1}
APPLY_AUTHORS_JSON=${aj}
APPLY_STAGE2=${s2}
STAGE2_MISSING="${missing2# }"
APPLY_STAGE3=${s3}
APPLY_STAGE4=${s4}
APPLY_STAGE5=${s5}
APPLY_FIX45092=${f45092}
APPLY_STAGE7=${s7}
EOF
  log "判定結果: ${DECISIONS}"
  cat "${DECISIONS}"
}

# ================================================================ 6章 backup
step_backup() {
  log "6章 バックアップ"
  local stamp; stamp="$(date +%Y%m%d%H%M)"
  dc exec -T postgresql pg_dump -U "${PGUSER}" -d "${PGDB}" -Fc > "${WORK_DIR}/invenio_${stamp}.dump"
  info "DB: ${WORK_DIR}/invenio_${stamp}.dump ($(du -h "${WORK_DIR}/invenio_${stamp}.dump" | cut -f1))"
  cp scripts/instance.cfg "${WORK_DIR}/instance.cfg.bak"
  dc exec -T web cat /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg \
    > "${WORK_DIR}/invenio.cfg.bak" 2>/dev/null || warn "invenio.cfg を取得できなかった"
  docker volume ls | tee "${WORK_DIR}/volumes.txt"
  warn "コンテンツファイル（volume / S3）のバックアップは別途行うこと"
}

# ================================================================ 7-3 config
set_cfg() {
  local key="$1" val="$2" f="$3"
  if grep -qE "^[[:space:]]*${key}[[:space:]]*=" "$f"; then
    sed -i -E "s|^[[:space:]]*${key}[[:space:]]*=.*|${key} = ${val}|" "$f"
    info "  set  ${key} = ${val}"
  else
    printf '\n%s = %s\n' "${key}" "${val}" >> "$f"
    info "  add  ${key} = ${val}"
  fi
}

step_config() {
  log "7-3 instance.cfg の書き換え"
  local f=scripts/instance.cfg
  [ -f "$f" ] || die "$f が無い"
  local head_rev; head_rev="$(git rev-parse --abbrev-ref HEAD)"
  [ "${head_rev}" = "v2.0.3" ] || warn "現在のブランチは ${head_rev}。7-2 で v2.0.3 をチェックアウトしてから実行すること"
  cp "$f" "${WORK_DIR}/instance.cfg.before_config"

  info "(1) 制限公開フラグ（手順書 3-3）"
  set_cfg WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG  True "$f"
  set_cfg WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS     True "$f"
  set_cfg WEKO_RECORDS_UI_RESTRICTED_API             True "$f"
  set_cfg WEKO_ITEMS_UI_PROXY_POSTING                True "$f"
  set_cfg WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED    True "$f"
  set_cfg WEKO_INDEX_TREE_SHOW_MODAL                 True "$f"
  set_cfg WEKO_USERPROFILES_CUSTOMIZE_ENABLED        True "$f"
  set_cfg INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED True "$f"

  info "(2) 'For JGSS' 節のコメント解除（手順書 3-2 #1,#2）"
  sed -i -E 's|^#--(WEKO_USERPROFILES_FORM_COLUMN)|\1|'          "$f"
  sed -i -E 's|^#--(WEKO_USERPROFILES_ROLE_MAPPING_ENABLED)|\1|' "$f"
  sed -i -E 's|^#--(WEKO_USERPROFILES_ROLE_MAPPING)([^_])|\1\2|' "$f"
  for k in WEKO_USERPROFILES_FORM_COLUMN WEKO_USERPROFILES_ROLE_MAPPING_ENABLED WEKO_USERPROFILES_ROLE_MAPPING; do
    grep -qE "^${k}[[:space:]]*=" "$f" && info "  ok   ${k}" || die "${k} のコメント解除に失敗した"
  done

  if [ -n "${USAGE_REPORT_NAME:-}" ]; then
    info "(3) WEKO_ITEMS_UI_USAGE_REPORT を DB の名称に合わせる"
    set_cfg WEKO_ITEMS_UI_USAGE_REPORT "\"${USAGE_REPORT_NAME}\"" "$f"
  else
    warn "(3) WEKO_ITEMS_UI_USAGE_REPORT は未変更。check の判定に従い USAGE_REPORT_NAME='利用報告' を指定すること"
  fi

  diff -u "${WORK_DIR}/instance.cfg.before_config" "$f" | tee "${WORK_DIR}/instance.cfg.config.diff" || true

  warn "以下は自動化していない。手順書 7-3 に従って手で反映すること:"
  warn "  (4) S3: S3_SECRECT_ACCESS_KEY -> S3_SECRET_ACCESS_KEY / S3_READONLY_* / FILES_REST_LOCATION_TYPE_LIST"
  warn "  (5) docker-compose2.yml の web/worker へ環境変数を追加（手順書 3-5）"
  warn "  (6) Redis Sentinel の値を docker-compose 用（sentinel-1/2/3）へ戻す"
  warn "  (7) WEKO_SITEMAP__ROBOT_TXT の移植"
  warn "  7-4 weko.conf（Shibboleth） / 7-5 uwsgi.ini の harakiri"
}

# ================================================================= 7-6 build
step_build() {
  log "7-6 イメージのビルド"
  DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 ${COMPOSE} build --no-cache --force-rm \
    2>&1 | tee "${WORK_DIR}/build.log"
  log "7-7 postgresql のみ起動"
  dc up -d postgresql
  local i=0
  until dc exec -T postgresql pg_isready -U "${PGUSER}" >/dev/null 2>&1; do
    i=$((i+1)); [ "$i" -gt 60 ] && die "postgresql が起動しない"
    sleep 2
  done
  info "postgresql ready"
}

wait_web() {
  info "web の起動を待つ"
  local i=0
  until dc exec -T web bash -lc 'true' >/dev/null 2>&1; do
    i=$((i+1)); [ "$i" -gt 90 ] && die "web が起動しない"
    sleep 2
  done
}

# ====================================================== 8-1 stage1 (v0.9.22)
step_stage1() {
  require_decisions
  log "8-1 段階1 v0.9.22相当"
  if [ "${APPLY_STAGE1}" != "yes" ] && [ "${APPLY_AUTHORS_JSON}" != "yes" ]; then
    info "check の判定では不要。スキップする"; return 0
  fi
  dump_stage stage1

  if [ "${APPLY_STAGE1}" = "yes" ]; then
    cat > "${WORK_DIR}/stage1_catchup.sql" <<'SQLEOF'
BEGIN;
DO $$
DECLARE
    eppn_len int;
BEGIN
RAISE NOTICE 'Start: stage1 (pr873 / pr1025 / pr1274 / fix_issue_37699)';

-- pr873.sql : facet_search_setting
ALTER TABLE facet_search_setting ADD COLUMN IF NOT EXISTS is_open boolean DEFAULT true NOT NULL;
ALTER TABLE facet_search_setting ADD COLUMN IF NOT EXISTS ui_type character varying(20) DEFAULT 'Editbox' NOT NULL;
ALTER TABLE facet_search_setting ADD COLUMN IF NOT EXISTS display_number integer;
UPDATE facet_search_setting SET ui_type = 'Range' WHERE mapping = 'temporal' AND ui_type <> 'Range';

-- pr1025.sql : files_location
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS s3_endpoint_url varchar(128);
ALTER TABLE files_location ADD COLUMN IF NOT EXISTS s3_send_file_directly boolean NOT NULL DEFAULT true;

-- pr1025.sql : workflow_activity_count
CREATE TABLE IF NOT EXISTS workflow_activity_count (
    status VARCHAR(1) NOT NULL,
    created TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    updated TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    date DATE NOT NULL,
    activity_count INTEGER NOT NULL,
    CONSTRAINT pk_workflow_activity_count PRIMARY KEY (date)
);
INSERT INTO workflow_activity_count (status, created, updated, date, activity_count)
SELECT 'N', now(), now(), CURRENT_DATE,
       (SELECT count(*) FROM workflow_activity a
         WHERE a.created >= CURRENT_DATE AND a.created < CURRENT_DATE + 1)
 WHERE NOT EXISTS (SELECT 1 FROM workflow_activity_count WHERE date = CURRENT_DATE);

-- pr1025.sql : admin_settings
INSERT INTO admin_settings (id, name, settings)
SELECT (SELECT COALESCE(MAX(id), 0) + 1 FROM admin_settings),
       'elastic_reindex_settings', '{"has_errored": false}'
 WHERE NOT EXISTS (SELECT 1 FROM admin_settings WHERE name = 'elastic_reindex_settings');
PERFORM setval('admin_settings_id_seq', (SELECT COALESCE(MAX(id), 1) FROM admin_settings));

-- pr1274.sql / 2023_Q4.sql : mail_config
ALTER TABLE mail_config ADD COLUMN IF NOT EXISTS mail_local_hostname character varying(255) DEFAULT '';

-- fix_issue_37699.sql / 2023_Q4.sql : shibboleth_user.shib_eppn
SELECT character_maximum_length INTO eppn_len FROM information_schema.columns
 WHERE table_name = 'shibboleth_user' AND column_name = 'shib_eppn';
IF eppn_len IS NOT NULL AND eppn_len < 2310 THEN
    ALTER TABLE shibboleth_user ALTER COLUMN shib_eppn TYPE CHARACTER VARYING(2310);
    RAISE NOTICE 'shibboleth_user.shib_eppn: % -> 2310', eppn_len;
ELSE
    RAISE NOTICE 'shibboleth_user.shib_eppn: already %, skipping', eppn_len;
END IF;

RAISE NOTICE 'End: stage1';
END $$;
COMMIT;
SQLEOF
    qf "${WORK_DIR}/stage1_catchup.sql"
    grep -iE 'error|fatal|rollback' "${WORK_DIR}/stage1_catchup.sql.log" \
      && die "段階1 でエラー。${WORK_DIR}/stage1_catchup.sql.log を確認すること" || true
  fi

  if [ "${APPLY_AUTHORS_JSON}" = "yes" ]; then
    log "authors.json の二重エンコード修復"
    dc exec -T postgresql psql -U "${PGUSER}" -d "${PGDB}" -v ON_ERROR_STOP=1 \
      -c "UPDATE authors SET json = (json #>> '{}')::jsonb WHERE jsonb_typeof(json) = 'string';" \
      2>&1 | tee "${WORK_DIR}/authors_json_fix.log"
  fi
}

# ====================================================== 8-2 stage2 (v0.9.26)
step_stage2() {
  require_decisions
  log "8-2 段階2 v0.9.26相当（sp65〜sp72 / v0.9.15_search_management）"
  if [ "${APPLY_STAGE2}" != "yes" ]; then
    info "check の判定では不要。スキップする"; return 0
  fi
  warn "不足の可能性がある SQL: ${STAGE2_MISSING}"
  warn "これらは jgss-pre のツリーに存在し、素の ADD COLUMN のため二重適用でエラーになる。"
  warn "内容を確認したうえで手で適用すること（原典: v0.9.17_to_v0.9.26.md「DBの更新」）:"
  for f in ${STAGE2_MISSING}; do
    if [ -f "postgresql/ddl/${f}.sql" ]; then
      echo "  docker cp postgresql/ddl/${f}.sql \$(${COMPOSE} ps -q postgresql):/tmp/"
      echo "  ${COMPOSE} exec -T postgresql psql -U ${PGUSER} -d ${PGDB} -f /tmp/${f}.sql"
    else
      warn "  postgresql/ddl/${f}.sql が見つからない"
    fi
  done
  die "段階2 は自動適用しない。上記を実施後、decisions.env の APPLY_STAGE2 を no にして再開すること"
}

# ====================================================== 8-3 stage3 (v0.9.27)
step_stage3() {
  require_decisions
  log "8-3 段階3 v0.9.27相当（v0.9.27.sql -> SELECT update_v0927()）"
  if [ "${APPLY_STAGE3}" != "yes" ]; then
    info "check の判定では不要。スキップする"; return 0
  fi
  warn "プロパティ 121/122/124/132 の削除と records_metadata の一括置換を行う（手順書 12章 の 3）"
  dump_stage stage3
  qf postgresql/ddl/v0.9.27.sql
  dc exec -T postgresql psql -U "${PGUSER}" -d "${PGDB}" -v ON_ERROR_STOP=1 \
    -c "SELECT update_v0927();" 2>&1 | tee "${WORK_DIR}/update_v0927.log"
  grep -iE 'error|fatal' "${WORK_DIR}/update_v0927.log" && die "update_v0927() でエラー" || true
}

# ================================================ 8-4 stage4 (JPCOAR 2.0)
step_stage4() {
  require_decisions
  log "8-4 段階4 v1.0.6相当（JPCOAR 2.0）"
  if [ "${APPLY_STAGE4}" != "yes" ]; then
    info "check の判定では不要。スキップする"; return 0
  fi
  dump_stage stage4
  dc up -d
  wait_web
  info "W2025-29.sql / update_W2025-29.py はこの処理を内包していない（手順書 8-4 の注記）"
  dc exec -T web invenio shell scripts/demo/update_jpcoar_2_0.py only_specified \
    2>&1 | tee "${WORK_DIR}/update_jpcoar_2_0.log" || true
  grep -iE 'error|traceback' "${WORK_DIR}/update_jpcoar_2_0.log" | head -20 || true
  log "OAI-PMH スキーマの更新"
  dc exec -T web invenio shell scripts/demo/register_oai_schema.py overwrite_all \
    2>&1 | tee "${WORK_DIR}/register_oai_schema.log" || true
  local jp; jp="$(q "SELECT count(*) FROM oaiserver_schema WHERE schema_name='jpcoar_v2_mapping';")"
  [ "${jp}" != "0" ] || die "jpcoar_v2_mapping が登録されていない。${WORK_DIR}/update_jpcoar_2_0.log を確認すること"
  info "jpcoar_v2_mapping: OK"
}

# ==================================================== 8-5 stage5 (v1.0.7a2)
step_stage5() {
  require_decisions
  log "8-5 段階5 v1.0.7a2相当（v1_0_7a2.sql）"
  if [ "${APPLY_STAGE5}" != "yes" ]; then
    info "check の判定では不要。スキップする"; return 0
  fi
  qf postgresql/update/v1_0_7a2.sql
  info "v1.0.7b.sql / fix_itemtype_issue_45614.sql は適用しない（手順書 8-5 の注記）"
}

# ================================================ 8-6 stage6 (W2025-29.sql)
step_stage6() {
  require_decisions
  log "8-6 段階6 v2.0.0相当"
  dump_stage stage6
  if [ "${APPLY_FIX45092}" = "yes" ]; then
    qf postgresql/update/fix_issue45092.sql
  else
    info "fix_issue45092.sql: スキップ"
  fi
  log "W2025-29.sql の適用"
  qf postgresql/ddl/W2025-29.sql
  local lg="${WORK_DIR}/W2025-29.sql.log"
  grep -iE 'error|fatal|rollback' "${lg}" && die "W2025-29.sql でエラー。${lg} を確認すること" || true
  grep -q 'COMMIT' "${lg}" || warn "COMMIT がログに見当たらない。${lg} を確認すること"
  tail -3 "${lg}"
}

# ====================================================== 8-7 stage7 (61660)
step_stage7() {
  require_decisions
  log "8-7 段階7 v2.0.3相当（61660.sql / S3利用時）"
  if [ "${APPLY_STAGE7}" != "yes" ]; then
    info "check の判定では不要（S3 未使用または適用済み）。スキップする"; return 0
  fi
  qf postgresql/ddl/61660.sql
}

# ================================================== 9-1,9-2 data
step_data() {
  require_decisions
  log "9-1 全サービス起動"
  dc up -d
  dc ps | tee "${WORK_DIR}/ps.txt"
  for s in inbox mongo; do
    dc ps "${s}" >/dev/null 2>&1 && info "${s}: 定義あり" || warn "${s} サービスが見つからない（docker-compose2.yml を確認）"
  done
  wait_web

  log "9-2 update_W2025-29.py（prop=${RESTRICTED_ACCESS_PROPERTY} batch=${BATCH_SIZE}）"
  local lg="${WORK_DIR}/update_W2025-29.log"
  dc exec -T web invenio shell scripts/demo/update_W2025-29.py \
    "${RESTRICTED_ACCESS_PROPERTY}" "${BATCH_SIZE}" 2>&1 | tee "${lg}" || true
  # main() は例外を握り潰すので終了コードで判定してはいけない
  grep -q 'All updates completed successfully' "${lg}" \
    || die "'All updates completed successfully.' がログに無い。${lg} を確認すること"
  info "OK: All updates completed successfully"
  grep -iE 'error|traceback|rollback|not found' "${lg}" | head -30 || true
}

# ================================================== 9-3〜9-5 reindex
step_reindex() {
  log "9-3 Elasticsearch マッピングの更新（communityIds）"
  local idx
  idx="$(dc exec -T elasticsearch curl -s "localhost:9200/_cat/indices/*authors*?h=index" \
        | tr -d '\r' | grep -v '^[[:space:]]*$' | head -1)"
  [ -n "${idx}" ] || die "authors インデックスが見つからない"
  info "authors index: ${idx}"
  dc exec -T elasticsearch curl -XPUT \
    "localhost:9200/${idx}/_mapping/author-v1.0.0?pretty" \
    -H "Content-Type: application/json" \
    -d '{"properties":{"communityIds":{"type":"keyword"}}}' 2>&1 | tee "${WORK_DIR}/es_mapping.log"
  dc exec -T elasticsearch curl -s "localhost:9200/${idx}/_mapping?pretty" \
    | grep -q communityIds || die "communityIds のマッピング追加に失敗した"
  info "communityIds: OK"

  log "9-4 dynamic mapping timeout = 600s"
  dc exec -T elasticsearch curl -XPUT localhost:9200/_cluster/settings \
    -H "Content-Type: application/json" \
    -d '{"persistent": {"indices.mapping.dynamic_timeout": "600s"}}' 2>&1 | tee -a "${WORK_DIR}/es_mapping.log"

  log "9-5 再インデックス（invenio index destroy は絶対に実行しないこと）"
  dc exec -T web invenio index reindex --pid-type recid --yes-i-know 2>&1 | tee "${WORK_DIR}/reindex.log"
  dc exec -T web invenio index run --raise-on-error False --chunk-size 50 2>&1 | tee -a "${WORK_DIR}/reindex.log"
  dc exec -T web invenio authors reindex --yes-i-know 2>&1 | tee "${WORK_DIR}/reindex_authors.log"

  log "件数照合"
  info "pidstore_pid(recid,R) = $(q "SELECT count(*) FROM pidstore_pid WHERE pid_type='recid' AND status='R';")"
  dc exec -T elasticsearch curl -s "localhost:9200/_cat/indices?v" | tee "${WORK_DIR}/es_indices.txt"
}

# ================================================================= 9-6 assets
step_assets() {
  log "9-6 静的リソースの再生成"
  dc exec -T web invenio assets build 2>&1 | tee "${WORK_DIR}/assets.log"
  dc exec -T web invenio collect -v    2>&1 | tee -a "${WORK_DIR}/assets.log"
  dc exec -T web bash -c \
    "jinja2 /code/scripts/instance.cfg > /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg"
  dc restart web worker
}

# =================================================================== verify
step_verify() {
  log "8-8 / 10章 機械的確認"

  log "v2.0.3 で追加されるテーブル"
  qt "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename IN
      ('mail_templates','mail_template_genres','mail_template_users','jsonld_mappings',
       'oa_status','user_activity_logs','notifications_user_settings','sword_clients',
       'workspace_default_conditions','workspace_status_management',
       'author_community_relations','file_onetime_download','file_secret_download',
       'workflow_activity_count','authors_affiliation_settings')
     ORDER BY tablename;"

  log "段階1 の適用確認"
  qt "SELECT table_name, column_name FROM information_schema.columns
       WHERE (table_name='facet_search_setting' AND column_name IN ('is_open','ui_type','display_number'))
          OR (table_name='files_location' AND column_name IN ('s3_endpoint_url','s3_send_file_directly'))
          OR (table_name='mail_config' AND column_name='mail_local_hostname')
       ORDER BY table_name, column_name;"
  info "shib_eppn 桁 = $(q "SELECT COALESCE(character_maximum_length,0) FROM information_schema.columns
                            WHERE table_name='shibboleth_user' AND column_name='shib_eppn';")（期待 2310）"

  log "段階3 / 段階4 の適用確認"
  info "旧 subitem 残存        = $(q "SELECT count(*) FROM item_type WHERE schema::text LIKE '%subitem_1587693279322%';")（0 であること）"
  info "旧プロパティ 121/122/124/132 = $(q "SELECT count(*) FROM item_type_property WHERE id IN (121,122,124,132);")（0 であること）"
  info "jpcoar_v2_mapping      = $(q "SELECT count(*) FROM oaiserver_schema WHERE schema_name='jpcoar_v2_mapping';")（1 であること）"

  log "records_metadata の変換確認"
  local shared owners
  shared="$(q "SELECT count(*) FROM records_metadata WHERE json ? 'weko_shared_id';")"
  owners="$(q "SELECT count(*) FROM records_metadata WHERE json ? 'owners';")"
  info "weko_shared_id 残存 = ${shared}（0 であること） / owners あり = ${owners}"
  [ "${shared}" = "0" ] || warn "weko_shared_id が残っている。W2025-29.sql の適用を確認すること"

  log "監査ログのパーティション"
  qt "SELECT tablename FROM pg_tables WHERE tablename LIKE 'user_activity_logs_%' ORDER BY 1;"

  log "JGSS アイテムタイプ"
  qt "SELECT id, name FROM item_type_name ORDER BY id;"

  log "スキーマ照合用のカラム一覧（移行後）"
  q "SELECT table_name||'.'||column_name FROM information_schema.columns
      WHERE table_schema='public' ORDER BY 1;" | sort > "${WORK_DIR}/cols.after.txt"
  if [ -f "${WORK_DIR}/cols.v2.0.3.txt" ]; then
    comm -13 "${WORK_DIR}/cols.after.txt" "${WORK_DIR}/cols.v2.0.3.txt" > "${WORK_DIR}/cols.missing.txt" || true
    local n; n="$(wc -l < "${WORK_DIR}/cols.missing.txt")"
    info "v2.0.3 に有って移行後に無いカラム = ${n} 件"
    [ "${n}" = "0" ] || { warn "不足あり:"; head -30 "${WORK_DIR}/cols.missing.txt"; }
  else
    warn "${WORK_DIR}/cols.v2.0.3.txt が無い。手順書 4-3 の照合を実施すること"
  fi

  log "Elasticsearch"
  dc exec -T elasticsearch curl -s "localhost:9200/_cluster/health?pretty" || true
  dc exec -T elasticsearch curl -s "localhost:9200/_cat/indices?v" || true
  log "統計インデックスの残存（消えていたら復旧不能）"
  dc exec -T elasticsearch curl -s "localhost:9200/_cat/indices/*stats*?h=index" || true

  log "コンテナ状態"
  dc ps
  warn "10章の残りの項目（画面確認）は手で実施すること"
}

usage() {
  sed -n '3,28p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 1
}

case "${1:-}" in
  check)   step_check   ;;
  backup)  step_backup  ;;
  config)  step_config  ;;
  build)   step_build   ;;
  stage1)  step_stage1  ;;
  stage2)  step_stage2  ;;
  stage3)  step_stage3  ;;
  stage4)  step_stage4  ;;
  stage5)  step_stage5  ;;
  stage6)  step_stage6  ;;
  stage7)  step_stage7  ;;
  data)    step_data    ;;
  reindex) step_reindex ;;
  assets)  step_assets  ;;
  verify)  step_verify  ;;
  *)       usage        ;;
esac

log "完了: ${1}"
