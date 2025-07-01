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
if [ "${SEARCH_INDEX_PREFIX}" = "" ]; then
    echo "[ERROR] Please set environment variable SEARCH_INDEX_PREFIX before runnning this script."
    echo "[ERROR] Example: export SEARCH_INDEX_PREFIX=tenant1"
    exit 1
fi

# load virtualenvrapper:
# shellcheck source=/dev/null
source "$(which virtualenvwrapper.sh)"

# switch virtual environment:
workon "${INVENIO_WEB_VENV}"

# quit on errors and unbound symbols:
set -o errexit
# set -o nounset

# sphinxdoc-create-database-begin
${INVENIO_WEB_INSTANCE} db drop --yes-i-know
${INVENIO_WEB_INSTANCE} db init
${INVENIO_WEB_INSTANCE} db create -v
${INVENIO_WEB_INSTANCE} stats partition create $(date +%Y)
${INVENIO_WEB_INSTANCE} stats partition create $(date -d 'year' +%Y)
# sphinxdoc-create-database-end

# sphinxdoc-index-initialisation-begin
# ${INVENIO_WEB_INSTANCE} index destroy --yes-i-know
${INVENIO_WEB_INSTANCE} index init
sleep 20
${INVENIO_WEB_INSTANCE} index queue init
# sphinxdoc-index-initialisation-end

# elasticsearch-ilm-setting-begin
curl -XPUT 'http://'${INVENIO_ELASTICSEARCH_HOST}':9200/_ilm/policy/weko_stats_policy' -H 'Content-Type: application/json' -d '
{
  "policy":{
    "phases":{
      "hot":{
        "actions":{
          "rollover":{
            "max_size":"50gb"
          }
        }
      }
    }
  }
}'
event_list=('celery-task' 'item-create' 'top-view' 'record-view' 'file-download' 'file-preview' 'search')
for event_name in ${event_list[@]}
do
  curl -XPUT 'http://'${INVENIO_ELASTICSEARCH_HOST}':9200/'${SEARCH_INDEX_PREFIX}'-events-stats-'${event_name}'-000001?timeout=2m' -H 'Content-Type: application/json' -d '
  {
    "aliases": {
      "'${SEARCH_INDEX_PREFIX}'-events-stats-'${event_name}'": {
        "is_write_index": true
      }
    }
  }'
  curl -XPUT 'http://'${INVENIO_ELASTICSEARCH_HOST}':9200/'${SEARCH_INDEX_PREFIX}'-stats-'${event_name}'-000001?timeout=2m' -H 'Content-Type: application/json' -d '
  {
    "aliases": {
      "'${SEARCH_INDEX_PREFIX}'-stats-'${event_name}'": {
        "is_write_index": true
      }
    }
  }'
done
# elasticsearch-ilm-setting-end

# sphinxdoc-populate-with-demo-records-begin
#${INVENIO_WEB_INSTANCE} demo init
# sphinxdoc-populate-with-demo-records-end

# sphinxdoc-create-files-location-begin
${INVENIO_WEB_INSTANCE} files location \
       "${INVENIO_FILES_LOCATION_NAME}" \
       "${INVENIO_FILES_LOCATION_URI}" \
       --default
# sphinxdoc-create-files-location-end

# sphinxdoc-create-user-account-begin
${INVENIO_WEB_INSTANCE} users create \
       "${INVENIO_USER_EMAIL}" \
       --password "${INVENIO_USER_PASS}" \
       --active
# sphinxdoc-create-user-account-end

# sphinxdoc-create-roles-begin
${INVENIO_WEB_INSTANCE} roles create "${INVENIO_ROLE_SYSTEM}"
${INVENIO_WEB_INSTANCE} roles create "${INVENIO_ROLE_REPOSITORY}"
${INVENIO_WEB_INSTANCE} roles create "${INVENIO_ROLE_CONTRIBUTOR}"
${INVENIO_WEB_INSTANCE} roles create "${INVENIO_ROLE_COMMUNITY}"
# sphinxdoc-create-roles-end

# sphinxdoc-set-user-role-begin
${INVENIO_WEB_INSTANCE} roles add \
       "${INVENIO_USER_EMAIL}" \
       "${INVENIO_ROLE_SYSTEM}"
# sphinxdoc-set-user-role-end

# sphinxdoc-set-role-access-begin
${INVENIO_WEB_INSTANCE} access \
       allow "superuser-access" \
       role "${INVENIO_ROLE_SYSTEM}"

${INVENIO_WEB_INSTANCE} access \
       allow "admin-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} access \
       allow "schema-access" \
       role "${INVENIO_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "index-tree-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} access \
       allow "indextree-journal-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}"

${INVENIO_WEB_INSTANCE} access \
       allow "item-type-access" \
       role "${INVENIO_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "item-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-bucket-update" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-delete" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-delete-version" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-read" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "files-rest-object-read-version" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "search-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "detail-page-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "download-original-pdf-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "author-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "items-autofill" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \
       role "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} access \
       allow "stats-api-access" \
       role "${INVENIO_ROLE_REPOSITORY}" \
       role "${INVENIO_ROLE_COMMUNITY}" \

