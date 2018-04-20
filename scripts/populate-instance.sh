#!/usr/bin/env bash
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

# check environment variables:
if [ "${INVENIO_WEB_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_HOST=192.168.50.10"
    exit 1
fi
if [ "${INVENIO_WEB_INSTANCE}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_INSTANCE before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_INSTANCE=invenio"
    exit 1
fi
if [ "${INVENIO_WEB_VENV}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_VENV before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_VENV=invenio"
    exit 1
fi
if [ "${INVENIO_USER_EMAIL}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_USER_EMAIL before runnning this script."
    echo "[ERROR] Example: export INVENIO_USER_EMAIL=info@inveniosoftware.org"
    exit 1
fi
if [ "${INVENIO_USER_PASS}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_USER_PASS before runnning this script."
    echo "[ERROR] Example: export INVENIO_USER_PASS=uspass123"
    exit 1
fi
if [ "${INVENIO_POSTGRESQL_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_POSTGRESQL_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_POSTGRESQL_HOST=192.168.50.11"
    exit 1
fi
if [ "${INVENIO_POSTGRESQL_DBNAME}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_POSTGRESQL_DBNAME before runnning this script."
    echo "[ERROR] Example: INVENIO_POSTGRESQL_DBNAME=invenio"
    exit 1
fi
if [ "${INVENIO_POSTGRESQL_DBUSER}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_POSTGRESQL_DBUSER before runnning this script."
    echo "[ERROR] Example: INVENIO_POSTGRESQL_DBUSER=invenio"
    exit 1
fi
if [ "${INVENIO_POSTGRESQL_DBPASS}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_POSTGRESQL_DBPASS before runnning this script."
    echo "[ERROR] Example: INVENIO_POSTGRESQL_DBPASS=dbpass123"
    exit 1
fi
if [ "${INVENIO_REDIS_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_REDIS_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_REDIS_HOST=192.168.50.12"
    exit 1
fi
if [ "${INVENIO_ELASTICSEARCH_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_ELASTICSEARCH_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_ELASTICSEARCH_HOST=192.168.50.13"
    exit 1
fi
if [ "${INVENIO_RABBITMQ_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_RABBITMQ_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_RABBITMQ_HOST=192.168.50.14"
    exit 1
fi
if [ "${INVENIO_WORKER_HOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WORKER_HOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_WORKER_HOST=192.168.50.15"
    exit 1
fi

# load virtualenvrapper:
# shellcheck source=/dev/null
source "$(which virtualenvwrapper.sh)"

# switch virtual environment:
workon "${INVENIO_WEB_VENV}"

# quit on errors and unbound symbols:
# set -o errexit
set -o nounset

# sphinxdoc-create-database-begin
${INVENIO_WEB_INSTANCE} db drop --yes-i-know
${INVENIO_WEB_INSTANCE} db init
${INVENIO_WEB_INSTANCE} db create -v
# sphinxdoc-create-database-end

# sphinxdoc-create-roles-begin
${INVENIO_WEB_INSTANCE} roles create "${INVENIO_ROLE_SYSTEM}"
${INVENIO_WEB_INSTANCE} roles create "${INVENIO_ROLE_REPOSITORY}"
${INVENIO_WEB_INSTANCE} roles create "${INVENIO_ROLE_CONTRIBUTOR}"
# sphinxdoc-create-roles-end

# sphinxdoc-create-user-account-begin
${INVENIO_WEB_INSTANCE} users create \
       "${INVENIO_USER_EMAIL}" \
       --password "${INVENIO_USER_PASS}" \
       --active
# sphinxdoc-create-user-account-end

# sphinxdoc-set-user-role-begin
${INVENIO_WEB_INSTANCE} roles add \
       "${INVENIO_USER_EMAIL}" \
       "${INVENIO_ROLE_SYSTEM}"
# sphinxdoc-set-user-role-end

# sphinxdoc-create-files-location-begin
${INVENIO_WEB_INSTANCE} files location \
       "${INVENIO_FILES_LOCATION_NAME}" \
       "${INVENIO_FILES_LOCATION_URI}" \
       --default
# sphinxdoc-create-files-location-end

# sphinxdoc-index-initialisation-begin
${INVENIO_WEB_INSTANCE} index init
sleep 20
${INVENIO_WEB_INSTANCE} index queue init
# sphinxdoc-index-initialisation-end

# sphinxdoc-populate-with-demo-records-begin
#${INVENIO_WEB_INSTANCE} demo init
# sphinxdoc-populate-with-demo-records-end

# sphinxdoc-create-test-data-begin
${INVENIO_WEB_INSTANCE} users create \
       "test01@hitachi.com" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} roles add \
       "test01@hitachi.com" \
       "${INVENIO_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} users create \
       "test02@hitachi.com" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} roles add \
        "test02@hitachi.com" \
       "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} users create \
       "test03@hitachi.com" \
       --password "${INVENIO_USER_PASS}" \
       --active
# sphinxdoc-create-test-data-end

# sphinxdoc-set-role-access-begin
${INVENIO_WEB_INSTANCE} access \
       allow "superuser-access" \
       role "${INVENIO_ROLE_SYSTEM}"

${INVENIO_WEB_INSTANCE} access \
       allow "admin-access" \
       role "${INVENIO_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "schema-access" \
       role "${INVENIO_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "index-tree-access" \
       role "${INVENIO_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "item-type-access" \
       role "${INVENIO_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "item-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-bucket-update" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-delete" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-delete-version" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} wekoaccess \
       allow "search-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} wekoaccess \
       allow "detail-page-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} wekoaccess \
       allow "author-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"
# sphinxdoc-set-role-access-end
