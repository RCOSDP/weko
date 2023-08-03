# -*- coding: utf-8 -*-
# 
# 
# 


from invenio_stats.utils import get_aggregations
from weko_index_tree.api import Indexes
from flask import current_app
from weko_search_ui.utils import get_doi_prefix
from invenio_search import RecordsSearch
from weko_schema_ui.models import PublishStatus
from elasticsearch import Elasticsearch, helpers
import datetime
import sys
import re

def count():
    today = datetime.date.today()
    evaluate_date = "{}-03-31".format(today.year)
    if len(sys.argv) > 1:
        date_pattern = re.compile('(\d{4})-(\d{1,2})-(\d{1,2})')
        s = sys.argv[1]
        result = date_pattern.search(s)
        if result:
            evaluate_date = s

    repo_name = current_app.config.get('WEB_HOST_NAME','')

    indexes = Indexes.get_public_indexes_list()
    indexes_query = []

    if indexes:
        indexes_num = len(indexes)
        div_indexes = []
        max_clause_count = current_app.config.get(
            'OAISERVER_ES_MAX_CLAUSE_COUNT', 1024)
        for div in range(0, int(indexes_num / max_clause_count) + 1):
            e_right = div * max_clause_count
            e_left = (div + 1) * max_clause_count \
                if indexes_num > (div + 1) * max_clause_count \
                else indexes_num
            div_indexes.append({
                "terms": {
                    "path": indexes[e_right:e_left]
                }
            })
        indexes_query.append({
            "bool": {
                "should": div_indexes
            }
        })

    aggs_query = {
        "size": 0,
        "aggs": {
            "aggs_public": {
                "filter": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "publish_status": PublishStatus.PUBLIC.value
                                }
                            },
                            {
                                "range": {
                                    "publish_date": {
                                        "lte": evaluate_date
                                    }
                                }
                            }
                        ],
                        "should": indexes_query
                    }
                }
            }
        },
        "query": {
            "bool": {
                "must": [
                    {
                        "term":
                        {
                            "relation_version_is_last": True
                        }
                    },
                    {
                        "exists":
                        {
                            "field": "path"
                        }
                    },
                    {
                        "terms":
                        {
                            "publish_status": [PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value]
                        }
                    }
                ]
            }
        }
    }

    aggs_results = get_aggregations(
        current_app.config['SEARCH_UI_SEARCH_INDEX'], aggs_query)

    public_item_count = aggs_results['aggregations']['aggs_public']['doc_count']
    item_count = aggs_results['hits']['total']
    private_item_count = item_count-public_item_count


    aggs_query = {
        "size": 0,
        "aggs": {
            "with_contents_item_count": {
                "filter": {
                    "bool": {
                        "must": [
                            {
                                "term": {
                                    "publish_status": PublishStatus.PUBLIC.value
                                }
                            },
                            {
                                "range": {
                                    "publish_date": {
                                        "lte": evaluate_date
                                    }
                                }
                            },{"exists":{"field":"file"}}
                        ],
                        "should": indexes_query
                    }
                }
            }
        },
        "query": {
            "bool": {
                "must": [
                    {
                        "term":
                        {
                            "relation_version_is_last": True
                        }
                    },
                    {
                        "exists":
                        {
                            "field": "path"
                        }
                    },
                    {
                        "terms":
                        {
                            "publish_status": [PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value]
                        }
                    },
                    {
                        "range": {
                            "publish_date": {
                                "lte": evaluate_date
                            }
                        }
                    }
                ]
            }
        }
    }
    aggs_results = get_aggregations(
        current_app.config['SEARCH_UI_SEARCH_INDEX'], aggs_query)

    with_contents_item_count = aggs_results['aggregations']['with_contents_item_count']['doc_count']
    no_contents_item_count = item_count - with_contents_item_count


    aggs_query = '{"query":{"range":{"timestamp":{"gte":"now-1d","lte":"now"}}},"aggs":{"total":{"sum":{"field":"unique_count"}}},"size":0}'

    aggs_results = get_aggregations(
        current_app.config.get("SEARCH_INDEX_PREFIX", "tenant1") + "stats-file-download", aggs_query)

    download_num = aggs_results['aggregations']['total']['value']

    ETD_count = 0

    search = RecordsSearch(index=current_app.config['INDEXER_DEFAULT_INDEX']).sort(
                {'control_number': {'order': 'asc'}}
            )

    search = search.query('range',**{"dateGranted":{"gte":"2013-04-01"}})
    search = search.query('match', **{'relation_version_is_last': 'true'})
    search = search.query('terms', **{'publish_status': [PublishStatus.PUBLIC.value, PublishStatus.PRIVATE.value]})
    search = search.query('exists',**{"field": "path"})

    for h in search.scan():
        if 'type' in h and 'accessRights' in h:
            if ('doctoral thesis' in h.type) and ('open access' in h.accessRights):
                ETD_count=ETD_count + 1


            

    JaLCDOI_prefix = get_doi_prefix('JaLC')

    host_name = ""
    repo_status = ""

    print("evaluate_date,repo_name,host_name,repo_status,item_count,public_item_count,private_item_count,with_contents_item_count,no_contents_item_count,download_num,ETD_count,JaLCDOI_prefix")
    print("{},{},{},{},{},{},{},{},{},{},{},{}".format(evaluate_date,repo_name,host_name,repo_status,item_count,public_item_count,private_item_count,with_contents_item_count,no_contents_item_count,download_num,ETD_count,JaLCDOI_prefix))

if __name__ == '__main__':
    count()


