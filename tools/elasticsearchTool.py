import os
import sys
import time
import traceback

from flask import current_app
from invenio_db import db
from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_files.api import Record
from sqlalchemy.exc import SQLAlchemyError
from weko_deposit.api import WekoRecord
from weko_records.models import ItemMetadata, ItemReference

from elasticsearch import Elasticsearch, helpers


def deleteUntrackableItems(dryrun=True):
    """
    deleteUntrackableItems Delete untrackable items from item index in Elasticsearch

    _extended_summary_

    Args:
        dryrun (bool, optional): True is dryrun mode. Defaults to True.
    """
    start = time.time()
    es = Elasticsearch(
        "http://" + os.environ.get("INVENIO_ELASTICSEARCH_HOST", "localhost") + ":9200"
    )
    _query = '{"query": {"match_all" : {}}}'
    results = helpers.scan(
        es,
        index=os.environ.get("SEARCH_INDEX_PREFIX", "tenant1") + "-weko-item-v1.0.0",
        preserve_order=True,
        query=_query,
    )
    idList = []

    for item in results:
        idList.append(item["_id"])

    current_app.logger.info("documents: {0}".format(len(idList)))

    delList = []
    for item in idList:
        current_app.logger.debug("checking item: {0}".format(item))
        try:
            pid = PersistentIdentifier.query.filter_by(
                pid_type="parent", object_uuid=str(item)
            ).first()
            if pid is not None and pid.is_deleted():
                delList.append(item)
        except ValueError as e:
            current_app.logger.error(e)
        except Exception as e:
            current_app.logger.error(e)

    current_app.logger.info("deleting items: {0}".format(len(delList)))

    for item in delList:
        if not dryrun:
            es.delete(
                index=os.environ.get("SEARCH_INDEX_PREFIX", "tenant1")
                + "-weko-item-v1.0.0",
                doc_type="item-v1.0.0",
                id=item,
            )
        current_app.logger.info("delete item : {0}".format(item))

    current_app.logger.info("elapsed time: {0}".format(time.time() - start))
