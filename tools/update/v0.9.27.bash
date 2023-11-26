#!/bin/bash

# build static files
docker-compose -f docker-compose2.yml run --rm web invenio assets build;
docker-compose -f docker-compose2.yml run --rm web invenio collect -v;

# update OAI-PMH schema
docker-compose -f docker-compose2.yml run --rm web invenio shell scripts/demo/register_oai_schema.py overwrite_all;

# update itemtype
docker cp postgresql/ddl/v0.9.27.sql $(docker-compose -f docker-compose2.yml ps postgresql -q):/tmp;
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -f /tmp/v0.9.27.sql;
docker-compose -f docker-compose2.yml exec postgresql psql -U invenio -c "SELECT update_v0927();";

# add new properties and update properties.
docker-compose -f docker-compose2.yml run --rm web invenio shell scripts/demo/register_properties.py only_specified;

# update default item type
docker-compose -f docker-compose2.yml exec web invenio shell scripts/demo/update_itemtype_full.py;

# reload all properteis of item types
docker-compose -f docker-compose2.yml exec web invenio shell scripts/demo/renew_all_item_types.py;

CNT=$(docker-compose -f docker-compose2.yml exec postgresql psql -qtAX -U invenio -c "SELECT count(id) FROM item_type_property;")
if [ $CNT -gt 100 ]; then
    docker-compose -f docker-compose2.yml exec web invenio index queue init;
    docker-compose -f docker-compose2.yml exec web invenio index reindex -t recid --yes-i-know;
    docker-compose -f docker-compose2.yml exec web invenio index run;
fi 

echo "Finish update"

exit 0