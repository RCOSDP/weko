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

# create-database-begin
docker-compose exec web invenio db drop --yes-i-know
docker-compose exec web invenio db init
docker-compose exec web invenio db create -v
# create-database-end

# postgresql-restore-begin
docker cp ./scripts/demo/postgresql/weko.sql $(docker-compose ps -q postgresql):/
docker-compose exec postgresql psql -U invenio -d invenio -f weko.sql
# postgresql-restore-end

# elasticsearch-restore-begin
docker-compose stop
docker-compose start elasticsearch
sleep 10
docker-compose exec elasticsearch \
    curl -XDELETE http://localhost:9200/*
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
docker cp ./scripts/demo/elasticsearch/backups $(docker-compose ps -q elasticsearch):/usr/share/elasticsearch/
docker-compose exec elasticsearch chown -R elasticsearch:elasticsearch ./backups
docker-compose exec elasticsearch \
    curl -X POST \
    http://localhost:9200/_snapshot/weko_backup/snapshot_all/_restore?wait_for_completion=true
docker-compose start
# elasticsearch-restore-end

# contents-restore-begin
sudo chown -R 1000:1000 ./scripts/demo/contents
docker-compose exec web cp -r /code/scripts/demo/contents/tmp /var/
# contents-restore-end
