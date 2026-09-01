#!/bin/bash

set -xe

# 既定は従来どおり docker-compose2.yml 単独。
# CI は COMPOSE_FILE に docker-compose.ci.yml を重ねて、ビルド済みイメージを
# 使わせる(そのときは -f を足さない。足すと COMPOSE_FILE が無視されるため)。
compose_args=()
if [ -z "${COMPOSE_FILE:-}" ]; then
  compose_args=(-f docker-compose2.yml)
fi
dc() { docker compose "${compose_args[@]}" "$@"; }

find . | grep -E "(__pycache__|\.tox|\.eggs|\.pyc|\.pyo$)" | xargs rm -rf
dc down -v

# WEKO_SKIP_BUILD=1 でイメージのビルドを省略する(CI が pull 済みのとき)。
# 未ビルドのサービスは後続の up / run が必要に応じてビルドする。
if [ "${WEKO_SKIP_BUILD:-}" = "1" ]; then
  echo "WEKO_SKIP_BUILD=1: イメージのビルドを省略します"
else
  DOCKER_BUILDKIT=1 COMPOSE_DOCKER_CLI_BUILD=1 dc build --no-cache --force-rm
fi

# Initialize resources
dc run --rm web ./scripts/populate-instance.sh
docker cp scripts/demo/fix_lang_code_column.sql $(dc ps -q postgresql):/tmp/fix_lang_code_column.sql
dc exec postgresql psql -U invenio -d invenio -f /tmp/fix_lang_code_column.sql
docker cp scripts/demo/item_type.sql $(dc ps -q postgresql):/tmp/item_type.sql
dc exec postgresql psql -U invenio -d invenio -f /tmp/item_type.sql
docker cp scripts/demo/indextree.sql $(dc ps -q postgresql):/tmp/indextree.sql
dc exec postgresql psql -U invenio -d invenio -f /tmp/indextree.sql
dc run --rm web invenio workflow init action_status,Action
docker cp scripts/demo/defaultworkflow.sql $(dc ps -q postgresql):/tmp/defaultworkflow.sql
dc exec postgresql psql -U invenio -d invenio -f /tmp/defaultworkflow.sql
docker cp scripts/demo/doi_identifier.sql $(dc ps -q postgresql):/tmp/doi_identifier.sql
dc exec postgresql psql -U invenio -d invenio -f /tmp/doi_identifier.sql
docker cp postgresql/ddl/W-OA-user_activity_log.sql $(dc ps -q postgresql):/tmp/W-OA-user_activity_log.sql
dc exec postgresql psql -U invenio -d invenio -f /tmp/W-OA-user_activity_log.sql
docker cp scripts/demo/restricted_mail_template.sql $(dc ps -q postgresql):/tmp/restricted_mail_template.sql
dc exec postgresql psql -U invenio -d invenio -f /tmp/restricted_mail_template.sql
# docker cp scripts/demo/resticted_access.sql $(dc ps -q postgresql):/tmp/resticted_access.sql
# dc exec postgresql psql -U invenio -d invenio -f /tmp/resticted_access.sql

dc run --rm web invenio assets build
dc run --rm web invenio collect -v

# Start services
dc up -d
