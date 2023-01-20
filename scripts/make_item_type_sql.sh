#!/bin/bash

docker-compose exec postgresql pg_dump -U invenio -t item_type -t item_type_name -t item_type_mapping -t item_type_property -t oaiserver_schema --column-insert -c invenio > ./item_type.sql