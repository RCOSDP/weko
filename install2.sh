#!/bin/bash

find . | grep -E "(__pycache__|\.eggs|\.pyc|\.pyo$)" | xargs rm -rf
docker-compose -f docker-compose2.yml down -v
for volume in $(docker volume ls -f name=weko -q); do
  docker volume rm $(volume)
done
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose -f docker-compose2.yml build --no-cache --force-rm

# Initialize resources
docker-compose -f docker-compose2.yml run --rm web ./scripts/populate-instance.sh
docker cp scripts/demo/item_type4.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/item_type.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker-compose -f docker-compose2.yml run --rm web invenio workflow init action_status,Action
docker-compose -f docker-compose2.yml run --rm web invenio workflow init gakuninrdm_data
docker-compose -f docker-compose2.yml run --rm web invenio shell scripts/demo/register_oai_schema.py overwrite_all
docker-compose -f docker-compose2.yml run --rm web invenio shell tools/update/addjpcoar_v1_mapping.py
docker-compose -f docker-compose2.yml run --rm web invenio assets build
docker-compose -f docker-compose2.yml run --rm web invenio collect -v

# Start services
docker-compose -f docker-compose2.yml up -d
