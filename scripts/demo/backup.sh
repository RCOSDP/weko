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
SNAPSHOT_NAME="snapshot_$(date +%Y%m%d_%H%M%S)"

# delete-old-backup-begin
rm -rf "${BACKUP_DIR}/contents" "${BACKUP_DIR}/elasticsearch" "${BACKUP_DIR}/postgresql"
mkdir -p "${BACKUP_DIR}/contents" "${BACKUP_DIR}/elasticsearch" "${BACKUP_DIR}/postgresql"
# delete-old-backup-end

# postgresql-backup-begin
docker compose exec postgresql pg_dump -U invenio -a -f /tmp/weko.sql -T alembic_version
docker cp "$(docker compose ps -q postgresql):/tmp/weko.sql" "${BACKUP_DIR}/postgresql/"
# postgresql-restore-end

# elasticsearch-backup-begin
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

docker compose exec elasticsearch \
    curl -fsS -X PUT \
    "http://localhost:9200/_snapshot/${ES_REPO_NAME}/${SNAPSHOT_NAME}" \
    -H 'content-type: application/json' \
    -d '{
            "indices": "*",
            "ignore_unavailable": true,
            "include_global_state": false
        }'

docker compose exec elasticsearch \
    curl -fsS \
    "http://localhost:9200/_snapshot/${ES_REPO_NAME}/${SNAPSHOT_NAME}"

docker cp "$(docker compose ps -q elasticsearch):/usr/share/elasticsearch/backups" "${BACKUP_DIR}/elasticsearch/"

printf '%s\n' "${SNAPSHOT_NAME}" > "${BACKUP_DIR}/elasticsearch/SNAPSHOT_NAME"
# elasticsearch-restore-end

# contents-backup-begin
mkdir -p "${BACKUP_DIR}/contents"
docker compose exec web mkdir -p /code/backup/contents
sudo chown -R "1000:1000" "${BACKUP_DIR}/contents"
docker compose exec web cp -r /var/tmp/. /code/backup/contents/
docker cp "$(docker compose ps -q web):/code/backup/contents" "${BACKUP_DIR}/"
# contents-restore-end