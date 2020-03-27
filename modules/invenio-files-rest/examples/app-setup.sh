#!/usr/bin/env bash

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py
mkdir $DIR/instance

# Create the database
flask db init
flask db create
