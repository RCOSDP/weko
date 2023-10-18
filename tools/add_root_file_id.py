
import os

from elasticsearch import Elasticsearch, helpers

es = Elasticsearch(
        "http://" + os.environ.get("INVENIO_ELASTICSEARCH_HOST", "localhost") + ":9200"
    )

    
def add_root_file_id(index, doc_type):
    errors = []
    _query = '{"query": {"bool": {"must_not": {"exists": {"field": "root_file_id"}}}}}'
    results = helpers.scan(
            es,
            index=index,
            preserve_order=True,
            query=_query,
        )
    for r in results:
        id = r['_id']
        source = r.get('_source')
        try:
            es.update(
                index=index,
                doc_type=doc_type,
                body={
                    "doc":{
                        "root_file_id":source["file_id"]
                    }
                },
                id=id
            )
            print("update data: {}".format(id))
        except:
            errors.append(id)
    return errors

    
if __name__ == "__main__":
    index = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-stats-file-download"
    doc_type = "file-download-day-aggregation"
    print("# {}".format(index))
    errors = add_root_file_id(index, doc_type)
    print("raise error item: {}".format(errors))
    index_event = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-events-stats-file-download"
    doc_type_event = "stats-file-download"
    print("# {}".format(index_event))
    errors = add_root_file_id(index_event, doc_type_event)
    print("raise error item: {}".format(errors))

