# -*- coding: utf-8 -*-
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

# Use Elasticsearch 6.
FROM docker.elastic.co/elasticsearch/elasticsearch:6.8.23
WORKDIR /usr/share/elasticsearch
ARG ELASTICSEARCH_S3_ACCESS_KEY
ARG ELASTICSEARCH_S3_SECRET_KEY
ARG ELASTICSEARCH_S3_ENDPOINT
ARG ELASTICSEARCH_S3_BUCKET
ENV ELASTICSEARCH_S3_ACCESS_KEY=${ELASTICSEARCH_S3_ACCESS_KEY}
ENV ELASTICSEARCH_S3_SECRET_KEY=${ELASTICSEARCH_S3_SECRET_KEY}
ENV ELASTICSEARCH_S3_ENDPOINT=${ELASTICSEARCH_S3_ENDPOINT}
ENV ELASTICSEARCH_S3_BUCKET=${ELASTICSEARCH_S3_BUCKET}
RUN mkdir -p backups && \
    chown -R elasticsearch:elasticsearch ./backups
COPY scripts/provision-elasticsearch.sh /tmp/
COPY elasticsearch/dic/character/kui.txt /usr/share/elasticsearch/config
# Install Elasticsarch plugins:
RUN /tmp/provision-elasticsearch.sh
