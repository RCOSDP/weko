
import os

from elasticsearch import Elasticsearch, helpers

from invenio_db import db
from invenio_files_rest.models import ObjectVersion

es = Elasticsearch(
        "http://" + os.environ.get("INVENIO_ELASTICSEARCH_HOST", "localhost") + ":9200"
    )

    
def add_root_file_id(index):
    errors = []
    updated = []
    _query = '{"query":{"bool":{"should":[{"bool":{"must_not":{"exists":{"field":"root_file_id"}}}},{"term":{"root_file_id":""}}]}}}'
    results = helpers.scan(
            es,
            index=index,
            preserve_order=True,
            query=_query,
        )
    _bulk = []
    for r in results:
        id = r['_id']
        source = r.get('_source')
        _index = r.get('_index')
        _type = r.get('_type')
        if "bucket_id" in source:
            with db.session.begin_nested():
                file = None
                if "file_key" in source and source['file_key'] is not "":
                    file = ObjectVersion.query.filter_by(key=source["file_key"],bucket_id=source['bucket_id']).first() 
                else:
                    file = ObjectVersion.query.filter_by(bucket_id=source["bucket_id"]).first()
                if file:
                    _body = {"file_keys":file.key,"root_file_id":file.root_file_id,"file_id":file.file_id}
                    _bulk.append({'_op_type': 'update',"_index":_index,"_type":_type,"_id":id,"doc":_body})
                    updated.append(id)
                else:
                    errors.append(id)
    if len(_bulk)>0:
        try:
            res = helpers.bulk(es, _bulk)
            print("update: {}".format(updated))
            print("result: {}".format(res))
        except Exception as e:
            errors.append(e)
    return errors

    
if __name__ == "__main__":
    index = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-stats-file-download"
    print("# {}".format(index))
    errors = add_root_file_id(index)
    print("raise error item: {}".format(errors))
    index_event = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-events-stats-file-download"
    print("# {}".format(index_event))
    errors = add_root_file_id(index_event)
    print("raise error item: {}".format(errors))
    index_event = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-events-stats-file-preview"
    print("# {}".format(index_event))
    errors = add_root_file_id(index_event)
    print("raise error item: {}".format(errors))
    index_event = os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-events-stats-file-preview"
    print("# {}".format(index_event))
    errors = add_root_file_id(index_event)
    print("raise error item: {}".format(errors))
