#!/bin/bash

# PM2 は supervisord の [program:pm2] 管理下で起動する。
# ここで pm2 start すると監視外のデーモンになり、落ちても誰も再起動しない。
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
