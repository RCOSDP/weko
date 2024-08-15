#!/usr/bin/env bash
# shellcheck disable=SC2103,SC2102
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
if [ "${INVENIO_WEB_HOST_NAME}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_WEB_HOST_NAME before runnning this script."
    echo "[ERROR] Example: export INVENIO_WEB_HOST_NAME=invenio"
    exit 1
fi
if [ "${INVENIO_USER_EMAIL}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_USER_EMAIL before runnning this script."
    echo "[ERROR] Example: export INVENIO_USER_EMAIL=wekosoftware@nii.ac.jp"
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
if [ "${INVENIO_RABBITMQ_USER}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_RABBITMQ_USER before runnning this script."
    echo "[ERROR] Example: export INVENIO_RABBITMQ_USER=guest"
    exit 1
fi
if [ "${INVENIO_RABBITMQ_PASS}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_RABBITMQ_PASS before runnning this script."
    echo "[ERROR] Example: export INVENIO_RABBITMQ_PASS=guest"
    exit 1
fi
if [ "${INVENIO_RABBITMQ_VHOST}" = "" ]; then
    echo "[ERROR] Please set environment variable INVENIO_RABBITMQ_VHOST before runnning this script."
    echo "[ERROR] Example: export INVENIO_RABBITMQ_VHOST=/"
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

# detect pathname of this script:
scriptpathname=$(cd "$(dirname "$0")" && pwd)

# sphinxdoc-create-virtual-environment-begin
mkvirtualenv "${INVENIO_WEB_VENV}"
cdvirtualenv
# sphinxdoc-create-virtual-environment-end

# quit on errors and unbound symbols:
set -o errexit
set -o nounset

# fix build error (weko#23031)
#pip install pip==20.2.4
#pip install setuptools==57.5.0
pip install pip==24.1.2
pip install setuptools==71.0.3
#pip cache purge
pip_version=$(pip --version)
setuptool_version=$(pip show setuptools | grep Version)
echo "pip version: ${pip_version}, setuptools version: ${setuptool_version}"
if [[ "$@" != *"--devel"* ]]; then
# sphinxdoc-install-invenio-full-begin
    pip install -r "$scriptpathname/../packages.txt"
    pip install --no-deps -r "$scriptpathname/../packages-invenio.txt"
    pip install --no-deps -r "$scriptpathname/../requirements-weko-modules.txt"
# sphinxdoc-install-invenio-full-end
else
    pip install -r "$scriptpathname/../requirements-devel.txt"
fi
