#!/bin/bash

docker-compose build
docker-compose up -d
docker-compose exec web ./scripts/populate-instance.sh

docker cp scripts/demo/item_type.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio invenio  -f /tmp/item_type.sql
docker cp scripts/demo/indextree.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio invenio  -f /tmp/indextree.sql
docker-compose exec web invenio workflow init action_status,Action,Flow
docker cp scripts/demo/resticted_access.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio invenio -f /tmp/resticted_access.sql
