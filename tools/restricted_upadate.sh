#!/bin/bash

if [ $# -ne 1 ]; then
  echo "Usage: $0 repository"
  exit 1
fi

REPO=$1
CONFIG_PATH=/fs-config

WEB_POD=$(kubectl get po -n weko3 --no-headers | grep $(echo ${REPO} | tr ._ -) | awk '{ print $1; })
PG_MASTER=$(kubectl get po -n weko3pg -l spilo-role=master --no-headers | awk '{ print $1; })
DATABASE=$(echo ${REPO} | tr .- _)
GITHUB_PATH=https://raw.githubusercontent.com/RCOSDP/weko/refs/heads/${BRANCH}

set -euo pipefail
IFS=$'\n\t'
trap 'rc=$?; echo "Error: ${BASH_COMMAND} (line $LINENO) exited with ${rc}" >&2; exit ${rc}' ERR

###SETTING_FILE=scripts/instance.cfg
SETTING_FILE=${CONFIG_PATH}/${REPO}/instance.cfg
RESTRICTED_ACCESS_PROPERTY=30015

# echo Backup file
#cp $SETTING_FILE `date +${SETTING_FILE}_%Y%m%d`

# show restricted access setting
grep -E "^WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG = True' >> $SETTING_FILE
else
### sed -i.bak 's/WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG *= *False/WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG = True/' $SETTING_FILE
    sudo sed -i 's/WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG *= *False/WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG = True/' $SETTING_FILE
fi

# show restricted access flag on the workflow screen
grep -E "^WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS = True' >> $SETTING_FILE
else
### sed -i.bak 's/WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS *= *False/WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS = True/' $SETTING_FILE
    sudo sed -i 's/WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS *= *False/WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS = True/' $SETTING_FILE
fi

# enable application for use API
grep -E "^WEKO_RECORDS_UI_RESTRICTED_API *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_RECORDS_UI_RESTRICTED_API = True' >> $SETTING_FILE
else
### sed -i.bak 's/WEKO_RECORDS_UI_RESTRICTED_API *= *False/WEKO_RECORDS_UI_RESTRICTED_API = True/' $SETTING_FILE
    sudo sed -i 's/WEKO_RECORDS_UI_RESTRICTED_API *= *False/WEKO_RECORDS_UI_RESTRICTED_API = True/' $SETTING_FILE
fi

# enable multiple proxy posters
grep -E "^WEKO_ITEMS_UI_PROXY_POSTING *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ITEMS_UI_PROXY_POSTING = True' >> $SETTING_FILE
else
### sed -i.bak 's/WEKO_ITEMS_UI_PROXY_POSTING *= *False/WEKO_ITEMS_UI_PROXY_POSTING = True/' $SETTING_FILE
    sudo sed -i 's/WEKO_ITEMS_UI_PROXY_POSTING *= *False/WEKO_ITEMS_UI_PROXY_POSTING = True/' $SETTING_FILE
fi

# enable forced import for item types
grep -E "^WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED = True' >> $SETTING_FILE
else
### sed -i.bak 's/WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED *= *False/WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED = True/' $SETTING_FILE
    sudo sed -i 's/WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED *= *False/WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED = True/' $SETTING_FILE
fi

# enable index public confirmation feature
grep -E "^WEKO_INDEX_TREE_SHOW_MODAL *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_INDEX_TREE_SHOW_MODAL = True' >> $SETTING_FILE
else
### sed -i.bak 's/WEKO_INDEX_TREE_SHOW_MODAL *= *False/WEKO_INDEX_TREE_SHOW_MODAL = True/' $SETTING_FILE
    sudo sed -i 's/WEKO_INDEX_TREE_SHOW_MODAL *= *False/WEKO_INDEX_TREE_SHOW_MODAL = True/' $SETTING_FILE
fi

# enable custom profile editing feature
grep -E "^WEKO_USERPROFILES_CUSTOMIZE_ENABLED *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_USERPROFILES_CUSTOMIZE_ENABLED = True' >> $SETTING_FILE
else
### sed -i.bak 's/WEKO_USERPROFILES_CUSTOMIZE_ENABLED *= *False/WEKO_USERPROFILES_CUSTOMIZE_ENABLED = True/' $SETTING_FILE
    sudo sed -i 's/WEKO_USERPROFILES_CUSTOMIZE_ENABLED *= *False/WEKO_USERPROFILES_CUSTOMIZE_ENABLED = True/' $SETTING_FILE
fi

# enable mail recipient settings (To, CC, BCC)
grep -E "^INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED = True' >> $SETTING_FILE
else
### sed -i.bak 's/INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED *= *False/INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED = True/' $SETTING_FILE
    sudo sed -i 's/INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED *= *False/INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED = True/' $SETTING_FILE
fi

###docker cp scripts/demo/resticted_access.sql $(docker compose ps -q postgresql):/tmp/resticted_access.sql
###docker-compose exec postgresql psql -U invenio -d invenio -v ON_ERROR_STOP=1 -f /tmp/resticted_access.sql
kubectl cp -n weko3pg -c postgres scripts/demo/resticted_access.sql ${PG_MASTER}:/tmp/resticted_access.sql
kubectl exec -n weko3pg -c postgres ${PG_MASTER} -- psql -U invenio -d ${DB} -v ON_ERROR_STOP=1 -f /tmp/resticted_access.sql
kubectl exec -n weko3pg -c postgres ${PG_MASTER} -- rm /tmp/resticted_access.sql

###docker-compose exec web invenio shell tools/update_restricted_access_property.py $RESTRICTED_ACCESS_PROPERTY enable
kubectl exec -n weko3 -c web ${WEB_POD} -- invenio shell tools/update_restricted_access_property.py $RESTRICTED_ACCESS_PROPERTY enable

# verify the update
tools/verify_restricted_update.sh $SETTING_FILE True
###docker compose exec web invenio shell tools/verify_restricted_records.py enable
kubectl exec -n weko3 -c web ${WEB_POD} -- invenio shell tools/verify_restricted_records.py enable

# docker-compose exec web bash -c "jinja2 /code/scripts/instance.cfg > /home/invenio/.virtualenvs/invenio/var/instance/invenio.cfg"
# docker-compose down
# docker-compose up -d
