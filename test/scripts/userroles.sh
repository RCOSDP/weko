#!/usr/bin/env bash
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is based on Invenio.
# Copyright (C) 2015-2018 CERN.
#
# WEKO3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

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
if [ "uspass123" = "" ]; then
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

# switch virtual environment:
workon "${INVENIO_WEB_VENV}"

set -x

set +e

INVENIO_WEB_INSTANCE="invenio"

WEKO3_ROLE_SYSTEM="System Administrator"
WEKO3_ROLE_REPOSITORY="Repository Administrator"
WEKO3_ROLE_CONTRIBUTOR="Contributor"
WEKO3_ROLE_COMMUNITY="Community Administrator"

WEKO3_ROLE_ADMIN="Administrator"
WEKO3_ROLE_GENERAL="General"
WEKO3_ROLE_GRADUATED_STUDENT="Graduated Student"
WEKO3_ROLE_STUDENT="Student"

INVENIO_USER_EMAIL=wekosoftware@nii.ac.jp
INVENIO_USER_PASS=uspass123


# WEKO3
${INVENIO_WEB_INSTANCE} roles create "${WEKO3_ROLE_SYSTEM}"
${INVENIO_WEB_INSTANCE} roles create "${WEKO3_ROLE_REPOSITORY}"
${INVENIO_WEB_INSTANCE} roles create "${WEKO3_ROLE_CONTRIBUTOR}"
${INVENIO_WEB_INSTANCE} roles create "${WEKO3_ROLE_COMMUNITY}"
# WEKO3
${INVENIO_WEB_INSTANCE} roles create "${WEKO3_ROLE_ADMIN}"
${INVENIO_WEB_INSTANCE} roles create "${WEKO3_ROLE_GENERAL}"
${INVENIO_WEB_INSTANCE} roles create "${WEKO3_ROLE_GRADUATED_STUDENT}"
${INVENIO_WEB_INSTANCE} roles create "${WEKO3_ROLE_STUDENT}"

# Access
${INVENIO_WEB_INSTANCE} access \
       allow "superuser-access" \
       role "${WEKO3_ROLE_SYSTEM}"

${INVENIO_WEB_INSTANCE} access \
       allow "superuser-access" \
       role "${WEKO3_ROLE_ADMIN}"

${INVENIO_WEB_INSTANCE} access \
       allow "admin-access" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} access \
       allow "schema-access" \
       role "${WEKO3_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "index-tree-access" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} access \
       allow "indextree-journal-access" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} access \
       allow "item-type-access" \
       role "${WEKO3_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "item-access" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}" \
       role "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-bucket-update" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}" \
       role "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-delete" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}" \
       role "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-delete-version" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}" \
       role "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-read" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}" \
       role "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "search-access" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}" \
       role "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "detail-page-access" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}" \
       role "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "download-original-pdf-access" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}" \
       role "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "author-access" \
       role "${WEKO3_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "items-autofill" \
       role "${WEKO3_ROLE_REPOSITORY}" \
       role "${WEKO3_ROLE_COMMUNITY}" \
       role "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "stats-api-access" \
       role "${WEKO3_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "item-access" \
       role "${WEKO3_ROLE_GENERAL}" \
       role "${WEKO3_ROLE_GRADUATED_STUDENT}" \
       role "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-bucket-update" \
       role "${WEKO3_ROLE_GENERAL}" \
       role "${WEKO3_ROLE_GRADUATED_STUDENT}" \
       role "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-delete" \
       role "${WEKO3_ROLE_GENERAL}" \
       role "${WEKO3_ROLE_GRADUATED_STUDENT}" \
       role "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-delete-version" \
       role "${WEKO3_ROLE_GENERAL}" \
       role "${WEKO3_ROLE_GRADUATED_STUDENT}" \
       role "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} access \
       allow "search-access" \
       role "${WEKO3_ROLE_GENERAL}" \
       role "${WEKO3_ROLE_GRADUATED_STUDENT}" \
       role "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} access \
       allow "detail-page-access" \
       role "${WEKO3_ROLE_GENERAL}" \
       role "${WEKO3_ROLE_GRADUATED_STUDENT}" \
       role "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} access \
       allow "download-original-pdf-access" \
       role "${WEKO3_ROLE_GENERAL}" \
       role "${WEKO3_ROLE_GRADUATED_STUDENT}" \
       role "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} access \
       allow "author-access" \
       role "${WEKO3_ROLE_GENERAL}" \
       role "${WEKO3_ROLE_GRADUATED_STUDENT}" \
       role "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} access \
       allow "items-autofill" \
       role "${WEKO3_ROLE_GENERAL}" \
       role "${WEKO3_ROLE_GRADUATED_STUDENT}" \
       role "${WEKO3_ROLE_STUDENT}"

