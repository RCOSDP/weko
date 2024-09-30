# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2024 National Institute of Informatics.
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

# Use Opensearch 2.
FROM opensearchproject/opensearch:2
WORKDIR /usr/share/opensearch
ARG OPENSEARCH_S3_ACCESS_KEY
ARG OPENSEARCH_S3_SECRET_KEY
ARG OPENSEARCH_S3_ENDPOINT
ARG OPENSEARCH_S3_BUCKET
ENV OPENSEARCH_S3_ACCESS_KEY=${OPENSEARCH_S3_ACCESS_KEY}
ENV OPENSEARCH_S3_SECRET_KEY=${OPENSEARCH_S3_SECRET_KEY}
ENV OPENSEARCH_S3_ENDPOINT=${OPENSEARCH_S3_ENDPOINT}
ENV OPENSEARCH_S3_BUCKET=${OPENSEARCH_S3_BUCKET}
ENV OPENSEARCH_INITIAL_ADMIN_PASSWORD=WekoOpensearch123!
ENV INVENIO_OPENSEARCH_USER=invenio
ENV INVENIO_OPENSEARCH_PASS=openpass123!

RUN mkdir -p backups && \
    chown -R opensearch:opensearch ./backups
COPY scripts/provision-opensearch.sh /tmp/
COPY opensearch/dic/character/kui.txt /usr/share/opensearch/config
USER root
RUN touch /.dockerenv
USER opensearch
# Install Opensearch plugins:
RUN /tmp/provision-opensearch.sh
