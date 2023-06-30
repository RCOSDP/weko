#!/bin/bash

pm2="pm2 start /usr/local/weko-frontend/dist/server/entry.mjs"
eval $pm2

supervisor="/usr/bin/supervisord -c /etc/supervisor/supervisord.conf"
eval $supervisor
