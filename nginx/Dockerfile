FROM ubuntu:focal AS nginx-with-shib

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /tmp

RUN apt-get update -y
RUN apt-get install -y \
    	    wget \
	    curl \
	    gnupg2 \
	    ca-certificates \
	    lsb-release \
	    unzip \
	    uuid-dev \
	    dpkg-dev && \
    echo "deb http://nginx.org/packages/ubuntu focal nginx" | tee /etc/apt/sources.list.d/nginx.list && \
    echo "deb-src http://nginx.org/packages/ubuntu focal nginx" | tee -a /etc/apt/sources.list.d/nginx.list && \
    curl -fsSL https://nginx.org/keys/nginx_signing.key | apt-key add - && \
    apt-get update -y && \
    apt-get source -y nginx=1.20.1 && \
    apt-get build-dep -y nginx=1.20.1 && \
    wget "https://github.com/samizdatco/nginx-http-auth-digest/archive/master.zip" -O nginx-http-auth-digest.zip && \
    # https://github.com/nginx-shib/nginx-http-shibboleth
    wget "https://github.com/nginx-shib/nginx-http-shibboleth/archive/v2.0.1.tar.gz" -O nginx-http-shibboleth-2.0.1.tar.gz && \
    wget "https://github.com/openresty/headers-more-nginx-module/archive/v0.33.tar.gz" -O headers-more-nginx-module-0.33.tar.gz && \
    wget "https://github.com/FRiCKLE/ngx_cache_purge/archive/2.3.tar.gz" -O ngx_cache_purge-2.3.tar.gz && \
    unzip nginx-http-auth-digest.zip && \
    tar zxf nginx-http-shibboleth-2.0.1.tar.gz && \
    tar zxf headers-more-nginx-module-0.33.tar.gz && \
    tar zxf ngx_cache_purge-2.3.tar.gz && \
    sed -i "s#--modules-path=/usr/lib/nginx/modules#--modules-path=/usr/lib/nginx/modules \
    	--add-module=/tmp/headers-more-nginx-module-0.33 \
	--add-module=/tmp/nginx-http-shibboleth-2.0.1 \
	--add-module=/tmp/nginx-http-auth-digest-master \
	--add-module=/tmp/ngx_cache_purge-2.3 #g" nginx-1.20.1/debian/rules && \
	cd nginx-1.20.1 && dpkg-buildpackage -b

FROM ubuntu:focal AS nginx-stage_1

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && \
    apt-get install -y \
    	    openssl \
	    wget \
	    curl \
	    unzip \
	    supervisor \
	    shibboleth-sp-common \
	    shibboleth-sp-utils \
	    php-fpm php-curl

WORKDIR /tmp
COPY --from=nginx-with-shib /tmp/nginx_1.20.1-1~focal_arm64.deb .
COPY --from=nginx-with-shib /tmp/nginx-dbg_1.20.1-1~focal_arm64.deb .
RUN dpkg -i nginx_1.20.1-1~focal_arm64.deb


ADD supervisord.conf /etc/supervisor/supervisord.conf
ADD shibboleth2.xml /etc/shibboleth/shibboleth2.xml
ADD attribute-map.xml /etc/shibboleth/attribute-map.xml
ADD attribute-policy.xml /etc/shibboleth/attribute-policy.xml
RUN sed -i 's/\/run\/php/\/tmp/g' /etc/php/7.4/fpm/php-fpm.conf && \
    sed -i 's/\/run\/php/\/tmp/g' /etc/php/7.4/fpm/pool.d/www.conf

ADD ./keys/server.crt /etc/shibboleth/server.crt
ADD ./keys/server.key /etc/shibboleth/server.key

RUN rm /etc/nginx/conf.d/default.conf && \
    rm /etc/nginx/nginx.conf
ADD weko.conf /etc/nginx/conf.d/
ADD nginx.conf /etc/nginx/nginx.conf
ADD ./keys/server.crt /etc/nginx/server.crt
ADD ./keys/server.key /etc/nginx/server.key
ADD ./idp-metadata.xml /etc/shibboleth/idp-metadata.xml
ADD ./orthros-idp-metadata.xml /etc/shibboleth/orthros-idp-metadata.xml
ADD ./htpasswd /etc/nginx/.htpasswd
ADD ./htdigest /etc/nginx/.htdigest
ADD redirect_list.map /etc/nginx/redirect_list.map

RUN chmod 400 /etc/nginx/server.key

RUN mkdir  /usr/share/nginx/html/secure
#ADD ./phpinfo.php /usr/share/nginx/html/secure/phpinfo.php
#ADD ./index.php /usr/share/nginx/html/secure/index.php
ADD ./login.php /usr/share/nginx/html/secure/login.php

ADD ./shib_clear_headers /etc/nginx/shib_clear_headers
ADD ./shib_fastcgi_params /etc/nginx/shib_fastcgi_params


CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]

