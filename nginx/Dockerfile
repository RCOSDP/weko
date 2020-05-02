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

FROM nginx:stable AS nginx-with-shib

# Make apt-get commands temporarily non-interactive
# Solution from https://github.com/phusion/baseimage-docker/issues/58
# Update apt cache to use fastest local mirror
RUN \
export DEBIAN_FRONTEND=noninteractive && \
export DEBCONF_NONINTERACTIVE_SEEN=true && \
apt-get update && \
apt-get install -y man netcat wget curl openssl nano less sudo procps git supervisor && \
apt-get install -y shibboleth-sp-common shibboleth-sp-utils php-fpm gcc pcre pcre-devel make perl httpd-tools
#apt-get install -y shibboleth-sp2-common shibboleth-sp2-utils

# Build nginx shibboleth modules, taken from
# https://github.com/ConsortiumGARR/idem-tutorials/blob/master/idem-community/HOWTO-Shibboleth/Service-Provider/Debian/HOW%20TO%20SETUP%20A%20SHIBBOLETH%20SP%20WITH%20NGINX.md
RUN mkdir -p /root/nginx-modules/deb
WORKDIR /root/nginx-modules
RUN wget "http://hg.nginx.org/pkg-oss/archive/tip.tar.gz" -o /root/nginx-modules/tip.tar.gz
# cant work!
#ADD tip.tar.gz /root/nginx-modules/tip.tar.gz

RUN \
tar -xvf tip.tar.gz && mv pkg-oss-* pkg-oss/ && \
git clone https://github.com/openresty/headers-more-nginx-module.git && \
git clone https://github.com/nginx-shib/nginx-http-shibboleth.git && \
pkg-oss/build_module.sh -y -o /root/nginx-modules/deb/ -n shibboleth -v `nginx -v 2>&1 | sed -n -e 's|^.*/||p' | tr -d '\n'` nginx-http-shibboleth/ && \
pkg-oss/build_module.sh -y -o /root/nginx-modules/deb/ -n headers-more -v `nginx -v 2>&1 | sed -n -e 's|^.*/||p' | tr -d '\n'` headers-more-nginx-module && \
cp -vf nginx-http-shibboleth/includes/* /etc/nginx


FROM nginx:stable

RUN mkdir -p /root/nginx-modules/deb
WORKDIR /root/nginx-modules
COPY --from=nginx-with-shib /root/nginx-modules/deb /root/nginx-modules/deb
COPY --from=nginx-with-shib /etc/nginx /etc/nginx
#RUN wget "https://github.com/atomx/nginx-http-auth-digest/archive/master.zip" -O /root/nginx-modules/nginx-http-auth-digest.zip

# Create _shibd uid.gid so we can control the numeric value of uid:gid
RUN \
adduser nginx _shibd && \
adduser nginx www-data

RUN apt-get install -y php-curl

ADD shibboleth.conf /etc/supervisor/conf.d/shibboleth.conf
ADD shibboleth2.xml /etc/shibboleth/shibboleth2.xml
ADD attribute-map.xml /etc/shibboleth/attribute-map.xml
ADD attribute-policy.xml /etc/shibboleth/attribute-policy.xml

ADD ./keys/server.crt /etc/shibboleth/server.crt
ADD ./keys/server.key /etc/shibboleth/server.key


RUN rm /etc/nginx/conf.d/default.conf
RUN rm /etc/nginx/nginx.conf
ADD weko.conf /etc/nginx/conf.d/
ADD nginx.conf /etc/nginx/nginx.conf
ADD ./keys/server.crt /etc/nginx/server.crt
ADD ./keys/server.key /etc/nginx/server.key
ADD ./idp-metadata.xml /etc/shibboleth/idp-metadata.xml

RUN chmod 400 /etc/nginx/server.key

RUN mkdir  /usr/share/nginx/html/secure
ADD ./phpinfo.php /usr/share/nginx/html/secure/phpinfo.php
ADD ./index.php /usr/share/nginx/html/secure/index.php
ADD ./login.php /usr/share/nginx/html/secure/login.php

ADD ./shib_clear_headers /etc/nginx/shib_clear_headers
ADD ./shib_fastcgi_params /etc/nginx/shib_fastcgi_params


CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/shibboleth.conf"]