# User
${INVENIO_WEB_INSTANCE} users create \
       "${INVENIO_USER_EMAIL}" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "sysadmin@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "sysadmin1@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "sysadmin2@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "sysadmin3@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "admin@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "repoadmin@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "repoadmin1@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "repoadmin2@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "repoadmin3@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "contributor@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "contributor1@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "contributor2@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "contributor3@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
      "comadmin@example.org" \
      --password "${INVENIO_USER_PASS}" \
      --active

${INVENIO_WEB_INSTANCE} users create \
      "comadmin1@example.org" \
      --password "${INVENIO_USER_PASS}" \
      --active

${INVENIO_WEB_INSTANCE} users create \
      "comadmin2@example.org" \
      --password "${INVENIO_USER_PASS}" \
      --active

${INVENIO_WEB_INSTANCE} users create \
      "comadmin3@example.org" \
      --password "${INVENIO_USER_PASS}" \
      --active

${INVENIO_WEB_INSTANCE} users create \
       "user@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "user1@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "user2@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "user3@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "hosyonin@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "hosyonin1@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "hosyonin2@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "hosyonin3@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "gstudent@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "gstudent1@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "gstudent2@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "gstudent3@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "student@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "student1@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "student2@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
       "student3@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

# Add Role
${INVENIO_WEB_INSTANCE} roles add \
       "${INVENIO_USER_EMAIL}" \
       "${WEKO3_ROLE_SYSTEM}"

${INVENIO_WEB_INSTANCE} roles add \
       "sysadmin@example.org" \
       "${WEKO3_ROLE_SYSTEM}"

${INVENIO_WEB_INSTANCE} roles add \
       "sysadmin1@example.org" \
       "${WEKO3_ROLE_SYSTEM}"

${INVENIO_WEB_INSTANCE} roles add \
       "sysadmin2@example.org" \
       "${WEKO3_ROLE_SYSTEM}"

${INVENIO_WEB_INSTANCE} roles add \
       "sysadmin3@example.org" \
       "${WEKO3_ROLE_SYSTEM}"

${INVENIO_WEB_INSTANCE} roles add \
       "admin@example.org" \
       "${WEKO3_ROLE_ADMIN}"

${INVENIO_WEB_INSTANCE} roles add \
       "repoadmin@example.org" \
       "${WEKO3_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} roles add \
       "repoadmin1@example.org" \
       "${WEKO3_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} roles add \
       "repoadmin2@example.org" \
       "${WEKO3_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} roles add \
       "repoadmin3@example.org" \
       "${WEKO3_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} roles add \
      "comadmin@example.org" \
      "${WEKO3_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} roles add \
      "comadmin1@example.org" \
      "${WEKO3_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} roles add \
      "comadmin2@example.org" \
      "${WEKO3_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} roles add \
      "comadmin3@example.org" \
      "${WEKO3_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} roles add \
       "contributor@example.org" \
       "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} roles add \
       "contributor1@example.org" \
       "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} roles add \
       "contributor2@example.org" \
       "${WEKO3_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} roles add \
       "contributor3@example.org" \
       "${WEKO3_ROLE_CONTRIBUTOR}"

## user@ はロールなしユーザ

${INVENIO_WEB_INSTANCE} roles add \
       "hosyonin@example.org" \
       "${WEKO3_ROLE_GENERAL}"

${INVENIO_WEB_INSTANCE} roles add \
       "hosyonin1@example.org" \
       "${WEKO3_ROLE_GENERAL}"

${INVENIO_WEB_INSTANCE} roles add \
       "hosyonin2@example.org" \
       "${WEKO3_ROLE_GENERAL}"

${INVENIO_WEB_INSTANCE} roles add \
       "hosyonin3@example.org" \
       "${WEKO3_ROLE_GENERAL}"

${INVENIO_WEB_INSTANCE} roles add \
       "gstudent@example.org" \
       "${WEKO3_ROLE_GRADUATED_STUDENT}"

${INVENIO_WEB_INSTANCE} roles add \
       "gstudent1@example.org" \
       "${WEKO3_ROLE_GRADUATED_STUDENT}"

${INVENIO_WEB_INSTANCE} roles add \
       "gstudent2@example.org" \
       "${WEKO3_ROLE_GRADUATED_STUDENT}"

${INVENIO_WEB_INSTANCE} roles add \
       "gstudent3@example.org" \
       "${WEKO3_ROLE_GRADUATED_STUDENT}"

${INVENIO_WEB_INSTANCE} roles add \
       "student@example.org" \
       "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} roles add \
       "student1@example.org" \
       "${WEKO3_ROLE_STUDENT}"

${INVENIO_WEB_INSTANCE} roles add \
       "student2@example.org" \
       "${WEKO3_ROLE_STUDENT}"
${INVENIO_WEB_INSTANCE} roles add \
       "student3@example.org" \
       "${WEKO3_ROLE_STUDENT}"

#
set -e
