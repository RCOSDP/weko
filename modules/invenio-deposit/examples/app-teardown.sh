#!/bin/sh

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# clean environment
[ -e "$DIR/instance" ] && rm -Rf $DIR/instance
[ -h "$DIR/static/.DS_Store" ] && rm -Rf $DIR/static/.DS_Store
[ -e "$DIR/static/.webassets-cache" ] && rm -Rf $DIR/static/.webassets-cache
[ -e "$DIR/static/admin" ] && rm -Rf $DIR/static/admin
[ -e "$DIR/static/bootstrap" ] && rm -Rf $DIR/static/bootstrap
[ -e "$DIR/static/gen" ] && rm -Rf $DIR/static/gen
[ -e "$DIR/static/images" ] && rm -Rf $DIR/static/images
[ -e "$DIR/static/js" ] && rm -Rf $DIR/static/js
[ -e "$DIR/static/json" ] && rm -Rf $DIR/static/json
[ -e "$DIR/static/node_modules" ] && rm -Rf $DIR/static/node_modules
[ -e "$DIR/static/package.json" ] && rm -Rf $DIR/static/package.json
[ -e "$DIR/static/scss" ] && rm -Rf $DIR/static/scss
[ -e "$DIR/static/templates/invenio_deposit" ] && rm -Rf $DIR/static/templates/invenio_deposit
[ -e "$DIR/static/templates/invenio_search_ui" ] && rm -Rf $DIR/static/templates/invenio_search_ui
[ -e "$DIR/static/vendor" ] && rm -Rf $DIR/static/vendor

# Delete the database
flask db drop --yes-i-know

# Delete indices
flask index destroy --yes-i-know --force
