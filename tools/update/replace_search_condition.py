"""
    The purpose of this batch program is to update existing Elasticsearch data
    to apply the latest advanced search settings.

    This program is intended to update only the target data that have been
    changed according to specific development requirements.
    Therefore, the target data to be updated is narrowed down by the function
    get_meta_records.

    In order to reuse the data in future development, it is necessary to
    change the target data, In that case, the function get_meta_record is
    assumed to be modified to accommodate the change.

"""

from sqlalchemy import create_engine
from flask import current_app
from elasticsearch.exceptions import TransportError
from invenio_records_rest.errors import PIDResolveRESTError
from weko_deposit.api import WekoDeposit
from weko_records.api import ItemsMetadata, FeedbackMailList
from werkzeug.exceptions import InternalServerError
from sqlalchemy.orm.exc import NoResultFound
from jsonpath_ng.ext import parse
from weko_records.utils import set_timestamp
from invenio_pidrelations.serializers.utils import serialize_relations
from invenio_pidstore.models import PersistentIdentifier
from datetime import datetime
import os
import sys
import logging

# Get start time of batch program
start_time = datetime.today()

# Postgres global connect
engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
connection = engine.connect()

# Prepare logger for batch
batch_logger = logging.getLogger('BATCH')
batch_logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)-15s %(levelname)-5s %(message)s')
fileHandler = logging.FileHandler(
    'logging-replace-search-condition-id-process' +
    '{:-%Y%m%d-%s.}'.format(datetime.now()) +
    str(os.getpid()) + ".log", mode='w')
fileHandler.setFormatter(formatter)
batch_logger.addHandler(fileHandler)
stdoutHandler = logging.StreamHandler(stream=sys.stdout)
batch_logger.addHandler(stdoutHandler)


def get_meta_records():
    """Get data in records_metadata.

    This function returns records_metadata for the following conditions.
        1. item_type_id is 12(Multiple)
        2. Meets one of the following conditions
            2-1. The distributor or holder/depositor is established.
            2-2. An overview or data type is established.

    Return:
        records_metadata data.
    """

    sql_meta_records = '''
    SELECT
        records_metadata.created, 
        records_metadata.updated, 
        records_metadata.id, 
        records_metadata.json, 
        records_metadata.version_id 
    FROM
        records_metadata
    WHERE
        json->>'item_type_id' = '12'
    ORDER BY id
    '''.strip()
    records = connection.execute(sql_meta_records).fetchall()
    return filter_records(records)


def filter_records(records):
    """Filters data for the specified records_metadata.

    The filtering criteria will be one of the following
        1. The distributor or holder/depositor is established.
        2. An overview or data type is established.
    Args:
        records: The records_metadata to be filtered.
    Return:
        Filtered records_metadata.
    """

    result = []
    d1551257276108_count = 0
    d1522657697257_count = 0

    for rec in records:
        isAppend = False

        if parse('$.item_1551264418667.attribute_value_mlt[*].' +
                 'subitem_1551257245638[*].subitem_1551257276108').find(
                     rec.json):
            isAppend = True
            d1551257276108_count += 1

        if parse('$.item_1636460428217.attribute_value_mlt[*].' +
                 'subitem_1522657697257').find(rec.json):
            isAppend = True
            d1522657697257_count += 1

        if isAppend:
            result.append(rec)

    batch_logger.info(('total:{} / d1551257276108_count:{} / ' +
                      'd1522657697257_count:{} / update_count:{}').format(
                          len(records), d1551257276108_count,
                          d1522657697257_count, len(result)))
    return result


