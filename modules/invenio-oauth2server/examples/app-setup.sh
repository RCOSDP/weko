#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Install specific dependencies
pip install -r requirements.txt

mkdir $DIR/instance

# Preapare all static files:
npm install -g node-sass clean-css@3.4.19 requirejs uglify-js
flask npm
cd static ; npm install ; cd ..
flask collect -v
flask assets build

# Create the database
flask db init
flask db create

# Install requirements
npm install -g node-sass clean-css clean-css-cli requirejs uglify-js

# Collect npm, requirements from registered bundles
flask npm

# Now install npm requirements (requires that npm is already installed)
cd static ; npm install ; cd ..

# Next, we copy the static files from the Python packages into the Flask
# application's static folder
flask collect -v

# Finally, we build the webassets bundles
flask assets build
