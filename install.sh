#!/bin/bash


docker-compose down -v
docker-compose build
docker-compose up -d
docker-compose exec web ./scripts/populate-instance.sh
docker cp scripts/demo/item_type.sql $(docker-compose ps -q postgresql):/tmp/item_type.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker-compose exec web invenio workflow init action_status,Action
