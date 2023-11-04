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

if [ ! -d "$1" ]; then
    echo "Usage: $0 backupdir"
    exit 1
fi
BACKUPDIR=$1
# args-check-end

# create-database-begin
docker-compose -f docker-compose2.yml exec -T web invenio db drop --yes-i-know
docker-compose -f docker-compose2.yml exec -T web invenio db init
docker-compose -f docker-compose2.yml exec -T web invenio db create -v
# create-database-end

# postgresql-restore-begin
if [ -f ${BACKUPDIR}/postgresql/weko.sql.gz ]; then
    gunzip ${BACKUPDIR}/postgresql/weko.sql.gz
fi
docker cp ${BACKUPDIR}/postgresql/weko.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/
docker-compose -f docker-compose2.yml exec -T postgresql psql -U invenio -d invenio -f weko.sql
# postgresql-restore-end

# elasticsearch-restore-begin
echo "elasticsearch-restore(1/4)"
docker-compose -f docker-compose2.yml exec -T web invenio index destroy --force --yes-i-know
docker-compose -f docker-compose2.yml exec -T web invenio index delete '*' --force --yes-i-know
echo ""
docker-compose -f docker-compose2.yml stop
docker-compose -f docker-compose2.yml start elasticsearch
sleep 20
echo "elasticsearch-restore(2/4)"
docker-compose -f docker-compose2.yml exec -T elasticsearch \
    curl -XPUT \
    http://localhost:9200/_snapshot/weko_backup \
    -H 'cache-control: no-cache' \
    -H 'content-type: application/json' \
    -d '{
            "type": "fs",
            "settings": {
                "location": "/usr/share/elasticsearch/backups"
            }
        }'
docker cp ${BACKUPDIR}/elasticsearch/backups $(docker-compose -f docker-compose2.yml ps -q elasticsearch):/usr/share/elasticsearch/
echo ""
echo "elasticsearch-restore(3/4)"
docker-compose -f docker-compose2.yml exec -T elasticsearch chown -R elasticsearch:elasticsearch ./backups
echo ""
echo "elasticsearch-restore(4/4)"
docker-compose -f docker-compose2.yml exec -T elasticsearch \
    curl -XPOST \
    http://localhost:9200/_snapshot/weko_backup/snapshot_all/_restore?wait_for_completion=true \
    -H 'content-type: application/json' \
    -d '{ 
            "indices": "*", 
            "ignore_unavailable": true,
            "include_global_state": true
        }'
echo ""
docker-compose -f docker-compose2.yml start
# elasticsearch-restore-end

# contents-restore-begin
if [ -d "${BACKUPDIR}/contents" ]; then
    sudo chown -R 1000:1000 ${BACKUPDIR}/contents
    docker-compose -f docker-compose2.yml exec -T web rm -fr /var/tmp/*
    docker cp ${BACKUPDIR}/contents/tmp/. $(docker-compose -f docker-compose2.yml ps -q web):/var/tmp
fi
# contents-restore-end

# data-restore-begin
if [ -d "${BACKUPDIR}/data" ]; then
    sudo chown -R 1000:1000 ${BACKUPDIR}/data
    docker-compose -f docker-compose2.yml exec -T web rm -fr /home/invenio/.virtualenvs/invenio/var/instance/data/*
    docker cp ${BACKUPDIR}/data/. $(docker-compose ps -q web):/home/invenio/.virtualenvs/invenio/var/instance/data
fi
# data-restore-end

## conf-restore-begin
#if [ -d "${BACKUPDIR}/conf" ]; then
#    sudo chown -R 1000:1000 ${BACKUPDIR}/conf
#    docker-compose -f docker-compose2.yml exec -T web rm -fr /home/invenio/.virtualenvs/invenio/var/instance/conf/*
#    docker cp ${BACKUPDIR}/conf/. $(docker-compose -f docker-compose2.yml ps -q web):/home/invenio/.virtualenvs/invenio/var/instance/conf
#fi
## conf-restore-end

