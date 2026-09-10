#!/bin/bash
# This script executes SQL only if records exist in the search_management table.

## Database connection information
DB_USER="invenio"
DB_NAME="invenio"
COMPOSE_FILE="docker-compose2.yml"
POSTGRES_CONTAINER=$(docker-compose -f $COMPOSE_FILE ps -q postgresql)  # Get PostgreSQL container ID

## Get record count from search_management table
record_count=$(docker-compose -f $COMPOSE_FILE exec postgresql psql -U $DB_USER -d $DB_NAME -t -c 'SELECT count(*) FROM search_management;')
record_count=$(echo $record_count | tr -d ' ')

## If records exist, execute SQL update
if [ "$record_count" -ge 1 ]; then
    echo "Records exist in search_management table. Executing SQL."
    # Copy SQL file to container
    docker cp scripts/demo/search_management_update.sql $POSTGRES_CONTAINER:/tmp/ams_search_management_update.sql
    # Execute SQL file
    docker-compose -f $COMPOSE_FILE exec postgresql psql -U $DB_USER -d $DB_NAME -f /tmp/ams_search_management_update.sql
else
    echo "search_management table is empty. SQL will not be executed."
fi
