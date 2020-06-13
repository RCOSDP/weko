#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Clean the database
flask db destroy --yes-i-know

# Clean the indices
flask index destroy --yes-i-know
