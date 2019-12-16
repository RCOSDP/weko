#!/usr/bin/env bash

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Create a user
flask users create info@inveniosoftware.org -a --password 123456

# Load some test data (you can re-run the command many times)
flask fixtures files
