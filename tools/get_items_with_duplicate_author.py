
import sys,os
from os.path import dirname, join
import csv
from flask import current_app

from invenio_indexer.api import RecordIndexer


def get_original_data(filename, institution):
    original_data = []
    with open(filename, "r") as f:
        reader = csv.reader(f)
        l = [row for row in reader]
        for ll in l[1:]:
            if institution in ll[0]:
                original_data.append(ll[1])
    return original_data

def get_items_with_duplicate_author(origin_data, institution):
    indexer = RecordIndexer()
    record_index = current_app.config['SEARCH_UI_SEARCH_INDEX']
    record_doc_type = current_app.config['INDEXER_DEFAULT_DOCTYPE']

    for pk_id in origin_data:
        query = {
            "query": {
                "bool": {
                    "must": [
                        { "match": { "relation_version_is_last": "true" } },
                        {"terms": {"author_link.raw": [str(pk_id)]}}
                    ]
                }
            },
            "size": 10000,
            "from": 0
        }
        search_result = indexer.client.search(
            index=record_index,doc_type=record_doc_type,body=query
        )
        if search_result["hits"]["total"]>0:
            hits = search_result["hits"]["hits"]
            for result in hits:
                recid = result.get("_source").get("control_number")
                metadata = result.get("_source",{}).get("_item_metadata")
                for k, v in metadata.items():
                    if isinstance(v, dict) \
                        and v.get("attribute_value_mlt") \
                            and isinstance(v["attribute_value_mlt"], list):
                        data_list = v["attribute_value_mlt"]
                        for data in data_list:
                            is_duplicate = False
                            # WEKO IDが対象と同じ
                            if isinstance(data, dict) and "nameIdentifiers" in data:
                                for id in data["nameIdentifiers"]:
                                    if id["nameIdentifierScheme"] == "WEKO":
                                        if id["nameIdentifier"] == str(pk_id):
                                            is_duplicate=True
                                            break
                            if is_duplicate:
                                full_name = data.get("creatorNames")[0].get("creatorName","") if len(data.get("creatorNames",[])) > 0 else ""
                                given_name = data.get("givenNames")[0].get("givenName","") if len(data.get("creatorNames",[])) > 0 else ""
                                family_name = data.get("familyNames")[0].get("familyName","") if len(data.get("creatorNames",[])) > 0 else ""
                                print("# {institution},{recid},{pk_id},'{full_name}',{first_name},{family_name}".format(
                                    institution=institution,
                                    recid=recid,
                                    pk_id=pk_id,
                                    full_name=full_name,
                                    first_name=given_name,
                                    family_name=family_name
                                ))
            
if __name__ == '__main__':
    args = sys.argv

    original_data_path = args[1] if len(args) == 2 else join(dirname(__file__), "duplicate_author_id_original.csv")
    institution = os.environ.get('SEARCH_INDEX_PREFIX', '')
    original_data = get_original_data(original_data_path, institution)
    
    get_items_with_duplicate_author(original_data, institution)