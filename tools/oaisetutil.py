import argparse
import json
import os
import sys
import traceback

import sqlalchemy
from flask import current_app
from invenio_communities.models import Community
from invenio_db import db
from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.models import RecordMetadata
from invenio_records_files.api import Record
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import cast
from weko_deposit.api import WekoRecord
from weko_records.models import ItemMetadata, ItemReference

from elasticsearch import Elasticsearch, helpers


def addOAISet(community_id):
    """Add OAI set on the items that belong to the community.

    Args:
        community_id (string): community id
    """
    c = Community.get(community_id)
    _addOAISet(c)


def _addOAISet(c):
    """Add OAI set on the records that belong to the community.

    Args:
        community (Community): community
    """
    # es = Elasticsearch(
    #    "http://"+os.environ.get('INVENIO_ELASTICSEARCH_HOST', 'localhost')+":9200")
    # _query = '{"query":{"term":{"path":{"value":"'+str(c.index.id)+'"}}}}'
    # res = helpers.scan(es, index=os.environ.get(
    #    'SEARCH_INDEX_PREFIX', 'tenant1')+"-weko-item-v1.0.0", preserve_order=True, query=_query)

    res = RecordMetadata.query.filter(
        cast(RecordMetadata.json['path'], sqlalchemy.String).like('%1582963390870%')).all()

    count = 0
    for i in res:
        try:
            # record = Record.get_record(i['_id'])
            pid = PersistentIdentifier.query.filter_by(
                pid_type='parent', object_uuid=i.id).first()
            if pid is not None and not pid.is_deleted():
                record = Record.get_record(i.id)
                if record is not None:
                    c.add_record(record)
                    record.commit()
                    db.session.commit()
                    try:
                        RecordIndexer().index_by_id(record.id)
                        current_app.logger.info(
                            "registered item:  {0} .".format(record.id))
                        count = count + 1
                    except Exception as e:
                        # current_app.logger.error(
                        #    "error item:  {0} .".format(i['_id']))
                        current_app.logger.error(
                            "error item:  {0} .".format(i.id))
                        current_app.logger.error(
                            list(traceback.TracebackException.from_exception(e).format()))
                        db.session.rollback()
        except Exception as sqlerror:
            # current_app.logger.error("error item:  {0} .".format(i['_id']))
            current_app.logger.error("error item:  {0} .".format(i.id))
            current_app.logger.error(
                list(traceback.TracebackException.from_exception(sqlerror).format()))
            db.session.rollback()
        current_app.logger.debug(
            "comunity: {0}, count: {1}".format(c.id, count))


def addOAISetToAll():
    for c in Community.query.all():
        current_app.logger.debug(c)
        _addOAISet(c)


def init_parser():
    parser = argparse.ArgumentParser(
        description='Add OAI set on the items that belong to the community.')
    parser.add_argument('--all', action="store_true", default=False,
                        help='Set to all communities.')
    parser.add_argument('-i', '--community_id',
                        type=str, help='Set a specific community ID.')

    return parser


if __name__ == '__main__':
    args = sys.argv
    if len(args) == 2:
        opt = args[1]
        if opt == "all":
            addOAISetToAll()
        else:
            addOAISet(opt)
    else:
        print("Usage: invenio shell oaisetutil.py [all|community_id]")

#    parser = init_parser()
#    args = parser.parse_args(args=[])
#    if args.all:
#        addOAISetToAll()
#    elif args.community_id is not None:
#        addOAISet(args.community_id)
#    else:
#        parser.print_help()
