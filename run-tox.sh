#!/bin/bash
# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
# :license: BSD, see LICENSE for details.

date --iso-8601="minutes"
pip install tox
pip install tox-setuptools-version
pip install pytest-timeout
for module_path in modules/*/; do
  # if [[ ${module_path} =~ ^modules/(invenio-|weko-).+$ ]] && [[ -d ${module_path}tests ]]; then
  #   if [[ ${module_path} =~ ^modules/(invenio-accounts).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-communities).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-db).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-deposit).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-files-rest).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-iiif).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-indexer).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-mail).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-oaiharvester).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-oaiserver).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-oauth2server).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(invenio-previewer).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(invenio-queues).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(invenio-records-rest).+$ ]]||
  #   [[ ${module_path} =~ ^modules/(invenio-records).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(invenio-resourcesyncclient).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(invenio-resourcesyncserver).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(invenio-s3).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(invenio-stats).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-accounts).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-admin).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-authors).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-bulkupdate).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-deposit).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-gridlayout).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-groups).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(weko-handle).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-indextree-journal).+$ ]] || 
  #   [[ ${module_path} =~ ^modules/(weko-items-autofill).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-items-ui).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-itemtypes-ui).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-logging).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-plugins).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-records-ui).+$ ]]|| 
  #   [[ ${module_path} =~ ^modules/(weko-records).+$ ]]||
  #   [[ ${module_path} =~ ^modules/(weko-schema-ui).+$ ]]||
  #   [[ ${module_path} =~ ^modules/(weko-search-ui).+$ ]]||
  #   [[ ${module_path} =~ ^modules/(weko-sitemap).+$ ]]||
  #   [[ ${module_path} =~ ^modules/(weko-swordserver).+$ ]]||
  #   [[ ${module_path} =~ ^modules/(weko-theme).+$ ]]||
  #   [[ ${module_path} =~ ^modules/(weko-user-profiles).+$ ]]||
  #   [[ ${module_path} =~ ^modules/(weko-workflow).+$ ]]; then
  #     echo "### skip tests for ${module_path%?} ###"
  #     continue
  #   fi
    echo "### Running tests for ${module_path%?} ###"
    (cd ${module_path} && tox >tox.result;rm -f tox.result.gz;gzip tox.result;rm -rf .toxq)
    echo
  fi
done
date --iso-8601="minutes"
