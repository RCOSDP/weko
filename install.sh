#!/bin/bash

find . | grep -E "(__pycache__|\.eggs|\.pyc|\.pyo$)" | xargs rm -rf
docker-compose down -v
for volume in $(docker volume ls -f name=weko -q); do
  docker volume rm $(volume)
done
docker-compose build --no-cache --force-rm

# Initialize resources
docker-compose run --rm web ./scripts/populate-instance.sh
docker cp scripts/demo/item_type3.sql $(docker-compose ps -q postgresql):/tmp/item_type.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker-compose run --rm web invenio workflow init action_status,Action
docker cp scripts/demo/resticted_access.sql $(docker-compose ps -q postgresql):/tmp/resticted_access.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/resticted_access.sql
docker-compose run --rm web invenio workflow init gakuninrdm_data

# Start services
docker-compose up -d
