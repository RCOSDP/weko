SETTING_FILE=scripts/instance.cfg

# echo Backup file
# cp $SETTING_FILE `date +${SETTING_FILE}_%Y%m%d`

grep -E "^WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS = True' >> $SETTING_FILE
else
    sed -i.bak 's/WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS *= *False/WEKO_ADMIN_DISPLAY_RESTRICTED_SETTINGS = True/' $SETTING_FILE
fi

grep -E "^WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT *= *.*$" $SETTING_FILE
if [ $? -ne 0 ]; then
    echo 'WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT = True' >> $SETTING_FILE
else
    sed -i.bak 's/WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT *= *False/WEKO_ADMIN_USE_MAIL_TEMPLATE_EDIT = True/' $SETTING_FILE
fi

docker cp scripts/demo/restricted_access_upgrade.sql $(docker compose ps -q postgresql):/tmp/restricted_access_upgrade.sql
docker-compose exec postgresql psql -U invenio -d invenio -f /tmp/restricted_access_upgrade.sql