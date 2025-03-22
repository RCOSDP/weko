#!/bin/bash

find . | grep -E "(__pycache__|\.tox|\.eggs|\.pyc|\.pyo$)" | xargs rm -rf
docker-compose -f docker-compose2.yml down -v
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose -f docker-compose2.yml build --no-cache --force-rm

# Initialize resources
docker-compose run --rm web ./scripts/populate-instance.sh
docker cp scripts/demo/item_type3.sql $(docker-compose ps -q postgresql):/tmp/item_type.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker cp scripts/demo/indextree.sql $(docker-compose ps -q postgresql):/tmp/indextree.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/indextree.sql
docker-compose run --rm web invenio workflow init action_status,Action
docker cp scripts/demo/defaultworkflow.sql $(docker-compose ps -q postgresql):/tmp/defaultworkflow.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/defaultworkflow.sql
docker cp scripts/demo/doi_identifier.sql $(docker-compose ps -q postgresql):/tmp/doi_identifier.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/doi_identifier.sql
# docker cp scripts/demo/resticted_access.sql $(docker-compose ps -q postgresql):/tmp/resticted_access.sql
# docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/resticted_access.sql
#docker-compose run --rm web invenio workflow init gakuninrdm_data
docker-compose run --rm web invenio shell scripts/demo/register_oai_schema.py overwrite_all
docker-compose run --rm web invenio shell tools/update/addjpcoar_v1_mapping.py

# Start services
docker-compose -f docker-compose2.yml up -d
