FROM phusion/baseimage:0.10.1
LABEL Name=handle_svr Version=0.0.1

## Image config

# Use baseimage-docker's init process.
CMD ["/sbin/my_init"]

# Update installed APT packages
RUN apt-get update && apt-get upgrade -y -o Dpkg::Options::="--force-confold"

RUN apt-get install -y ntp wget openjdk-8-jre python3 mysql-client libmysql-java sqlite3 libpostgresql-jdbc-java aria2

# Cleanup
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

## Handle Server setup

# Get the handle server package and put it in the container
WORKDIR /tmp
RUN aria2 -x5 http://www.handle.net/hnr-source/handle-9.1.0-distribution.tar.gz
RUN mkdir -p /opt/handle && tar xf /tmp/handle-9.1.0-distribution.tar.gz -C /opt/handle --strip-components=1

# Add the jdbc connector so it gets loaded
RUN ln -s /usr/share/java/mysql-connector-java.jar /opt/handle/lib/mysql-connector-java.jar
RUN ln -s /usr/share/java/postgresql.jar /opt/handle/lib/postgresql.jar
WORKDIR /opt/handle/lib/
RUN aria2 -x5 https://bitbucket.org/xerial/sqlite-jdbc/downloads/sqlite-jdbc-3.30.1.jar

# Copy over the handle base configs and build script
COPY handle/ /home/handle/

# Create the working directory for the handle server that will run in the container
RUN mkdir -p /var/handle/svr/logs

# Redirect log files to stdout/stderr
RUN ln -sf /dev/stdout /var/handle/svr/logs/access.log \
    && ln -sf /dev/stderr /var/handle/svr/logs/error.log

# Install Handle server as a service
RUN mkdir /etc/service/handle
COPY handle.sh /etc/service/handle/run
RUN chmod +x /etc/service/handle/run

