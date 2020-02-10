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

if [ ! -d "$1" ]; then
    echo "Usage: $0 backupdir"
    exit 1
fi
BACKUPDIR=$1
# args-check-end

# create-database-begin
docker-compose exec web invenio db drop --yes-i-know
docker-compose exec web invenio db init
docker-compose exec web invenio db create -v
# create-database-end

# postgresql-restore-begin
if [ -f ${BACKUPDIR}/postgresql/weko.sql.gz ]; then
    gunzip ${BACKUPDIR}/postgresql/weko.sql.gz
fi
docker cp ${BACKUPDIR}/postgresql/weko.sql $(docker-compose ps -q postgresql):/
docker-compose exec postgresql psql -U invenio -d invenio -f weko.sql
# postgresql-restore-end

# elasticsearch-restore-begin
docker-compose stop
docker-compose start elasticsearch
sleep 20
echo "elasticsearch-restore(1/5)"
docker-compose exec elasticsearch \
    curl -XDELETE http://localhost:9200/*
echo ""
echo "elasticsearch-restore(2/5)"
docker-compose exec elasticsearch \
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
docker cp ${BACKUPDIR}/elasticsearch/backups $(docker-compose ps -q elasticsearch):/usr/share/elasticsearch/
echo ""
echo "elasticsearch-restore(3/5)"
docker-compose exec elasticsearch chown -R elasticsearch:elasticsearch ./backups
echo ""
echo "elasticsearch-restore(4/5)"
docker-compose exec elasticsearch \
    curl -XPOST \
    http://localhost:9200/_snapshot/weko_backup/snapshot_all/_restore?wait_for_completion=true
echo ""
echo "elasticsearch-restore(5/5)"
docker-compose exec elasticsearch \
    curl -XPUT \
    http://localhost:9200/_ingest/pipeline/item-file-pipeline \
    -H 'Content-Type: application/json' \
    -d '{
            "description" : "Index contents of each file.",
            "processors" : [
                {
                    "foreach": {
                        "field": "content",
                        "processor": {
                            "attachment": {
                                "indexed_chars" : -1,
                                "target_field": "_ingest._value.attachment",
                                "field": "_ingest._value.file",
                                "properties": [
                                    "content"
                                ]
                            }
                        }
                    }
                }
             ]
         }'
echo ""
docker-compose start
# elasticsearch-restore-end

# contents-restore-begin
if [ -d "${BACKUPDIR}/contents" ]; then
    sudo chown -R 1000:1000 ${BACKUPDIR}/contents
    docker cp ${BACKUPDIR}/contents/tmp $(docker-compose ps -q web):/var/
fi
# contents-restore-end
