#!/bin/bash

set -xe

# Select the compose file to use.
# Priority: 1st argument > COMPOSE_FILE env var > auto-detection by CPU architecture.
# On arm64 (Apple Silicon etc.) docker-compose.arm64.yml is used automatically.
if [ -n "$1" ]; then
  COMPOSE_FILE="$1"
elif [ -z "$COMPOSE_FILE" ]; then
  case "$(uname -m)" in
    aarch64 | arm64)
      COMPOSE_FILE="docker-compose.arm64.yml"
      ;;
    *)
      COMPOSE_FILE="docker-compose2.yml"
      ;;
  esac
fi

echo "Using compose file: ${COMPOSE_FILE}"

find . | grep -E "(__pycache__|\.tox|\.eggs|\.pyc|\.pyo$)" | xargs rm -rf
docker compose -f "${COMPOSE_FILE}" down -v
DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 docker compose -f "${COMPOSE_FILE}" build --no-cache --force-rm

# Initialize resources
docker compose -f "${COMPOSE_FILE}" run --rm web ./scripts/populate-instance.sh
docker cp scripts/demo/fix_lang_code_column.sql $(docker compose -f "${COMPOSE_FILE}" ps -q postgresql):/tmp/fix_lang_code_column.sql
docker compose -f "${COMPOSE_FILE}" exec postgresql psql -U invenio -d invenio -f /tmp/fix_lang_code_column.sql
docker cp scripts/demo/item_type.sql $(docker compose -f "${COMPOSE_FILE}" ps -q postgresql):/tmp/item_type.sql
docker compose -f "${COMPOSE_FILE}" exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker cp scripts/demo/indextree.sql $(docker compose -f "${COMPOSE_FILE}" ps -q postgresql):/tmp/indextree.sql
docker compose -f "${COMPOSE_FILE}" exec postgresql psql -U invenio -d invenio -f /tmp/indextree.sql
docker compose -f "${COMPOSE_FILE}" run --rm web invenio workflow init action_status,Action
docker cp scripts/demo/defaultworkflow.sql $(docker compose -f "${COMPOSE_FILE}" ps -q postgresql):/tmp/defaultworkflow.sql
docker compose -f "${COMPOSE_FILE}" exec postgresql psql -U invenio -d invenio -f /tmp/defaultworkflow.sql
docker cp scripts/demo/doi_identifier.sql $(docker compose -f "${COMPOSE_FILE}" ps -q postgresql):/tmp/doi_identifier.sql
docker compose -f "${COMPOSE_FILE}" exec postgresql psql -U invenio -d invenio -f /tmp/doi_identifier.sql
docker cp postgresql/ddl/W-OA-user_activity_log.sql $(docker compose -f "${COMPOSE_FILE}" ps -q postgresql):/tmp/W-OA-user_activity_log.sql
docker compose -f "${COMPOSE_FILE}" exec postgresql psql -U invenio -d invenio -f /tmp/W-OA-user_activity_log.sql
docker cp scripts/demo/restricted_mail_template.sql $(docker compose -f "${COMPOSE_FILE}" ps -q postgresql):/tmp/restricted_mail_template.sql
docker compose -f "${COMPOSE_FILE}" exec postgresql psql -U invenio -d invenio -f /tmp/restricted_mail_template.sql
# docker cp scripts/demo/resticted_access.sql $(docker compose -f "${COMPOSE_FILE}" ps -q postgresql):/tmp/resticted_access.sql
# docker compose -f "${COMPOSE_FILE}" exec postgresql psql -U invenio -d invenio -f /tmp/resticted_access.sql

docker compose -f "${COMPOSE_FILE}" run --rm web invenio assets build
docker compose -f "${COMPOSE_FILE}" run --rm web invenio collect -v

# Start services
docker compose -f "${COMPOSE_FILE}" up -d
