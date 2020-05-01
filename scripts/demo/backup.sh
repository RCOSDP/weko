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

# quit on errors and unbound symbols:
set -o errexit

# delete-old-backup-begin
rm -rf ./scripts/demo/contents ./scripts/demo/elasticsearch ./scripts/demo/postgresql
mkdir -p ./scripts/demo/contents ./scripts/demo/elasticsearch ./scripts/demo/postgresql
# delete-old-backup-end

# postgresql-backup-begin
docker-compose exec postgresql pg_dump -U invenio -a -f weko.sql -T alembic_version
docker cp $(docker-compose ps -q postgresql):/weko.sql ./scripts/demo/postgresql/
# postgresql-restore-end

# elasticsearch-backup-begin
docker-compose exec elasticsearch \
    curl -X PUT \
    http://localhost:9200/_snapshot/weko_backup \
    -H 'cache-control: no-cache' \
    -H 'content-type: application/json' \
    -d '{
            "type": "fs",
            "settings": {
                "location": "/usr/share/elasticsearch/backups"
            }
        }'
docker-compose exec elasticsearch \
    curl -X DELETE \
    http://localhost:9200/_snapshot/weko_backup/snapshot_all?wait_for_completion=true
docker-compose exec elasticsearch \
    curl -X PUT \
    http://localhost:9200/_snapshot/weko_backup/snapshot_all?wait_for_completion=true
docker cp $(docker-compose ps -q elasticsearch):/usr/share/elasticsearch/backups ./scripts/demo/elasticsearch/
# elasticsearch-restore-end

# contents-backup-begin
chown -R 1000:1000 ./scripts/demo/contents
docker-compose exec web cp -r /var/tmp /code/scripts/demo/contents/
# contents-restore-end
