#!/bin/bash

# check version
docker-compose exec postgresql psql --version

# datadump restore
docker cp /tmp/datadump.backup $(docker-compose ps -q postgresql):/tmp/datadump.backup
docker-compose exec postgresql pg_restore --clean --if-exists -U invenio -d invenio /tmp/datadump.backup > /tmp/output.txt

# data migration
docker cp scripts/migration.sql $(docker-compose ps -q postgresql):/tmp/migration.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/migration.sql > /tmp/output.txt

