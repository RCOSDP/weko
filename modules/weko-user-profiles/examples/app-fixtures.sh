#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Create the users
flask users create -a info@inveniosoftware.org --password 123456
flask users create -a another@inveniosoftware.org --password 123456

# give to 'info' user the access to the admin page
flask roles create admin
flask roles add info@inveniosoftware.org admin
flask access allow admin-access role admin

