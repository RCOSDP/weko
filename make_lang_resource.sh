#!/bin/bash
# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
# :license: BSD, see LICENSE for details.

date --iso-8601="minutes"
LNG=$1
for module_path in modules/*/; do
  if [[ ${module_path} =~ ^modules/(invenio-|weko-).+$ ]]; then
    if [[ ${module_path} =~ ^modules/(invenio-admin).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-app).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-db).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-iiif).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-indexer).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-mail).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-oaiharvester).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-oaiharvester).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-queues).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-records).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-records-rest).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-resourcesyncclient).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-resourcesyncserver).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-s3).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(invenio-stats).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(weko-bulkupdate).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(weko-handle).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(weko-logging).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(weko-redis).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(weko-sitemap).+$ ]]; then
      continue
    fi
    if [[ ${module_path} =~ ^modules/(weko-swordserver).+$ ]]; then
      continue
    fi
    (cd ${module_path} && python setup.py init_catalog -l ${LNG})
    # if test -d ${module_path}/*/translations/${LNG}; then
    #   echo "### update catalog for ${module_path%?} ###"
    #   (cd ${module_path} && python setup.py update_catalog -l ${LNG})
    # else
    #   echo "### init catalog for ${module_path%?} ###"
    #   (cd ${module_path} && python setup.py init_catalog -l ${LNG})
    # fi
  fi
done
date --iso-8601="minutes"
