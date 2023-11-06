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
if [ ! -f ./docker-compose2.yml ]; then
    echo "No such ./docker-compose2.yml"
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
# contents
if [ -e ${BACKUPDIR}/contents ]; then
    rm -ri ${BACKUPDIR}/contents
fi
mkdir -p ${BACKUPDIR}/contents
# elasticsearch
if [ -e ${BACKUPDIR}/elasticsearch ]; then
    rm -ri ${BACKUPDIR}/elasticsearch
fi
mkdir -p ${BACKUPDIR}/elasticsearch
# postgresql
if [ -e ${BACKUPDIR}/postgresql ]; then
    rm -ri ${BACKUPDIR}/postgresql
fi
mkdir -p ${BACKUPDIR}/postgresql
# data
if [ -e ${BACKUPDIR}/data ]; then
    rm -ri ${BACKUPDIR}/data
fi
mkdir -p ${BACKUPDIR}/data
# conf
if [ -e ${BACKUPDIR}/conf ]; then
    rm -ri ${BACKUPDIR}/conf
fi
mkdir -p ${BACKUPDIR}/conf

# delete-old-backup-end

# get-gitshow-begin
git show > ${BACKUPDIR}/git_show.txt
# get-gitshow-end

# pip-freeze-begin
docker-compose -f docker-compose2.yml exec -T web pip freeze > ${BACKUPDIR}/pip_freeze.txt
# pip-freeze-end

# postgresql-backup-begin
docker-compose -f docker-compose2.yml exec -T postgresql pg_dump -U invenio -a -f weko.sql -T alembic_version
docker cp $(docker-compose -f docker-compose2.yml ps -q postgresql):/weko.sql ${BACKUPDIR}/postgresql/
# postgresql-restore-end

# elasticsearch-backup-begin
echo "elasticsearch-backup(1/4)"
docker-compose -f docker-compose2.yml exec -T elasticsearch bash -c "rm  -fr /usr/share/elasticsearch/backups"
docker-compose -f docker-compose2.yml exec -T elasticsearch bash -c "mkdir  /usr/share/elasticsearch/backups"
docker-compose -f docker-compose2.yml exec -T elasticsearch bash -c "chown -R elasticsearch:root  /usr/share/elasticsearch/backups"
docker-compose -f docker-compose2.yml exec -T elasticsearch \
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
docker-compose -f docker-compose2.yml exec -T elasticsearch \
    curl -X DELETE \
    http://localhost:9200/_snapshot/weko_backup/snapshot_all
echo ""
echo "elasticsearch-backup(3/4)"
docker-compose -f docker-compose2.yml exec -T elasticsearch \
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

docker cp $(docker-compose -f docker-compose2.yml ps -q elasticsearch):/usr/share/elasticsearch/backups ${BACKUPDIR}/elasticsearch/
chown -R 1000:1000 ${BACKUPDIR}/elasticsearch
# elasticsearch-restore-end

# contents-backup-begin
docker cp $(docker-compose -f docker-compose2.yml ps -q web):/var/tmp ${BACKUPDIR}/contents/
chown -R 1000:1000 ${BACKUPDIR}/contents
# contents-restore-end


# data-backup-begin
docker cp $(docker-compose -f docker-compose2.yml ps -q web):/home/invenio/.virtualenvs/invenio/var/instance/data ${BACKUPDIR}/
chown -R 1000:1000 ${BACKUPDIR}/data
# data-backup-end

# conf-backup-begin
docker cp $(docker-compose -f docker-compose2.yml ps -q web):/home/invenio/.virtualenvs/invenio/var/instance/conf ${BACKUPDIR}/
chown -R 1000:1000 ${BACKUPDIR}/conf
# conf-backup-end

