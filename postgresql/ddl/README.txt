# Run database upgrade

## Example.
## docker cp sp52_workflow_userrole.sql $(docker-compose ps -q postgresql):/tmp/
## docker-compose exec postgresql psql -U invenio invenio  -f /tmp/sp52_workflow_userrole.sql

## scripts
# for i in $(ls postgresql/ddl/*.sql);do echo "docker cp "$i" $(docker-compose ps -q postgresql):/tmp/;";echo "docker-compose exec postgresql psql -U invenio -f /tmp/$(basename "$i");";done




