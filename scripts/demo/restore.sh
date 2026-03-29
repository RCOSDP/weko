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

set -euo pipefail

BACKUP_DIR="./backup"
ES_REPO_NAME="weko_backup"

LATEST_SNAPSHOT="$(find "${BACKUP_DIR}/elasticsearch/backups" -maxdepth 1 -type f -name 'snapshot_*' -printf '%f\n' | sort | tail -n 1)"

if [ -z "${LATEST_SNAPSHOT}" ]; then
    echo "ERROR: no Elasticsearch snapshot found in ${BACKUP_DIR}/elasticsearch/backups" >&2
    exit 1
fi

# create-database-begin
docker compose exec web invenio db drop --yes-i-know
docker compose exec web invenio db init
docker compose exec web invenio db create -v
# create-database-end

# postgresql-restore-begin
docker cp "${BACKUP_DIR}/postgresql/weko.sql" "$(docker compose ps -q postgresql):/tmp/weko.sql"
docker compose exec postgresql psql -U invenio -d invenio -f /tmp/weko.sql
# postgresql-restore-end

# elasticsearch-restore-begin
docker compose stop
docker compose start elasticsearch
sleep 10

docker compose exec elasticsearch \
    curl -fsS -X DELETE "http://localhost:9200/_all"

docker compose exec elasticsearch \
    curl -fsS -X PUT \
    "http://localhost:9200/_snapshot/${ES_REPO_NAME}" \
    -H 'cache-control: no-cache' \
    -H 'content-type: application/json' \
    -d '{
            "type": "fs",
            "settings": {
                "location": "/usr/share/elasticsearch/backups",
                "compress": true
            }
        }'

docker compose exec elasticsearch rm -rf /usr/share/elasticsearch/backups
docker cp "${BACKUP_DIR}/elasticsearch/backups" "$(docker compose ps -q elasticsearch):/usr/share/elasticsearch/"

docker compose exec elasticsearch chown -R elasticsearch:elasticsearch /usr/share/elasticsearch/backups

docker compose exec elasticsearch \
    curl -fsS -X POST \
    "http://localhost:9200/_snapshot/${ES_REPO_NAME}/${LATEST_SNAPSHOT}/_restore" \
    -H 'content-type: application/json' \
    -d '{
            "indices": "*",
            "ignore_unavailable": true,
            "include_global_state": false
        }'

docker compose start
# elasticsearch-restore-end

# contents-restore-begin
docker cp "${BACKUP_DIR}/contents" "$(docker compose ps -q web):/code/backup/"
docker compose exec web mkdir -p /var/tmp
docker compose exec web sh -c 'cp -a /code/backup/contents/. /var/tmp/'
# contents-restore-end
