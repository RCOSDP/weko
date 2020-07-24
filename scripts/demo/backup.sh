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

# args-check-begin
if [ ! -f ./docker-compose.yml ]; then
    echo "No such ./docker-compose.yml"
    exit 1
fi

if [ -z "$1" ]; then
    echo "Usage: $0 backupdir"
    exit 1
fi
BACKUPDIR=$1
mkdir -p $1
# args-check-end

# delete-old-backup-begin
if [ -e  ${BACKUPDIR}/contents -o -e ${BACKUPDIR}/static -o -e ${BACKUPDIR}/elasticsearch -o -e ${BACKUPDIR}/postgresql ]; then
    rm -ri ${BACKUPDIR}/contents ${BACKUPDIR}/static ${BACKUPDIR}/elasticsearch ${BACKUPDIR}/postgresql
fi
mkdir -p ${BACKUPDIR}/contents ${BACKUPDIR}/static ${BACKUPDIR}/elasticsearch ${BACKUPDIR}/postgresql
# delete-old-backup-end

# get-gitshow-begin
git show > ${BACKUPDIR}/git_show.txt
# get-gitshow-end

# pip-freeze-begin
docker-compose exec -T web pip freeze > ${BACKUPDIR}/pip_freeze.txt
# pip-freeze-end

# postgresql-backup-begin
docker-compose exec -T postgresql pg_dump -U invenio -a -f weko.sql -T alembic_version
docker cp $(docker-compose ps -q postgresql):/weko.sql ${BACKUPDIR}/postgresql/
# postgresql-restore-end

# elasticsearch-backup-begin
echo "elasticsearch-backup(1/4)"
docker-compose exec -T elasticsearch \
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
echo ""
echo "elasticsearch-backup(2/4)"
docker-compose exec -T elasticsearch \
    curl -X DELETE \
    http://localhost:9200/_snapshot/weko_backup/snapshot_all
echo ""
echo "elasticsearch-backup(3/4)"
docker-compose exec -T elasticsearch \
    curl -X PUT \
    http://localhost:9200/_snapshot/weko_backup/snapshot_all?wait_for_completion=true \
    -H 'Content-Type: application/json' \
    -d '{
        "indices": "*",
        "ignore_unavailable": true,
        "include_global_state": true
    }'
echo ""
echo "elasticsearch-backup(4/4)"
docker cp $(docker-compose ps -q elasticsearch):/usr/share/elasticsearch/backups ${BACKUPDIR}/elasticsearch/
# elasticsearch-restore-end

# contents-backup-begin
chown -R 1000:1000 ${BACKUPDIR}/contents
docker cp $(docker-compose ps -q web):/var/tmp ${BACKUPDIR}/contents/
# contents-restore-end


# static-backup-begin
chown -R 1000:1000 ${BACKUPDIR}/static
docker cp $(docker-compose ps -q web):/home/invenio/.virtualenvs/invenio/var/instance/static ${BACKUPDIR}/static/
# static-backup-end

