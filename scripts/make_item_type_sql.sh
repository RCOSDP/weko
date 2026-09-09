#!/bin/bash
#
# scripts/demo/item_type.sql を作り直す。
#
#     scripts/make_item_type_sql.sh
#
# デモ用アイテムタイプが入った稼働中の WEKO に対して実行すると、
# その内容で scripts/demo/item_type.sql を上書きする。
#
# 【なぜスキーマを含めないか】
# 出力先の SQL は install.sh が populate-instance.sh の**後**に流す。その時点で
# テーブルはモジュールの models.py どおりに作られているので、スキーマを作り直す
# 必要はない。むしろ作り直せない。
#
# 以前はここで pg_dump -c (clean) を使っていたが、-c が出す
#
#     ALTER TABLE ONLY public.item_type DROP CONSTRAINT pk_item_type;
#
# は必ず失敗する。item_type.id は下の TABLES に挙げた表だけでなく、
# workflow_workflow など**ここではダンプしない表**からも参照されており、
# PostgreSQL は「その主キー索引に依存している外部キーがある」として拒否するため。
#
#     ERROR: cannot drop constraint pk_item_type on table item_type
#            because other objects depend on it
#     DETAIL: constraint fk_workflow_workflow_itemtype_id_item_type on table
#             workflow_workflow depends on index pk_item_type
#
# psql は既定で失敗しても続行するので、古いテーブルが残ったまま CREATE TABLE が
# 走って "multiple primary keys for table item_type are not allowed" になり、
# **初期データが入らないまま終了コード 0 で終わる**。UI テストの
# test_import_to_gakunin_rdm_button が落ちていたのはこれが原因だった。
#
# なのでデータだけを出し、既存行は DELETE で消す。
#
# 【順序】
# pg_dump はデータのみのダンプで外部キーの順序を保証しない (表名順に出る)。
# item_type.name_id -> item_type_name のような依存があるため、ここで
# 親 -> 子 の順を明示し、DELETE はその逆順に並べる。全体を1トランザクションに
# 入れ、途中で失敗したら何も入らないようにする。
#
# 【表を増やすとき】
# TABLES に足すだけでよい。位置は親より後、子より前にすること。

set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT"

OUT=scripts/demo/item_type.sql

# 親 -> 子 の順。DELETE はこの逆順で出す。
TABLES=(
  item_type_name
  item_type
  item_type_version
  item_type_mapping
  item_type_mapping_version
  jsonld_mappings
  jsonld_mappings_version
  item_type_property
  oaiserver_schema
  oaiserver_schema_version
)

# 上の表が所有しないが、値を固定したいシーケンス。
#   pidstore_recid_recid_seq  デモのレコード ID を運用データと衝突させない
#   transaction_id_seq        *_version 行が参照する SQLAlchemy-Continuum の採番
EXTRA_SEQUENCES=(
  pidstore_recid_recid_seq
  transaction_id_seq
)

# ID のリザーブ。
#
# これらは「ダンプ元 DB の現在値」ではなく、**予約済みの下限**である。
# デモのアイテムタイプが使う実際の最大 id は 30002 で、40000 はそれを
# 超えて確保した床。運用で作られるデータとデモデータの ID 空間を
# 分けるために置いてある。pidstore_recid_recid_seq に至っては、この
# ダンプは pidstore の行を1件も持たない。
#
# したがって last_value をそのまま書き出してはいけない。リザーブが
# 効いていない DB から再生成すると、予約が黙って失われる。
# 下限を明示し、実際の値と大きい方を採用する。
declare -A RESERVED_SEQUENCES=(
  [item_type_id_seq]=40000
  [item_type_name_id_seq]=40000
  [item_type_mapping_id_seq]=40000
  [item_type_property_id_seq]=40000
  [jsonld_mappings_id_seq]=40000
  [pidstore_recid_recid_seq]=2000000
)

# install.sh と同じ流儀。COMPOSE_FILE が設定済みならそれに従う。
compose_args=()
if [ -z "${COMPOSE_FILE:-}" ]; then
  compose_args=(-f docker-compose2.yml)
fi
dc() { docker compose "${compose_args[@]}" "$@"; }

psql_q() { dc exec -T postgresql psql -U invenio -d invenio -tAq -c "$1"; }