${INVENIO_WEB_INSTANCE} access \
       allow "read-style-action" \
       role "${INVENIO_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} access \
       allow "update-style-action" \
       role "${INVENIO_ROLE_REPOSITORY}"

# sphinxdoc-set-role-access-end

#### sphinxdoc-create-language-data-begin
${INVENIO_WEB_INSTANCE} language create \
        --active --registered "en" "English" 001

${INVENIO_WEB_INSTANCE} language create \
        --active "zh-cn" "中文 (簡体)" 000

${INVENIO_WEB_INSTANCE} language create \
        --active "zh-tw" "中文 (繁体)" 000

${INVENIO_WEB_INSTANCE} language create \
        --active "id" "Indonesia" 000

${INVENIO_WEB_INSTANCE} language create \
        --active "vi" "Tiếng Việt" 000

${INVENIO_WEB_INSTANCE} language create \
         --active "ms" "Bahasa Melayu" 000

${INVENIO_WEB_INSTANCE} language create \
         --active "fil" "Filipino (Pilipinas)" 000

${INVENIO_WEB_INSTANCE} language create \
         --active "th" "ไทย" 000

${INVENIO_WEB_INSTANCE} language create \
         --active "hi" "हिन्दी" 000

${INVENIO_WEB_INSTANCE} language create \
         --active --registered "ja" "日本語" 002
#### sphinxdoc-create-language-data-end

##### sphinxdoc-create-test-data-begin
${INVENIO_WEB_INSTANCE} users create \
       "repoadmin@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} roles add \
       "repoadmin@example.org" \
       "${INVENIO_ROLE_REPOSITORY}"

${INVENIO_WEB_INSTANCE} users create \
       "contributor@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} roles add \
        "contributor@example.org" \
       "${INVENIO_ROLE_CONTRIBUTOR}"

${INVENIO_WEB_INSTANCE} users create \
       "user@example.org" \
       --password "${INVENIO_USER_PASS}" \
       --active

${INVENIO_WEB_INSTANCE} users create \
      "comadmin@example.org" \
      --password "${INVENIO_USER_PASS}" \
      --active

${INVENIO_WEB_INSTANCE} roles add \
        "comadmin@example.org" \
       "${INVENIO_ROLE_COMMUNITY}"

##### sphinxdoc-create-test-data-end

# sphinxdoc-set-web-api-account-combobox-begin
${INVENIO_WEB_INSTANCE} cert insert crf CrossRef
${INVENIO_WEB_INSTANCE} cert insert oaa "OAアシスト"
# sphinxdoc-set-web-api-account-combobox-end

#### sphinxdoc-create-widget_type-data-begin
${INVENIO_WEB_INSTANCE} widget_type create \
        "Free description" "Free description"

${INVENIO_WEB_INSTANCE} widget_type create \
        "Access counter" "Access counter"

${INVENIO_WEB_INSTANCE} widget_type create \
        "Notice" "Notice"

${INVENIO_WEB_INSTANCE} widget_type create \
        "New arrivals" "New arrivals"

${INVENIO_WEB_INSTANCE} widget_type create \
        "Main contents" "Main contents"

${INVENIO_WEB_INSTANCE} widget_type create \
        "Menu" "Menu"
${INVENIO_WEB_INSTANCE} widget_type create \
        "Header" "Header"
${INVENIO_WEB_INSTANCE} widget_type create \
        "Footer" "Footer"
### sphinxdoc-create-widget_type-data-end

# sphinxdoc-set-report-unit-and-target-begin
${INVENIO_WEB_INSTANCE} report create_unit \
       "1" "Day"
${INVENIO_WEB_INSTANCE} report create_unit \
       "2" "Week"
${INVENIO_WEB_INSTANCE} report create_unit \
       "3" "Year"
${INVENIO_WEB_INSTANCE} report create_unit \
       "4" "Item"
${INVENIO_WEB_INSTANCE} report create_unit \
       "5" "Host"
${INVENIO_WEB_INSTANCE} report create_target \
       "1" "Item registration report" "1,2,3,5"
${INVENIO_WEB_INSTANCE} report create_target \
       "2" "Item detail view report" "1,2,3,4,5"
${INVENIO_WEB_INSTANCE} report create_target \
       "3" "Contents download report" "1,2,3,4,5"
# sphinxdoc-set-report-unit-and-target-end

${INVENIO_WEB_INSTANCE} billing create \
       --active 1

# create-admin-settings-begin
${INVENIO_WEB_INSTANCE} admin_settings create_settings \
       1 "items_display_settings" \
       "{'items_search_author': 'name', 'items_display_email': True}"
${INVENIO_WEB_INSTANCE} admin_settings create_settings \
       2 "storage_check_settings" \
       "{'threshold_rate': 80, 'cycle': 'weekly', 'day': 0}"
