#!/bin/bash

set -xe
jinja2 /code/scripts/instance.cfg > /home/invenio/.virtualenvs/invenio/var/instance/conf/invenio.cfg
/usr/bin/supervisord -c /code/scripts/supervisord.conf