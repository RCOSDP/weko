import os
import re
import sys
import time
import traceback

from elasticsearch import Elasticsearch


def replace_fqdn_in_source(source, ofqdn, nfqdn):
    """
    Replace ofqdn with nfqdn in specific fields of the source dict.

    Args:
        source (dict): Target dictionary.
        ofqdn (str): Old FQDN to replace.
        nfqdn (str): New FQDN to use.

    Returns:
        dict: Updated dictionary.
    """
    # _oai -> id
    oai = source.get("_oai", {})
    oai_id = oai.get("id")
    if oai_id and ofqdn in oai_id:
        oai["id"] = re.sub(re.escape(ofqdn), nfqdn, oai_id)

    # _item_metadata -> _oai -> id
    item_metadata = source.get("_item_metadata", {})
    oai_meta = item_metadata.get("_oai", {})
    oai_meta_id = oai_meta.get("id")
    if oai_meta_id and ofqdn in oai_meta_id:
        oai_meta["id"] = re.sub(re.escape(ofqdn), nfqdn, oai_meta_id)
        item_metadata["_oai"] = oai_meta

    # file property -> url -> url
    for meta_val in item_metadata.values():
        if isinstance(meta_val, dict) and meta_val.get("attribute_type") == "file":
            for file_obj in meta_val.get("attribute_value_mlt", []):
                url_dict = file_obj.get("url", {})
                url_val = url_dict.get("url")
                if url_val and ofqdn in url_val:
                    file_obj["url"]["url"] = re.sub(re.escape(ofqdn), nfqdn, url_val)

    # content -> url -> url
    if "content" in source and isinstance(source["content"], list):
        for content_obj in source["content"]:
            url_dict = content_obj.get("url", {})
            url_val = url_dict.get("url")
            if url_val and ofqdn in url_val:
                content_obj["url"]["url"] = re.sub(re.escape(ofqdn), nfqdn, url_val)

    # file -> URI -> value
    if "file" in source and isinstance(source["file"], dict):
        uri_list = source["file"].get("URI", [])
        for uri_obj in uri_list:
            uri_val = uri_obj.get("value")
            if uri_val and ofqdn in uri_val:
                uri_obj["value"] = re.sub(re.escape(ofqdn), nfqdn, uri_val)

    source["_oai"] = oai
    source["_item_metadata"] = item_metadata
    return source


def update_es_records(ofqdn, nfqdn, id_file_path=None):
    """
    Update Elasticsearch records.
    If id_file_path is given, only update documents whose IDs are listed in the file.
    Otherwise, update all documents in the index.

    Args:
        ofqdn (str): The original fully qualified domain name to be replaced.
        nfqdn (str): The new fully qualified domain name to use as a replacement.
        id_file_path (str, optional): Path to a file containing document IDs (one per line).
    """
    HOST = os.getenv("INVENIO_ELASTICSEARCH_HOST")
    INDEX_PREFIX = os.getenv("SEARCH_INDEX_PREFIX")
    PORT = 9200
    index_name = f"{INDEX_PREFIX}-weko-item-v1.0.0"
    es = Elasticsearch(f"http://{HOST}:{PORT}")

    if id_file_path:
        with open(id_file_path, "r") as f:
            id_list = [line.strip() for line in f if line.strip()]
        print(f"[INFO] {index_name}: {len(id_list)} IDs loaded from {id_file_path}")
    else:
        id_list = None

    query = {"query": {"match_all": {}}}

    try:
        if id_list is not None:
            result_count = len(id_list)
        else:
            result_count = es.count(index=index_name, body=query)["count"]
        print(f"[INFO] {index_name}: Total items: {result_count}")
    except Exception as e:
        print(f"[ERROR] {index_name}: Failed to get count")
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)

    start_time = time.time()
    failed_count = 0
    count = 0

    try:
        if id_list is not None:
            for doc_id in id_list:
                try:
                    hit = es.get(index=index_name, doc_type="_doc", id=doc_id)
                except Exception as e:
                    print(f"[ERROR] {index_name}: Failed to get document ID: {doc_id}")
                    print(f"Error: {e}")
                    traceback.print_exc()
                    failed_count += 1
                    continue

                source = hit["_source"]
                version = hit.get("_version", 1)
                new_source = replace_fqdn_in_source(source, ofqdn, nfqdn)

                try:
                    es.index(
                        index=index_name,
                        doc_type="_doc",
                        id=doc_id,
                        body=new_source,
                        version=version,
                        version_type="external_gte",
                    )
                except Exception as e:
                    print(
                        f"[ERROR] {index_name}: Failed to update document ID: {doc_id}"
                    )
                    print(f"Error: {e}")
                    traceback.print_exc()
                    failed_count += 1
                    continue
                count += 1
                if count % 1000 == 0:
                    elapsed = time.time() - start_time
                    print(
                        f"[INFO] {index_name}: {count} items processed (elapsed time: {elapsed:.2f} seconds)"
                    )
        else:
            scroll = es.search(
                index=index_name,
                body=query,
                params={"version": "true"},
                scroll="2m",
                size=1000,
            )
            scroll_id = scroll["_scroll_id"]
            hits = scroll["hits"]["hits"]

            while hits:
                for hit in hits:
                    doc_id = hit["_id"]
                    source = hit["_source"]
                    version = hit.get("_version", 1)
                    new_source = replace_fqdn_in_source(source, ofqdn, nfqdn)

                    try:
                        es.index(
                            index=index_name,
                            doc_type="_doc",
                            id=doc_id,
                            body=new_source,
                            version=version,
                            version_type="external_gte",
                        )
                    except Exception as e:
                        print(
                            f"[ERROR] {index_name}: Failed to update document ID: {doc_id}"
                        )
                        print(f"Error: {e}")
                        traceback.print_exc()
                        failed_count += 1
                        continue
                    count += 1

                    if count % 1000 == 0:
                        elapsed = time.time() - start_time
                        print(
                            f"[INFO] {index_name}: {count} items processed (elapsed time: {elapsed:.2f} seconds)"
                        )

                scroll = es.scroll(scroll_id=scroll_id, scroll="2m")
                scroll_id = scroll["_scroll_id"]
                hits = scroll["hits"]["hits"]

        total_elapsed = time.time() - start_time

        print(
            f"[INFO] {index_name}: {count} items replaced/updated elapsed time: {total_elapsed:.2f} seconds"
        )
        print(f"[INFO] count(success, error): ({count}, {failed_count})")

    except Exception as e:
        print(f"[ERROR] {index_name}: Unexpected error")
        print(f"Error: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python replace_es_fqdn.py <old_fqdn> <new_fqdn> [id_file_path]")
        sys.exit(1)
    ofqdn = sys.argv[1]
    nfqdn = sys.argv[2]
    id_file_path = sys.argv[3] if len(sys.argv) > 3 else None
    update_es_records(ofqdn, nfqdn, id_file_path)