${INVENIO_WEB_INSTANCE} admin_settings create_settings \
       3 "site_license_mail_settings" \
       "{'Root Index': {'auto_send_flag': False}}"
${INVENIO_WEB_INSTANCE} admin_settings create_settings \
       4 "default_properties_settings" \
       "{'show_flag': True}"
${INVENIO_WEB_INSTANCE} admin_settings create_settings \
       5 "elastic_reindex_settings" \
       "{'has_errored': False}"
${INVENIO_WEB_INSTANCE} admin_settings create_settings \
       6 "blocked_user_settings" \
       "{'blocked_ePPNs': []}"
${INVENIO_WEB_INSTANCE} admin_settings create_settings \
       7 "shib_login_enable" \
       "{'shib_flg': False}"
${INVENIO_WEB_INSTANCE} admin_settings create_settings \
       8 "default_role_settings" \
       "{'gakunin_role': '', 'orthros_outside_role': '', 'extra_role': ''}"
${INVENIO_WEB_INSTANCE} admin_settings create_settings \
       9 "attribute_mapping" \
       "{'shib_eppn': '', 'shib_role_authority_name': '', 'shib_mail': '', 'shib_user_name': ''}"
# create-admin-settings-end

# create-default-authors-prefix-settings-begin
${INVENIO_WEB_INSTANCE} authors_prefix default_settings \
       "WEKO" "WEKO" ""
${INVENIO_WEB_INSTANCE} authors_prefix default_settings \
       "ORCID" "ORCID" "https://orcid.org/##"
${INVENIO_WEB_INSTANCE} authors_prefix default_settings \
       "CiNii" "CiNii" "https://ci.nii.ac.jp/author/##"
${INVENIO_WEB_INSTANCE} authors_prefix default_settings \
       "KAKEN2" "KAKEN2" "https://nrid.nii.ac.jp/nrid/##"
${INVENIO_WEB_INSTANCE} authors_prefix default_settings \
       "ROR" "ROR" "https://ror.org/##"
${INVENIO_WEB_INSTANCE} authors_prefix default_settings \
       "ISNI" "ISNI" "http://www.isni.org/isni/##"
${INVENIO_WEB_INSTANCE} authors_prefix default_settings \
       "VIAF" "VIAF" "https://viaf.org/viaf/##"
${INVENIO_WEB_INSTANCE} authors_prefix default_settings \
       "AID" "AID" ""
${INVENIO_WEB_INSTANCE} authors_prefix default_settings \
       "e-Rad_Researcher" "e-Rad_Researcher" ""
# create-default-authors-prefix-settings-end

# create-default-authors-affiliation-settings-begin
${INVENIO_WEB_INSTANCE} authors_affiliation default_settings \
       "ISNI" "ISNI" "http://www.isni.org/isni/##"
${INVENIO_WEB_INSTANCE} authors_affiliation default_settings \
       "GRID" "GRID" "https://www.grid.ac/institutes/##"
${INVENIO_WEB_INSTANCE} authors_affiliation default_settings \
       "Ringgold" "Ringgold" ""
${INVENIO_WEB_INSTANCE} authors_affiliation default_settings \
       "kakenhi" "kakenhi" ""
${INVENIO_WEB_INSTANCE} authors_affiliation default_settings \
       "ROR" "ROR" "https://ror.org/##"
# create-default-authors-affiliation-settings-end

# create-widget-bucket-begin
${INVENIO_WEB_INSTANCE} widget init
# create-widget-bucket-end

# create-facet-search-setting-begin
${INVENIO_WEB_INSTANCE} facet_search_setting create \
       "Data Language"	"デ一タの言語"	"language"	"[]"	True   SelectBox     1      True    OR
${INVENIO_WEB_INSTANCE} facet_search_setting create \
       "Access"	"アクセス制限"	"accessRights"	"[]"	True   SelectBox     2      True    OR
${INVENIO_WEB_INSTANCE} facet_search_setting create \
       "Location"	"地域"	"geoLocation.geoLocationPlace"	"[]"	True   SelectBox     3      True    OR
${INVENIO_WEB_INSTANCE} facet_search_setting create \
       "Temporal"	"時間的範囲"	"temporal"	"[]"	True   SelectBox     4      True    OR
${INVENIO_WEB_INSTANCE} facet_search_setting create \
       "Topic"	"トピック"	"subject.value"	"[]"	True   SelectBox     5      True    OR
${INVENIO_WEB_INSTANCE} facet_search_setting create \
       "Distributor"	"配布者"	"contributor.contributorName"	"[{'agg_value': 'Distributor', 'agg_mapping': 'contributor.@attributes.contributorType'}]"	True   SelectBox     6      True    OR
${INVENIO_WEB_INSTANCE} facet_search_setting create \
       "Data Type"	"デ一タタイプ"	"description.value"	"[{'agg_value': 'Other', 'agg_mapping': 'description.descriptionType'}]"	True   SelectBox     7      True    OR
# create-facet-search-setting-end
