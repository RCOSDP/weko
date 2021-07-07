#!/bin/bash

docker cp test/postgresql/del_index.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/del_index.sql

#docker cp test/postgresql/index2.sql $(docker-compose ps -q postgresql):/tmp/
#docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/index2.sql

docker cp test/postgresql/index.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/index.sql
