SETTING_FILE=scripts/instance.cfg
RESTRICTED_ACCESS_PROPERTY=30015

# echo Backup file
# cp $SETTING_FILE `date +${SETTING_FILE}_%Y%m%d`

# show restricted access setting
grep -E "^WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG = False' >> $SETTING_FILE
else
    sed -i.bak 's/WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG *= *True/WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG = False/' $SETTING_FILE
fi

# show restricted access flag on the workflow screen
grep -E "^WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS = False' >> $SETTING_FILE
else
    sed -i.bak 's/WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS *= *True/WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS = False/' $SETTING_FILE
fi

# enable application for use API
grep -E "^WEKO_RECORDS_UI_RESTRICTED_API *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_RECORDS_UI_RESTRICTED_API = False' >> $SETTING_FILE
else
    sed -i.bak 's/WEKO_RECORDS_UI_RESTRICTED_API *= *True/WEKO_RECORDS_UI_RESTRICTED_API = False/' $SETTING_FILE
fi

# enable multiple proxy posters
grep -E "^WEKO_ITEMS_UI_PROXY_POSTING *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ITEMS_UI_PROXY_POSTING = False' >> $SETTING_FILE
else
    sed -i.bak 's/WEKO_ITEMS_UI_PROXY_POSTING *= *True/WEKO_ITEMS_UI_PROXY_POSTING = False/' $SETTING_FILE
fi

# enable forced import for item types
grep -E "^WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED = False' >> $SETTING_FILE
else
    sed -i.bak 's/WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED *= *True/WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED = False/' $SETTING_FILE
fi

# enable index public confirmation feature
grep -E "^WEKO_INDEX_TREE_SHOW_MODAL *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_INDEX_TREE_SHOW_MODAL = False' >> $SETTING_FILE
else
    sed -i.bak 's/WEKO_INDEX_TREE_SHOW_MODAL *= *True/WEKO_INDEX_TREE_SHOW_MODAL = False/' $SETTING_FILE
fi

# enable custom profile editing feature
grep -E "^WEKO_USERPROFILES_CUSTOMIZE_ENABLED *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_USERPROFILES_CUSTOMIZE_ENABLED = False' >> $SETTING_FILE
else
    sed -i.bak 's/WEKO_USERPROFILES_CUSTOMIZE_ENABLED *= *True/WEKO_USERPROFILES_CUSTOMIZE_ENABLED = False/' $SETTING_FILE
fi

# enable mail recipient settings (To, CC, BCC)
grep -E "^INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED = False' >> $SETTING_FILE
else
    sed -i.bak 's/INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED *= *True/INVENIO_MAIL_ADDITIONAL_RECIPIENTS_ENABLED = False/' $SETTING_FILE
fi

docker cp scripts/demo/disable_restricted_access.sql $(docker compose ps -q postgresql):/tmp/disable_restricted_access.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/disable_restricted_access.sql

docker-compose exec web invenio shell tools/update_restricted_access_property.py $RESTRICTED_ACCESS_PROPERTY disable
