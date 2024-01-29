
import sys,os
from os.path import dirname, join
import csv

from elasticsearch import Elasticsearch

names_key_map = {
    "creator":{
        "names_key": "creatorNames",
        "name_key": "creatorName",
        "fnames_key": "familyNames",
        "fname_key": "familyName",
        "gnames_key": "givenNames",
        "gname_key": "givenName",
    },
    "contributor": {
        "names_key": "contributorNames",
        "name_key": "contributorName",
        "fnames_key": "familyNames",
        "fname_key": "familyName",
        "gnames_key": "givenNames",
        "gname_key": "givenName",
    },
    "full_name":{
        "names_key": "names",
        "name_key": "name",
        "fnames_key": "familyNames",
        "fname_key": "familyName",
        "gnames_key": "givenNames",
        "gname_key": "givenName",
    }
}
def get_original_data(filename):
    original_data = []
    with open(filename, "r") as f:
        reader = csv.reader(f)
        l = [row for row in reader]
        for ll in l[1:]:
            original_data.append((ll[0],ll[1]))
    return original_data

def get_items_with_duplicate_author(origin_data):
    for institution, pk_id in origin_data:
        try:
            es = Elasticsearch("http://"+os.environ.get('INVENIO_ELASTICSEARCH_HOST','localhost')+":9200")
            record_index = "{}-weko".format(institution.replace('-authors-author-v1.0.0',''))
            query = {
                "query": {
                    "bool": {
                        "must": [
                            { "match": { "relation_version_is_last": "true" } },
                            {"terms": {"author_link.raw": [str(pk_id)]}}
                        ]
                    }
                },
                "_source":{"excludes":["content"]},
                "size": 10000,
                "from": 0
            }
            search_result = es.search(index=record_index,body=query)
            if search_result["hits"]["total"]>0:
                hits = search_result["hits"]["hits"]
                for result in hits:
                    recid = result.get("_source").get("control_number")
                    metadata = result.get("_source",{}).get("_item_metadata")
                    for k, v in metadata.items():
                        if isinstance(v, dict) \
                            and v.get("attribute_value_mlt") \
                                and isinstance(v["attribute_value_mlt"], list):
                            attribute_name=v.get("attribute_name","")
                            data_list = v["attribute_value_mlt"]
                            for data in data_list:
                                is_duplicate = False
                                # WEKO IDが対象と同じ
                                if isinstance(data, dict) and "nameIdentifiers" in data:
                                    if 'creatorNames' in data:
                                        prop_type = 'creator'
                                    elif 'contributorNames' in data:
                                        prop_type = 'contributor'
                                    elif 'names' in data:
                                        prop_type = 'full_name'
                                    else:
                                        continue
                                    
                                    for id in data["nameIdentifiers"]:
                                        if id["nameIdentifierScheme"] == "WEKO":
                                            if id["nameIdentifier"] == str(pk_id):
                                                is_duplicate=True
                                                break
                                if is_duplicate:
                                    key_map = names_key_map[prop_type]
                                    full_name = data.get(key_map["names_key"])[0].get(key_map["name_key"],"") if len(data.get(key_map["names_key"],[])) > 0 else ""
                                    given_name = data.get(key_map["gnames_key"])[0].get(key_map["gname_key"],"") if len(data.get(key_map["gnames_key"],[])) > 0 else ""
                                    family_name = data.get(key_map["fnames_key"])[0].get(key_map["fname_key"],"") if len(data.get(key_map["fnames_key"],[])) > 0 else ""
                                    print('{institution},{pk_id},{recid},{attribute_name},{family_name},{given_name},"{full_name}","{json}"'.format(
                                        institution=institution,
                                        recid=recid,
                                        pk_id=pk_id,
                                        attribute_name=attribute_name,
                                        full_name=full_name,
                                        given_name=given_name,
                                        family_name=family_name,
                                        json=data
                                    ))
        except:
            import traceback
            traceback.print_exc()
            
if __name__ == '__main__':
    args = sys.argv

    original_data_path = args[1] if len(args) == 2 else join(dirname(__file__), "duplicate_author_id_original.csv")
    original_data = get_original_data(original_data_path)
    get_items_with_duplicate_author(original_data)