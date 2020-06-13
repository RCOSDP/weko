#!/usr/bin/env bash

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# clean environment
flask db destroy --yes-i-know
[ -e "instance" ] && rm -Rf instance
[ -e "data" ] && rm -Rf data
