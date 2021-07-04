#!/bin/bash

docker cp test/postgresql/del_index.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/del_index.sql

#docker cp test/postgresql/index2.sql $(docker-compose ps -q postgresql):/tmp/
#docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/index2.sql

docker cp test/postgresql/index.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/index.sql

# docker-compose exec postgresql pg_dump -U invenio --data-only --table workflow_action --table workflow_flow_action_role --table workflow_action_feedbackmail --table workflow_action_status --table workflow_flow_define --table workflow_activity_action  --table workflow_userrole --table workflow_action_identifier --table workflow_workflow --table workflow_flow_action --table workflow_action_journal
docker cp test/postgresql/workflow.sql $(docker-compose ps -q postgresql):/tmp/
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/workflow.sql
