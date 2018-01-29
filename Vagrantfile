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

#OS = 'centos/7'
OS = 'ubuntu/trusty64'

Vagrant.configure("2") do |config|

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
  end

  config.vm.define "web" do |web|
    web.vm.box = OS
    web.vm.hostname = 'web'
    web.vm.provision "file", source: ".inveniorc", destination: ".inveniorc"
    web.vm.provision "shell", inline: "source .inveniorc && /vagrant/scripts/provision-web.sh", privileged: false
    web.vm.network "forwarded_port", guest: 80, host: 80
    web.vm.network "forwarded_port", guest: 5000, host: 5000
    web.vm.network "private_network", ip: ENV.fetch('INVENIO_WEB_HOST','192.168.50.10')
    web.vm.provider :virtualbox do |vb|
      vb.customize ["modifyvm", :id, "--memory", "1024"]
      vb.customize ["modifyvm", :id, "--cpus", 2]
    end
  end

  config.vm.define "postgresql" do |postgresql|
    postgresql.vm.box = OS
    postgresql.vm.hostname = 'postgresql'
    postgresql.vm.provision "file", source: ".inveniorc", destination: ".inveniorc"
    postgresql.vm.provision "shell", inline: "source .inveniorc && /vagrant/scripts/provision-postgresql.sh", privileged: false
    postgresql.vm.network "private_network", ip: ENV.fetch('INVENIO_POSTGRESQL_HOST','192.168.50.11')
  end

  config.vm.define "redis" do |redis|
    redis.vm.box = OS
    redis.vm.hostname = 'redis'
    redis.vm.provision "file", source: ".inveniorc", destination: ".inveniorc"
    redis.vm.provision "shell", inline: "source .inveniorc && /vagrant/scripts/provision-redis.sh", privileged: false
    redis.vm.network "private_network", ip: ENV.fetch('INVENIO_REDIS_HOST','192.168.50.12')
  end

  config.vm.define "elasticsearch" do |elasticsearch|
    elasticsearch.vm.box = OS
    elasticsearch.vm.hostname = 'elasticsearch'
    elasticsearch.vm.provision "file", source: ".inveniorc", destination: ".inveniorc"
    elasticsearch.vm.provision "shell", inline: "source .inveniorc && /vagrant/scripts/provision-elasticsearch.sh", privileged: false
    elasticsearch.vm.network "private_network", ip: ENV.fetch('INVENIO_ELASTICSEARCH_HOST','192.168.50.13')
  end

  config.vm.define "rabbitmq" do |rabbitmq|
    rabbitmq.vm.box = OS
    rabbitmq.vm.hostname = 'rabbitmq'
    rabbitmq.vm.provision "file", source: ".inveniorc", destination: ".inveniorc"
    rabbitmq.vm.provision "shell", inline: "source .inveniorc && /vagrant/scripts/provision-rabbitmq.sh", privileged: false
    rabbitmq.vm.network "private_network", ip: ENV.fetch('INVENIO_RABBITMQ_HOST','192.168.50.14')
  end

  config.vm.define "worker" do |worker|
    worker.vm.box = OS
    worker.vm.hostname = 'worker'
    worker.vm.provision "file", source: ".inveniorc", destination: ".inveniorc"
    worker.vm.provision "shell", inline: "source .inveniorc && /vagrant/scripts/provision-worker.sh", privileged: false
    worker.vm.network "private_network", ip: ENV.fetch('INVENIO_WORKER_HOST','192.168.50.15')
  end

end
