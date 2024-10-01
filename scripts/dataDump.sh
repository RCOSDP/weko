#!/bin/bash

docker-compose exec -u postgres postgresql pg_ctl stop -D /var/lib/postgresql/data

#table backup
docker cp scripts/backup.sql $(docker-compose ps -q postgresql):/tmp/backup.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/backup.sql > /tmp/output.txt

# #datadump backup
docker-compose exec postgresql pg_dump -U invenio -d invenio -F c -b -v -f /tmp/datadump.backup
docker cp $(docker-compose ps -q postgresql):/tmp/datadump.backup /tmp/datadump.backup

docker-compose stop postgresql

# create volume directry 
mv /var/lib/docker/volumes/weko_pgsql-data/_data /var/lib/docker/volumes/weko_pgsql-data/_data_old

mkdir /var/lib/docker/volumes/weko_pgsql-data/_data