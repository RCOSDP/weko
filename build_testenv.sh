#!/bin/bash

docker cp test/postgresql/index.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/index.sql
