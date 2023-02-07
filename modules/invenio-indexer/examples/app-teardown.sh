#!/bin/sh

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Delete database
flask db destroy --yes-i-know

# Delete indices
flask index destroy --yes-i-know --force
