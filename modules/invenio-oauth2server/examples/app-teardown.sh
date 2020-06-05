#!/bin/sh

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Drop the database tables
flask db drop --yes-i-know

# clean environment
[ -e "$DIR/instance" ] && rm -Rf $DIR/instance
[ -e "$DIR/static" ] && rm -Rf $DIR/static
