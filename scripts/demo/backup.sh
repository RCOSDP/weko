#!/usr/bin/env bash
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

# 現在の環境を scripts/demo/ 配下に退避する。
#
#   ./scripts/demo/backup.sh              既定の置き場所へ
#   ./scripts/demo/backup.sh <ディレクトリ>  別の場所へ(複数世代を残したいとき)
#
# 取得するのは3つ。どれか1つでも欠けると復元しても同じ状態にならない。
#   postgresql/   データのみ(alembic_version は除く。スキーマはコードが作る)
#   elasticsearch/ 検索インデックス
#   contents/     ファイル実体(INVENIO_FILES_LOCATION_URI)
#
# 併せて manifest.json に由来(リビジョン・日時)を残す。ダンプは中身を
# 差分で読めないため、いつ・どのコードで取ったかが分からなくなると使えない。

# quit on errors and unbound symbols:
set -o errexit
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
DST="${1:-$HERE}"

# docker compose(v2) と docker-compose(v1) のどちらでも動くようにする
export COMPOSE_IGNORE_ORPHANS=1
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "docker compose が見つかりません" >&2; exit 1
fi
cd "$ROOT"

cid() {  # サービス名からコンテナ名を引く
  # docker compose ps はプロジェクト名/実行ディレクトリに依存して空を返す
  # ことがある。ラベルで探すほうが確実で、他のツール群とも揃う。
  local name
  name="$(docker ps --filter "label=com.docker.compose.service=$1" \
                    --format '{{.Names}}' | head -1)"
  if [ -z "$name" ]; then
    name="$($DC ps -q "$1" 2>/dev/null | head -1)"
  fi
  [ -n "$name" ] || { echo "$1 コンテナが起動していません" >&2; exit 1; }
  printf '%s' "$name"
}

mkdir -p "$DST"
DST="$(cd "$DST" && pwd)"
echo "退避先: $DST"

# delete-old-backup-begin
rm -rf "$DST/contents" "$DST/elasticsearch" "$DST/postgresql"
mkdir -p "$DST/contents" "$DST/elasticsearch" "$DST/postgresql"
# delete-old-backup-end

# postgresql-backup-begin
echo "[1/4] PostgreSQL"
# -T alembic_version: スキーマ管理はコード側に任せ、別バージョンへも
# 流し込めるようにする。復元後に invenio alembic upgrade を回すこと。
docker exec "$(cid postgresql)" \
    pg_dump -U invenio -d invenio -a -T alembic_version -f /weko.sql
docker cp "$(cid postgresql):/weko.sql" "$DST/postgresql/"
# postgresql-backup-end

# elasticsearch-backup-begin
echo "[2/4] Elasticsearch"
ES="$(cid elasticsearch)"
docker exec "$ES" curl -s -o /dev/null -X PUT \
    "http://localhost:9200/_snapshot/weko_backup" \
    -H 'content-type: application/json' \
    -d '{"type":"fs","settings":{"location":"/usr/share/elasticsearch/backups"}}'
# 前回分が無くても失敗しない(初回はここで 404 が返る)
docker exec "$ES" curl -s -o /dev/null -X DELETE \
    "http://localhost:9200/_snapshot/weko_backup/snapshot_all?wait_for_completion=true" || true
docker exec "$ES" curl -s -o /dev/null -X PUT \
    "http://localhost:9200/_snapshot/weko_backup/snapshot_all?wait_for_completion=true"
docker cp "$ES:/usr/share/elasticsearch/backups" "$DST/elasticsearch/"
# elasticsearch-backup-end

# contents-backup-begin
echo "[3/4] ファイル実体"
# コンテナ内から /code へコピーする方式はリポジトリを bind mount して
# いる前提で、所有者もずれる。docker cp でホスト側へ直接取り出す。
docker cp "$(cid web):/var/tmp" "$DST/contents/"
# contents-backup-end

# manifest-begin
echo "[4/4] 由来を記録"
python3 - "$DST" "$ROOT" <<'PY'
import datetime, json, os, subprocess, sys
dst, root = sys.argv[1], sys.argv[2]
def sh(*a):
    try:
        return subprocess.run(a, capture_output=True, text=True, cwd=root).stdout.strip()
    except Exception:
        return ''
m = {
    'created': datetime.datetime.now().isoformat(timespec='seconds'),
    'weko_rev': sh('git', 'rev-parse', '--short', 'HEAD'),
    'weko_describe': sh('git', 'describe', '--tags', '--always'),
    'weko_branch': sh('git', 'rev-parse', '--abbrev-ref', 'HEAD'),
    'weko_dirty': bool(sh('git', 'status', '--porcelain')),
}
inv = os.environ.get('WEKO_API_INVENTORY_DIR')
p = os.path.join(inv, 'fixtures.json') if inv else None
if p and os.path.exists(p):
    d = json.load(open(p, encoding='utf-8'))
    m['fixtures'] = {'index': d.get('index'), 'indexes': d.get('indexes'),
                     'records': {k: v.get('recid')
                                 for k, v in (d.get('records') or {}).items()},
                     'demo': d.get('demo')}
json.dump(m, open(os.path.join(dst, 'manifest.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('  rev=%s%s' % (m['weko_rev'],
                      ' ★未コミットの変更あり' if m['weko_dirty'] else ''))
PY
# manifest-end

echo ""
echo "完了: $(du -sh "$DST" | cut -f1)"
