# Input restricted item property id
RESTRICTED_ITEM_PROPERTY_ID=30015

# Stop and remove web container
docker-compose rm web -fsv

# Build web container image
docker-compose build web --no-cache

# Apply sp70
docker cp postgresql/ddl/sp70-workflow_location.sql $(docker-compose ps -q postgresql):/tmp/sp70-workflow_location.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/sp70-workflow_location.sql

# apply sp72
docker cp postgresql/ddl/sp72-CreateAuthersAffiliation.sql $(docker-compose ps -q postgresql):/tmp/sp72-CreateAuthersAffiliation.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/sp72-CreateAuthersAffiliation.sql
docker cp postgresql/ddl/sp72-createindex.sql $(docker-compose ps -q postgresql):/tmp/sp72-createindex.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/sp72-createindex.sql

# apply W2023
docker cp "postgresql/ddl/W2023-21 workflow_flow_action_role.sql" $(docker-compose ps -q postgresql):"/tmp/W2023-21 workflow_flow_action_role.sql"
docker-compose exec postgresql psql -U invenio -d invenio -f "/tmp/W2023-21 workflow_flow_action_role.sql"
docker cp "postgresql/ddl/W2023-21 update_resticted_items.sql" $(docker-compose ps -q postgresql):"/tmp/W2023-21 update_resticted_items.sql"
docker-compose exec postgresql psql -U invenio -d invenio -f "/tmp/W2023-21 update_resticted_items.sql"
docker cp "postgresql/ddl/W2023-22 mail_template_genre.sql" $(docker-compose ps -q postgresql):"/tmp/W2023-22 mail_template_genre.sql"
docker-compose exec postgresql psql -U invenio -d invenio -f "/tmp/W2023-22 mail_template_genre.sql"

# Start web container
docker-compose down
docker-compose up -d

# Update json records
docker-compose exec web invenio shell tools/updateRestrictedRecords.py $RESTRICTED_ITEM_PROPERTY_ID

# Update resources 
docker-compose exec web invenio collect -v
docker-compose exec web invenio assets build
docker-compose exec web bash -c "jinja2 /code/scripts/instance.cfg > /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg"
docker-compose down
docker-compose up -d