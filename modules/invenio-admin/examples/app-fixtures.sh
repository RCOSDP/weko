#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Create a user
flask users create info@inveniosoftware.org -a --password 123456
flask roles create admin
flask roles add info@inveniosoftware.org admin
flask access allow admin-access role admin
