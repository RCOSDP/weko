#!/bin/bash

pm2="pm2 start /usr/local/ecosystem.config.js"
eval $pm2

supervisor="/usr/bin/supervisord -c /etc/supervisor/supervisord.conf"
eval $supervisor
