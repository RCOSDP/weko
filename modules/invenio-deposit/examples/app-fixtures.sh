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

# Load fixtures
flask fixtures location
flask fixtures records
