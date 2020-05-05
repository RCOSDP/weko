#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Install specific dependencies
mkdir $DIR/instance

# Install assets
flask collect -v
flask webpack buildall

# Create the database
flask db init
flask db create