if ! psql_q 'select 1' >/dev/null 2>&1; then
  echo "postgresql コンテナに接続できない。WEKO を起動してから実行すること。" >&2
  exit 1
fi

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

{
  cat <<'HEADER'
--
-- WEKO デモ用アイテムタイプ初期データ
--
-- scripts/make_item_type_sql.sh が生成する。手で編集しないこと。
--
-- 【なぜデータだけなのか】
-- この SQL は install.sh が populate-instance.sh の**後**に流す。その時点で
-- テーブルはモジュールの models.py どおりに作られているので、スキーマを
-- 作り直す必要はない。むしろ作り直せない: item_type.id は
-- item_type_mapping / jsonld_mappings のほかに workflow など、ここでは
-- ダンプしない表からも参照されており、pg_dump -c が出す
--     ALTER TABLE ONLY public.item_type DROP CONSTRAINT pk_item_type;
-- は "other objects depend on it" で必ず失敗する。psql は既定で続行するため、
-- 古いテーブルが残ったまま CREATE TABLE が走って "multiple primary keys" になり、
-- 初期データが入らないまま正常終了してしまう。
--
-- 【順序】
-- pg_dump はデータのみのダンプで外部キーの順序を保証しないので、
-- 親 -> 子 の順に並べてある。削除はその逆順。全体を1トランザクションにして、
-- 途中で失敗したら何も入らないようにしてある。
--
SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

BEGIN;

--
-- 既存データを消す (子 -> 親)
--
HEADER

  for (( i=${#TABLES[@]}-1 ; i>=0 ; i-- )); do
    echo "DELETE FROM public.${TABLES[i]};"
  done
  echo

  for t in "${TABLES[@]}"; do
    dc exec -T postgresql pg_dump -U invenio -d invenio \
        --data-only --column-inserts --no-owner --no-privileges \
        -t "public.$t" > "$tmp"
    n=$(grep -c "^INSERT INTO public\.$t " "$tmp" || true)
    printf -- '--\n-- %s (%s 行)\n--\n' "$t" "$n"
    grep "^INSERT INTO public\.$t " "$tmp" || true
    echo
  done

  echo '--'
  echo '-- シーケンス'
  echo '--'
  # 対象表が所有するシーケンス + 明示指定分。
  # 値は「ダンプ元の last_value」と「RESERVED_SEQUENCES の下限」の大きい方。
  #
  # transaction_id_seq には下限を置かず、ダンプに含めた *_version 行が使う
  # transaction_id の最大値を床にする。これを下回ると、次に
  # SQLAlchemy-Continuum が採番したとき既存の版と衝突する。
  tx_floor=$(
    union=""
    for t in "${TABLES[@]}"; do
      case "$t" in
        *_version)
          if [ -n "$union" ]; then union="$union union all "; fi
          union="${union}select transaction_id from public.$t" ;;
      esac
    done
    if [ -n "$union" ]; then
      psql_q "select coalesce(max(transaction_id), 0) from ($union) v"
    else
      echo 0
    fi
  )

  {
    for t in "${TABLES[@]}"; do
      psql_q "select s.relname
                from pg_class s
                join pg_depend d on d.objid = s.oid and d.deptype = 'a'
                join pg_class t on t.oid = d.refobjid
               where s.relkind = 'S' and t.relname = '$t'"
    done
    printf '%s\n' "${EXTRA_SEQUENCES[@]}"
  } | sort -u | while read -r seq; do
    [ -n "$seq" ] || continue
    last=$(psql_q "select last_value from public.$seq" 2>/dev/null || true)
    [ -n "$last" ] || last=0
    floor=${RESERVED_SEQUENCES[$seq]:-0}
    if [ "$seq" = transaction_id_seq ]; then floor=$tx_floor; fi
    value=$(( last > floor ? last : floor ))
    if [ "$value" -gt "$last" ]; then
      echo "-- ダンプ元は $last。リザーブ下限 $floor を採用する。"
    fi
    echo "SELECT pg_catalog.setval('public.$seq', $value, true);"
  done
  echo

  echo 'COMMIT;'
} > "$OUT"

echo "生成しました: $OUT"
grep -c '^INSERT INTO' "$OUT" | xargs printf '  INSERT %s 行\n'
grep -c '^SELECT pg_catalog.setval' "$OUT" | xargs printf '  setval %s 件\n'
