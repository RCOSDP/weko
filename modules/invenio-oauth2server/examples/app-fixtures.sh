#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

## Load fixtures
flask users create reader@inveniosoftware.org -a --password 123456
flask users create clientapp@inveniosoftware.org -a --password 123456
flask users create admin@inveniosoftware.org -a --password 123456

# create admin role and add the role to a user
flask roles create admin
flask roles add reader@inveniosoftware.org admin
flask roles add admin@inveniosoftware.org admin

# assign some allowed actions to this users
flask access allow admin-access role admin
flask access allow superuser-access role admin
