#!/bin/bash

echo 'create ams itemtype'
docker cp scripts/demo/ams/item_type_name.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/ams_itemtype_name.sql
docker cp scripts/demo/ams/item_type.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/ams_itemtype.sql
docker cp scripts/demo/ams/item_type_mapping.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/ams_itemtype_mapping.sql
docker cp scripts/demo/ams/rocrate_mapping.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/ams_rocrate_mapping.sql
docker cp scripts/demo/ams/facet_search_setting.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/ams_facet_search_setting.sql
docker cp scripts/demo/ams/jsonld_mappings.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/ams_jsonld_mappings.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/ams_itemtype_name.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/ams_itemtype.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/ams_itemtype_mapping.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/ams_rocrate_mapping.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/ams_facet_search_setting.sql
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/ams_jsonld_mappings.sql

echo 'add free textarea to file property'
docker-compose -f docker-compose2.yml exec web invenio shell /code/tools/add_free_textarea.py

echo 'create search settings'
record_count=$(docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -t -c 'SELECT count(*) FROM search_management;')
if [ $record_count -lt 1 ]; then
    docker cp scripts/demo/ams/search_management.sql $(docker-compose -f docker-compose2.yml ps -q postgresql):/tmp/ams_search_management.sql
    docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -d invenio -f /tmp/ams_search_management.sql
fi
docker-compose -f docker-compose2.yml exec web invenio shell /code/scripts/demo/ams/update_search_management.py
