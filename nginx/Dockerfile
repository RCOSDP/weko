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

FROM nginx:stable

# Make apt-get commands temporarily non-interactive
# Solution from https://github.com/phusion/baseimage-docker/issues/58
# Update apt cache to use fastest local mirror
RUN \
export DEBIAN_FRONTEND=noninteractive && \
export DEBCONF_NONINTERACTIVE_SEEN=true && \
apt-get update && \
apt-get install -y man netcat wget curl openssl nano less sudo procps git supervisor shibboleth-sp-common shibboleth-sp-utils

# Build nginx shibboleth modules, taken from
# https://github.com/ConsortiumGARR/idem-tutorials/blob/master/idem-community/HOWTO-Shibboleth/Service-Provider/Debian/HOW%20TO%20SETUP%20A%20SHIBBOLETH%20SP%20WITH%20NGINX.md
RUN mkdir -p /root/nginx-modules/deb
WORKDIR /root/nginx-modules
ADD http://hg.nginx.org/pkg-oss/archive/tip.tar.gz tip.tar.gz
RUN \
tar -xvf tip.tar.gz && mv pkg-oss-* pkg-oss/ && \
git clone https://github.com/openresty/headers-more-nginx-module.git && \
git clone https://github.com/nginx-shib/nginx-http-shibboleth.git && \
pkg-oss/build_module.sh -y -o /root/nginx-modules/deb/ -n shibboleth -v `nginx -v 2>&1 | sed -n -e 's|^.*/||p' | tr -d '\n'` nginx-http-shibboleth/ && \
pkg-oss/build_module.sh -y -o /root/nginx-modules/deb/ -n headers-more -v `nginx -v 2>&1 | sed -n -e 's|^.*/||p' | tr -d '\n'` headers-more-nginx-module && \
cp -vf nginx-http-shibboleth/includes/* /etc/nginx && \
rm -f deb/*-dbg_*.deb && dpkg -i deb/*.deb && \
rm -fr /root/debuild && rm -f tip.tar.gz && \
apt-get purge -y build-essential gcc make unzip wget mercurial git libpcre3-dev zlib1g-dev libssl-dev devscripts debhelper dpkg-dev quilt lsb-release && \
apt-get autoremove -y && \
apt-get clean -y

# Create _shibd uid.gid so we can control the numeric value of uid:gid
RUN \
adduser nginx _shibd && \
adduser nginx www-data

ADD shibboleth.conf /etc/supervisor/conf.d/shibboleth.conf
ADD shibboleth2.xml /etc/shibboleth/shibboleth2.xml 

RUN rm /etc/nginx/conf.d/default.conf
RUN rm /etc/nginx/nginx.conf
ADD weko.conf /etc/nginx/conf.d/
ADD nginx.conf /etc/nginx/nginx.conf
ADD ./keys/server.crt /etc/nginx/server.crt
ADD ./keys/server.key /etc/nginx/server.key

RUN chmod 400 /etc/nginx/server.key

CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/shibboleth.conf"]
