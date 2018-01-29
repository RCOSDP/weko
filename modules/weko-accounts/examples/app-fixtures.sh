#!/bin/sh

# quit on errors:
set -o errexit

# quit on unbound symbols:
set -o nounset

DIR=`dirname "$0"`

cd $DIR
export FLASK_APP=app.py

# Setup fixtures

# create users. Use the following emails and passwords to login.
flask users create wekosoftware@nii.ac.jp -a --password 123456
flask users create reader@nii.ac.jp -a --password 123456
flask users create editor@nii.ac.jp -a --password 123456
flask users create admin@nii.ac.jp -a --password 123456

# create admin role and add the role to a user
flask roles create admin
flask roles add wekosoftware@nii.ac.jp admin
flask roles add admin@nii.ac.jp admin
