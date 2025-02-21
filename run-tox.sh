#!/bin/bash
# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018, 2019, 2020 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
# :license: BSD, see LICENSE for details.

date --iso-8601="minutes"
pip install tox
pip install tox-setuptools-version
pip install pytest-timeout
for module_path in modules/*/; do
  if [[ ${module_path} =~ ^modules/(invenio-|weko-).+$ ]] && [[ -d ${module_path}tests ]]; then
    # if [[ ${module_path} =~ ^modules/(invenio-accounts).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-communities).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi 
    # if [[ ${module_path} =~ ^modules/(invenio-db).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-deposit).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-files-rest).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-iiif).+$ ]]; then    
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-indexer).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi   
    # if [[ ${module_path} =~ ^modules/(invenio-mail).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-oaiharvester).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-oaiserver).+$ ]] ; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-oauth2server).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-previewer).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-queues).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-records-rest).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-records).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi 
    # if [[ ${module_path} =~ ^modules/(invenio-resourcesyncclient).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-resourcesyncserver).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-s3).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(invenio-stats).+$ ]];then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-accounts).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-admin).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-authors).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-bulkupdate).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-deposit).+$ ]];then  
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-gridlayout).+$ ]];then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi 
    # if [[ ${module_path} =~ ^modules/(weko-groups).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi 
    # if [[ ${module_path} =~ ^modules/(weko-handle).+$ ]];then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-index-tree).+$ ]];then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi 
    # if [[ ${module_path} =~ ^modules/(weko-indextree-journal).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-items-autofill).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-items-ui).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-itemtypes-ui).+$ ]];then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-logging).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-plugins).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-records-ui).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/weko-records/$ ]];then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-schema-ui).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-search-ui).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-sitemap).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-swordserver).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-theme).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-user-profiles).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi
    # if [[ ${module_path} =~ ^modules/(weko-workflow).+$ ]]; then
    #   echo "### skip tests for ${module_path%?} ###"
    #   continue
    # fi

    echo "### Running tests for ${module_path%?} ###"
    (cd ${module_path} && tox >tox.result;rm -f tox.result.gz;gzip tox.result)
    # (cd ${module_path} && tox >tox.result;rm -f tox.result.gz;gzip tox.result;rm -rf .tox)
    echo
  fi
done
date --iso-8601="minutes"