def update_records_metadata():
    """Update Elasticsearch information based on the contents of
    records_metadata.

    Please refer to the function get_meta_records for the update target.
    """

    # Get record information of the item to be changed
    records = get_meta_records()

    ok_count = 0
    pid_error = 0
    internal_error = 0
    noresult_error = 0
    key_error = 0
    transport_error = 0
    data_count = 0
    for rec in records:
        if data_count % 1000 == 0:
            batch_logger.info(' data progress count: {} / {}.'.format(
                data_count, len(records)))
        data_count += 1
        deposit = WekoDeposit(rec.json, rec)
        try:
            # Update Elasticsearch Metadata.
            update_record_metadata(deposit, rec)
            ok_count += 1
        except PIDResolveRESTError as ex:
            batch_logger.warning(' ERROR ID:' + str(deposit.id))
            batch_logger.warning(' PIDResolveRESTError: {}.'.format(ex))
            pid_error += 1
            continue
        except InternalServerError as isex:
            batch_logger.warning(' ERROR ID:' + str(deposit.id))
            batch_logger.warning(' InternalServerError: {}.'.format(isex))
            internal_error += 1
            continue
        except NoResultFound as nex:
            batch_logger.warning(' ERROR ID:' + str(deposit.id))
            batch_logger.warning(' NoResultFound: {}.'.format(nex))
            noresult_error += 1
            continue
        except KeyError as err:
            batch_logger.warning(' ERROR ID:' + str(deposit.id))
            batch_logger.warning(' KeyError: {}.'.format(err))
            key_error += 1
        except TransportError as ex:
            batch_logger.warning(' ERROR ID:' + str(deposit.id))
            batch_logger.warning(' ERROR-TransportError: {}.'.format(ex))
            transport_error += 1
            continue

    batch_logger.info(' data progress count: {} / {}.'.format(
        data_count, len(records)))
    batch_logger.info(' OK:{}'.format(ok_count))
    batch_logger.info(' PIDResolveRESTError:{}'.format(pid_error))
    batch_logger.info(' InternalServerError:{}'.format(internal_error))
    batch_logger.info(' NoResultFound:{}'.format(noresult_error))
    batch_logger.info(' KeyError:{}'.format(key_error))
    batch_logger.info(' TransportError:{}'.format(transport_error))


def update_record_metadata(deposit, record):
    """Update Elasticsearch Metadata.

    This function is based on WekoDeposit.commit() and does not update the DB.

    Args:
        deposit: WekoDeposit Object
        record: records_metadata
    Return:
        Filtered records_metadata.
    """

    index = {'index': deposit.get('path', []),
             'actions': deposit.get('publish_status')}
    args = [index, ItemsMetadata.get_record(deposit.id).dumps()]
    deposit.update(*args)
    recid = PersistentIdentifier.query.filter_by(
        pid_type='recid',
        object_uuid=deposit.id
    ).one_or_none()
    set_timestamp(deposit.jrc, deposit.created, datetime.utcnow())

    if deposit.jrc and len(deposit.jrc):
        if record and record.json and '_oai' in record.json:
            deposit.jrc['_oai'] = record.json.get('_oai')
            deposit.jrc['_item_metadata'].update(
                dict(_oai=record.json.get('_oai')))
            if 'path' in deposit.jrc and '_oai' in deposit.jrc \
                and ('sets' not in deposit.jrc['_oai']
                     or not deposit.jrc['_oai']['sets']):
                setspec_list = deposit.jrc['path'] or []
                if setspec_list:
                    deposit.jrc['_oai'].update(dict(sets=setspec_list))
                    deposit.jrc['_item_metadata']['_oai'].update(
                        dict(sets=setspec_list))

    deposit.indexer.get_es_index()
    deposit.indexer.upload_metadata(
                            deposit.jrc,
                            deposit.pid.object_uuid,
                            deposit.revision_id)

    feedback_mail_list = FeedbackMailList.get_mail_list_by_item_id(deposit.id)
    if feedback_mail_list:
        deposit.update_feedback_mail()
    else:
        deposit.remove_feedback_mail()

    relations = serialize_relations(recid)
    if relations and 'version' in relations:
        relations_ver = relations['version'][0]
        relations_ver['id'] = recid.object_uuid
        relations_ver['is_last'] = relations_ver.get('index') == 0
        deposit.indexer.update_relation_version_is_last(relations_ver)


def main():
    """Application's main function. """
    batch_logger.info('-' * 60)
    batch_logger.info(' STARTED replace_search_condition.')
    batch_logger.info('-' * 60)

    update_records_metadata()

    end_time = datetime.today()

    batch_logger.info('--> Finished')
    batch_logger.info('    start time - {}'.format(start_time))
    batch_logger.info('    end time   - {}'.format(end_time))
    connection.close()
    print(' Finished! ')


if __name__ == '__main__':  # pragma: no cover
    main()  # pragma: no cover
