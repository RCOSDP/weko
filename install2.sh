#!/bin/bash

find . | grep -E "(__pycache__|\.tox|\.eggs|\.pyc|\.pyo$)" | xargs rm -rf
docker-compose -f docker-compose2.yml down -v
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker-compose -f docker-compose2.yml build --no-cache --force-rm

# Initialize resources
docker-compose -f docker-compose2.yml run --rm web ./scripts/populate-instance.sh
docker cp scripts/demo/item_type3.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/item_type.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker cp scripts/demo/indextree.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/indextree.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/indextree.sql
docker-compose -f docker-compose2.yml run --rm web invenio workflow init action_status,Action
# # docker-compose -f docker-compose2.yml run --rm web invenio workflow init gakuninrdm_data
docker cp scripts/demo/defaultworkflow.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/defaultworkflow.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/defaultworkflow.sql
docker cp scripts/demo/doi_identifier.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/doi_identifier.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/doi_identifier.sql
docker cp postgresql/ddl/v0.9.27.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/v0.9.27.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/v0.9.27.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -c "SELECT update_v0927();"

docker-compose -f docker-compose2.yml run --rm web invenio shell scripts/demo/register_oai_schema.py overwrite_all
# # docker-compose -f docker-compose2.yml run --rm web invenio shell tools/update/addjpcoar_v1_mapping.py
docker-compose -f docker-compose2.yml run --rm web invenio shell scripts/demo/update_jpcoar_2_0.py only_specified
docker cp postgresql/update/2023_Q4.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/2023_Q4.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/2023_Q4.sql
docker-compose -f docker-compose2.yml run --rm web invenio assets build
docker-compose -f docker-compose2.yml run --rm web invenio collect -v

# Start services
docker-compose -f docker-compose2.yml up -d
