import os
from elasticsearch import Elasticsearch
elasticsearch_host = os.environ.get('INVENIO_ELASTICSEARCH_HOST')
prefix = os.environ.get('SEARCH_INDEX_PREFIX')
con = Elasticsearch(host=elasticsearch_host, verify_certs=False)

# Delete all aliases
indices = con.cat.aliases(h='index',s='index').splitlines()
aliases = con.cat.aliases(h='alias',s='index').splitlines()
zipped = zip(indices,aliases)
for index, alias in zipped:
    if '{}'.format(prefix) in index:
        con.indices.delete_alias(index=index, name=alias)

# Create aliases for WEKO3
alias_name = "{}-weko".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-weko*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-weko'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})


alias_name = "{}-authors".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-authors*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-authors'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-events-stats-celery-task".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-events-stats-celery-task*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-events-stats-celery-task'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-events-stats-file-download".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-events-stats-file-download*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-events-stats-file-download'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-events-stats-file-preview".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-events-stats-file-preview*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-events-stats-file-preview'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-events-stats-item-create".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-events-stats-item-create*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-events-stats-item-create'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-events-stats-record-view".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-events-stats-record-view*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-events-stats-record-view'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-events-stats-search".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-events-stats-search*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-events-stats-search'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-events-stats-top-view".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-events-stats-top-view*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-events-stats-top-view'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-stats-celery-task".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-stats-celery-task*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-stats-celery-task'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-stats-file-download".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-stats-file-download*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-stats-file-download'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})


alias_name = "{}-stats-file-preview".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-stats-file-preview*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-stats-file-preview'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})

alias_name = "{}-stats-item-create".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-stats-item-create*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-stats-item-create'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})


alias_name = "{}-stats-record-view".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-stats-record-view*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-stats-record-view'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})


alias_name = "{}-stats-search".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-stats-search*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-stats-search'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})


alias_name = "{}-stats-top-view".format(prefix)
last_index = ""
indices = con.cat.indices(index='{}-stats-top-view*'.format(prefix), h='index',s='creation.date.string').splitlines()
for index in indices:
    if '{}-stats-top-view'.format(prefix) in index:
        con.indices.put_alias(index=index, name=alias_name)
        last_index = index
if last_index is not "":
    con.indices.put_alias(index=last_index, name=alias_name,body={"is_write_index":True})
