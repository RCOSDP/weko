import argparse
import json
import os
import sys
import time
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
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import cast
from weko_deposit.api import WekoRecord
from weko_records.models import ItemMetadata, ItemReference

from elasticsearch import Elasticsearch, helpers


def removeOAISet():
    start = time.process_time()
    count = 0
    try:
        records = RecordMetadata.query.filter(
            RecordMetadata.json['_oai']['sets'] != None).all()
        # pid = PersistentIdentifier.query.filter_by(
        #    pid_type='parent', status='R').all()
        # for p in pid:
        for r in records:
            try:
                record = Record.get_record(r.id)
                if '_oai' in record:
                    if 'sets' in record['_oai']:
                        tmp = record['_oai']['sets']
                        del(record['_oai']['sets'])
                        record.commit()
                        count = count + 1
                        current_app.logger.info(
                            'remove all sets from record {0} set:{1}'.format(record.id, tmp))
            except NoResultFound as e:
                # current_app.logger.error(
                #    "no record match {0}".format(p.object_uuid))
                current_app.logger.error(
                    "no record match {0}".format(record.id))
        db.session.commit()
        current_app.logger.info(
            "Processed {0} items, elapsed time: {1}".format(count, time.process_time()-start))
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(
            list(traceback.TracebackException.from_exception(e).format()))


def addOAISet(community_id):
    """Add OAI set on the items that belong to the community.

    Args:
        community_id (string): community id
    """
    c = Community.get(community_id)
    if c is not None:
        _addOAISet(c.id)
    else:
        current_app.logger.error(
            "community id {0} does not exist.".format(community_id))


def _addOAISet(id):
    """Add OAI set on the records that belong to the community.

    Args:
        id : community id
    """
    # es = Elasticsearch(
    #    "http://"+os.environ.get('INVENIO_ELASTICSEARCH_HOST', 'localhost')+":9200")
    # _query = '{"query":{"term":{"path":{"value":"'+str(c.index.id)+'"}}}}'
    # res = helpers.scan(es, index=os.environ.get(
    #    'SEARCH_INDEX_PREFIX', 'tenant1')+"-weko-item-v1.0.0", preserve_order=True, query=_query)

    c = Community.get(id)

    res = RecordMetadata.query.filter(
        cast(RecordMetadata.json['path'], sqlalchemy.String).like(
            "%{0}%".format(c.index.id))).filter(
                cast(RecordMetadata.json['recid'], sqlalchemy.String).notlike(
                    "%.%")).all()

    count = 0
    for i in res:
        try:
            # record = Record.get_record(i['_id'])
            pid = PersistentIdentifier.query.filter_by(
                pid_type='parent', object_uuid=i.id).first()
            if pid is not None and not pid.is_deleted():
                record = Record.get_record(pid.object_uuid)
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
    start = time.process_time()
    cl = Community.query.all()
    c_id_list = []
    for c in cl:
        c_id_list.append(c.id)

    for c in c_id_list:
        current_app.logger.info("start {0}".format(c))
        _addOAISet(c)
        current_app.logger.info("end {0}".format(c))

    current_app.logger.info(
        "elapsed time: {0}".format(time.process_time()-start))


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
