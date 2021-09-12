#!/bin/bash

docker cp test/postgresql/del_index.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/del_index.sql

docker cp test/postgresql/indexA.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/indexA.sql

docker cp test/postgresql/indexB.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/indexB.sql

docker cp test/postgresql/indexC.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/indexC.sql

