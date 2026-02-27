import time
import re
import os
import sys
import traceback
from elasticsearch import Elasticsearch

def update_es_records(ofqdn, nfqdn):
    """
    Update Elasticsearch records.
    Update Elasticsearch records, replacing all occurrences of `ofqdn` with `nfqdn`
    in specific fields such as OAI IDs and URLs, for all documents in the index.
    Connects to Elasticsearch using environment variables, iterates all documents,
    replaces `ofqdn` in relevant fields, updates documents, and logs progress/errors.

    Args:
        ofqdn (str): The original fully qualified domain name to be replaced.
        nfqdn (str): The new fully qualified domain name to use as a replacement.

    Behavior:
        - Connects to Elasticsearch using environment variables for host and index prefix.
        - Iterates through all documents in the target index.
        - For each document, replaces `ofqdn` with `nfqdn` in relevant fields.
        - Updates each document in Elasticsearch, preserving versioning.
        - Logs progress and errors.
        - Prints a summary of the operation upon completion.
    """
    HOST = os.getenv("INVENIO_ELASTICSEARCH_HOST")
    INDEX_PREFIX = os.getenv("SEARCH_INDEX_PREFIX")
    PORT = 9200
    index_name = f"{INDEX_PREFIX}-weko-item-v1.0.0"
    es = Elasticsearch(f"http://{HOST}:{PORT}")

    query = {
        "query": {
            "match_all": {}
        }
    }

    try:
        result_count = es.count(index=index_name, body=query)
        print(f"[INFO] {index_name}: Total items: {result_count['count']}")
    except Exception as e:
        print(f"[ERROR] {index_name}: Failed to get count")
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

    start_time = time.time()

    try:
        scroll = es.search(
            index=index_name,
            body=query,
            params={"version": "true"},
            scroll="2m",
            size=1000
        )
    except Exception as e:
        print(f"[ERROR] {index_name}: Failed to search")
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

    scroll_id = scroll['_scroll_id']
    hits = scroll['hits']['hits']

    failed_count = 0
    count = 0

    try:
        while hits:
            for hit in hits:
                doc_id = hit["_id"]
                source = hit["_source"]
                version = hit.get("_version", 1)

                # _oai -> id
                oai = source.get("_oai", {})
                oai_id = oai.get("id")
                if oai_id and ofqdn in oai_id:
                    new_oai_id = re.sub(re.escape(ofqdn), nfqdn, oai_id)
                    oai["id"] = new_oai_id

                # _item_metadata -> oid -> id
                item_metadata = source.get("_item_metadata", {})
                oai_meta = item_metadata.get("_oai", {})
                oai_meta_id = oai_meta.get("id")
                if oai_meta_id and ofqdn in oai_meta_id:
                    new_oai_meta_id = re.sub(re.escape(ofqdn), nfqdn, oai_meta_id)
                    oai_meta["id"] = new_oai_meta_id
                    item_metadata["_oai"] = oai_meta

                # file property -> url -> url
                for _, meta_val in item_metadata.items():
                    if isinstance(meta_val, dict) and meta_val.get("attribute_type") == "file":
                        for file_obj in meta_val.get("attribute_value_mlt", []):
                            url_dict = file_obj.get("url", {})
                            url_val = url_dict.get("url")
                            if url_val and ofqdn in url_val:
                                new_url = re.sub(re.escape(ofqdn), nfqdn, url_val)
                                file_obj["url"]["url"] = new_url

                # content -> url -> url
                if "content" in source and isinstance(source["content"], list):
                    for content_obj in source["content"]:
                        url_dict = content_obj.get("url", {})
                        url_val = url_dict.get("url")
                        if url_val and ofqdn in url_val:
                            new_url = re.sub(re.escape(ofqdn), nfqdn, url_val)
                            content_obj["url"]["url"] = new_url

                # file -> URI -> value
                if "file" in source and isinstance(source["file"], dict):
                    uri_list = source["file"].get("URI", [])
                    for uri_obj in uri_list:
                        uri_val = uri_obj.get("value")
                        if uri_val and ofqdn in uri_val:
                            new_uri = re.sub(re.escape(ofqdn), nfqdn, uri_val)
                            uri_obj["value"] = new_uri

                try:
                    es.index(
                        index=index_name,
                        doc_type="_doc",
                        id=doc_id,
                        body={**source, "_oai": oai, "_item_metadata": item_metadata},
                        version=version,
                        version_type="external_gte"
                    )
                except Exception as e:
                    print(f"[ERROR] {index_name}: Failed to update document ID: {doc_id}")
                    print(f"Error: {e}")
                    traceback.print_exc()
                    failed_count += 1
                    continue
                count += 1
                if count % 1000 == 0:
                    elapsed = time.time() - start_time
                    print(f"[INFO] {index_name}: {count} items processed (elapsed time: {elapsed:.2f} seconds)")

            scroll = es.scroll(scroll_id=scroll_id, scroll="2m")
            scroll_id = scroll['_scroll_id']
            hits = scroll['hits']['hits']

        total_elapsed = time.time() - start_time

        print(f"[INFO] {index_name}: {count} items replaced/updated (elapsed time: {total_elapsed:.2f} seconds)")
        print(f"[INFO] count(success, error): ({count}, {failed_count})")

    except Exception as e:
        print(f"[ERROR] {index_name}: Unexpected error")
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python replace_es_fqdn.py <old_fqdn> <new_fqdn>")
        sys.exit(1)
    ofqdn = sys.argv[1]
    nfqdn = sys.argv[2]
    update_es_records(ofqdn, nfqdn)
