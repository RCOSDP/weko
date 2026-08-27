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

# backup.sh で退避した状態に戻す。
#
#   ./scripts/demo/restore.sh              既定の置き場所から
#   ./scripts/demo/restore.sh <ディレクトリ>  別の場所から
#
# ★現在のデータは失われる。
# ★別バージョンのコードへ戻したときは、続けて alembic を上げること。
#     docker compose exec web invenio alembic upgrade

# quit on errors and unbound symbols:
set -o errexit
set -o nounset

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
SRC="${1:-$HERE}"

export COMPOSE_IGNORE_ORPHANS=1
if docker compose version >/dev/null 2>&1; then
  DC="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
else
  echo "docker compose が見つかりません" >&2; exit 1
fi
cd "$ROOT"
SRC="$(cd "$SRC" && pwd)"

for d in postgresql elasticsearch contents; do
  [ -d "$SRC/$d" ] || { echo "$SRC/$d がありません。backup.sh を先に実行してください" >&2; exit 1; }
done

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

echo "復元元: $SRC"
if [ -f "$SRC/manifest.json" ]; then
  python3 -c "import json,sys;m=json.load(open(sys.argv[1]));print('  rev=%s  作成=%s'%(m.get('weko_rev'),m.get('created')))" "$SRC/manifest.json"
fi
echo "★ 現在のデータは失われます。"

# create-database-begin
echo "[1/3] PostgreSQL を作り直す"
docker exec "$(cid web)" bash -lc \
    'source ~/.virtualenvs/invenio/bin/activate; cd /code; invenio db drop --yes-i-know; invenio db init; invenio db create -v'
# create-database-end

# postgresql-restore-begin
docker cp "$SRC/postgresql/weko.sql" "$(cid postgresql):/weko.sql"
docker exec "$(cid postgresql)" psql -q -U invenio -d invenio -f /weko.sql
# postgresql-restore-end

# elasticsearch-restore-begin
echo "[2/3] Elasticsearch"
ES="$(cid elasticsearch)"
docker exec "$ES" curl -s -o /dev/null -X DELETE "http://localhost:9200/*" || true
docker cp "$SRC/elasticsearch/backups/." "$ES:/usr/share/elasticsearch/backups"
# docker cp はホスト側の所有者を持ち込むので戻す
docker exec -u root "$ES" chown -R elasticsearch:elasticsearch \
    /usr/share/elasticsearch/backups
docker exec "$ES" curl -s -o /dev/null -X PUT \
    "http://localhost:9200/_snapshot/weko_backup" \
    -H 'content-type: application/json' \
    -d '{"type":"fs","settings":{"location":"/usr/share/elasticsearch/backups"}}'
docker exec "$ES" curl -s -o /dev/null -X POST \
    "http://localhost:9200/_snapshot/weko_backup/snapshot_all/_restore?wait_for_completion=true"
# elasticsearch-restore-end

# contents-restore-begin
echo "[3/3] ファイル実体"
# sudo での chown は不要。docker cp でコンテナへ直接戻す。
docker cp "$SRC/contents/tmp/." "$(cid web):/var/tmp"
# contents-restore-end

echo "[4/4] web を再起動"
docker restart "$(cid web)" >/dev/null

echo ""
echo "完了。"
echo "※ 退避時と別バージョンのコードで動かす場合は、続けて実行すること:"
echo "     $DC exec web invenio alembic upgrade"
