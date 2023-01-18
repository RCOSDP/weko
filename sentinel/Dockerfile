FROM redis:3

EXPOSE 26379

ADD sentinel.conf /etc/redis/sentinel.conf

RUN chown redis:redis /etc/redis/sentinel.conf

COPY sentinel-entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/sentinel-entrypoint.sh

ENTRYPOINT ["sentinel-entrypoint.sh"]