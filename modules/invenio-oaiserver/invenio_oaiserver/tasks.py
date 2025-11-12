# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Task for OAI."""

from time import sleep
import datetime
import json
import io
import traceback

from lxml import etree
from celery import group, shared_task
from flask import current_app
from flask_celeryext import RequestContextTask
from itsdangerous import URLSafeTimedSerializer
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_files_rest.models import Bucket, FileInstance, Location, ObjectVersion

from .query import get_affected_records
from .response import listrecords
from .utils import datetime_to_datestamp

OAIPMH_FOLDER_NAME = 'OAI_SERVER_FILE_CREATE'
NS_OAIPMH = 'http://www.openarchives.org/OAI/2.0/'

try:
    from itertools import zip_longest
except ImportError:  # pragma: no cover
    from itertools import izip_longest as zip_longest


def _records_commit(record_ids):
    """Commit all records."""
    for record_id in record_ids:
        record = Record.get_record(record_id)
        record.commit()


@shared_task(base=RequestContextTask)
def update_records_sets(record_ids):
    """Update records sets.

    :param record_ids: List of record UUID.
    """
    try:
        _records_commit(record_ids)
        db.session.commit()

        # update record to ES
        sleep(20)
        query = (x[0] for x in PersistentIdentifier.query.filter_by(
            object_type='rec', status=PIDStatus.REGISTERED
        ).filter(
            PersistentIdentifier.pid_type.in_(['oai'])
        ).filter(
            PersistentIdentifier.object_uuid.in_(record_ids)
        ).values(
            PersistentIdentifier.object_uuid
        ))
        RecordIndexer().bulk_index(query)
        RecordIndexer().process_bulk_queue(
            es_bulk_kwargs={'raise_on_error': True})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)


@shared_task(base=RequestContextTask)
def update_affected_records(spec=None, search_pattern=None):
    """Update all affected records by OAISet change.

    :param spec: The record spec.
    :param search_pattern: The search pattern.
    """
    chunk_size = current_app.config['OAISERVER_CELERY_TASK_CHUNK_SIZE']
    record_ids = get_affected_records(spec=spec, search_pattern=search_pattern)

    group(
        update_records_sets.s(list(filter(None, chunk)))
        for chunk in zip_longest(*[iter(record_ids)] * chunk_size)
    )()


@shared_task
def create_data():
    """ Create a file for the ListRecords response."""

    current_app.logger.warn(
        'OAI-PMH Create file for ListRecords  BATCH START ')

    try:
        # Obtaining batch times
        batch_time = datetime.datetime.now()
        batch_time_str = batch_time.strftime('%Y%m%d%H%M%S%f')
        current_app.logger.debug('batch_time : {0}'.format(str(batch_time)))

        # Get file location
        location = get_create_file_location()
        if location is None:
            current_app.logger.info(
                'OAI-PMH Create file for ListRecords BATCH FAILED END')
            return

        # Retrieving data.json
        data_json_obj, data_json = get_data_json(location)
        if data_json is None:
            # If data.json does not exist, create it.
            data_json_obj, data_json = create_data_json(location)
        elif data_json.get('datas') is not None \
                and len(data_json.get('datas')) > 1:
            # Files can only have a maximum of two generations and should be
            # deleted before they are created.
            data_json_obj, data_json = delete_data_json_data(data_json_obj,
                                                             data_json)

        # Creating backke for file cross sections.
        bucket = Bucket.create(location)
        ObjectVersion.create(bucket, '{0}/{1}'.format(
            OAIPMH_FOLDER_NAME, batch_time_str))

        # Format minute file creation process
        formats = current_app.config['OAISERVER_FILE_BATCH_FORMATS']
        for format in formats:
            save_item_data(bucket, format, batch_time_str)

        # Update data.json
        update_data_json_data(data_json_obj, data_json, batch_time,
                              batch_time_str)
    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        current_app.logger.info(
            'OAI-PMH Create file for ListRecords  BATCH FAILED END')
        return

    current_app.logger.warn(
        'OAI-PMH Create file for ListRecords  BATCH SUCCESS END')


def delete_data_json_data(data_json_obj, data_json):
    """ Delete file sections created in a batch.
        Files can only have a maximum of two generations and should be
        deleted before they are created.

        Args:
            data_json_obj: Version object in data.json
            data_json:  Dictionary type representation in data.json
    """
    delete_ids = []
    current_data_id = data_json.get('current_data')
    for data in data_json['datas']:
        if data.get('id') != current_data_id:
            delete_ids.append(data.get('id'))

    for delete_id in delete_ids:
        data_obj = ObjectVersion.query.filter_by(key='{0}/{1}'.format(
            OAIPMH_FOLDER_NAME, delete_id)).first()
        current_app.logger.info('remove_buket_id : {0}'.format(
            str(data_obj.bucket_id)))
        data_obj.bucket.remove()

    new_data_json = {'current_data': current_data_id, 'datas': [data]}
    file_bytes = io.BytesIO(bytes(json.dumps(new_data_json), encoding="utf-8"))
    try:
        new_data_json_obj = ObjectVersion.create(
            data_json_obj.bucket, '{0}/data.json'.format(OAIPMH_FOLDER_NAME),
            stream=file_bytes)
        data_json_obj.remove()
        db.session.commit()
        return new_data_json_obj, new_data_json
    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        current_app.logger.error('ERR_IOS-002: IO error occurred.')
        raise e


def get_data_json(location):
    """ Get definition information on files for acceleration.

        Args:
            location: Location where the file is stored.
        Returns:
            Definition information on files for acceleration.
    """
    data_json = None
    data_folder = None
    data_json_obj = None

    for obj_version in ObjectVersion.query.filter_by(key=OAIPMH_FOLDER_NAME):
        current_app.logger.debug('default_location : {0}'.format(
            str(obj_version.bucket.default_location)))
        current_app.logger.debug('location.id : {0}'.format(str(location.id)))
        if obj_version.bucket.default_location == location.id:
            data_folder = obj_version
            break

    current_app.logger.debug('data_folder : {0}'.format(str(data_folder)))
    if data_folder is not None:
        data_json_obj = ObjectVersion.get(
            data_folder.bucket_id, '{0}/data.json'.format(OAIPMH_FOLDER_NAME))
        if data_json_obj is not None:
            try:
                with data_json_obj.file.storage().open() as f:
                    data_json = json.loads(f.read().decode(encoding='utf-8'))
                    current_app.logger.debug(
                        'data.json : {0}'.format(data_json))
            except Exception as e:
                current_app.logger.error(e)
                current_app.logger.error(traceback.format_exc())
                current_app.logger.error(
                    'ERR_IOS-002: IO error occurred.')
                raise e

    return data_json_obj, data_json


def create_data_json(location):
    """ Create data.json.
        The data.json contains information on generation management
        of files for acceleration.

        Args:
            location:  Location where the file is stored.
        Returns:
            data_json_obj: Version object in data.json
            result:  Dictionary type representation in data.json
    """

    data_folder = None

    for obj_version in ObjectVersion.query.filter_by(key=OAIPMH_FOLDER_NAME):
        current_app.logger.debug('location.id : {0}'.format(str(location.id)))
        if obj_version.bucket.default_location == location.id:
            data_folder = obj_version
            break

    result = {}
    data_json_obj = None
    bytesIO = io.BytesIO(bytes(json.dumps(result), encoding="utf-8"))
    bucket = None
    try:
        if not data_folder:
            bucket = Bucket.create(location)
            data_folder = ObjectVersion.create(bucket, OAIPMH_FOLDER_NAME)
        else:
            bucket = Bucket.get(data_folder.bucket_id)

        data_json_obj = ObjectVersion.create(
            bucket, '{0}/data.json'.format(OAIPMH_FOLDER_NAME),
            stream=bytesIO)
    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        current_app.logger.error(
            'ERR_IOS-002: IO error occurred.')
        raise e

    db.session.commit()
    return data_json_obj, result


def get_create_file_location():
    """ Returns the Location where the file for acceleration is stored."""
    location_name = current_app.config['OAISERVER_FILE_BATCH_STORAGE_LOACTION']
    if location_name is None:
        current_app.logger.error(
            'ERR_IOS-001: Location is not set up correctly.')
        return None

    result = Location.query.filter_by(name=location_name).first()
    if result is None:
        current_app.logger.error(
            'ERR_IOS-001: Location is not set up correctly.')
    return result


def save_item_data(bucket, format, batch_time_str):
    """ To speed up ListRecords, pre-file output of items
        to be written in each format.
        To support Harvest condition specification, information
        on extraction conditions is output to index.json.

        Args:
            bucket:  The bucket in which the file is to be stored.
            format:  Format of output target.
            batch_time_str:  Batch run identifier..
    """

    # Create ObjectVersion.
    ObjectVersion.create(bucket, '{0}/{1}/{2}'.format(
        OAIPMH_FOLDER_NAME, batch_time_str, format))

    # index.json
    index_json = {'items': []}

    num = 0
    token = 'token'
    param = {'metadataPrefix': format, 'verb': 'ListRecords', 'url': 'batch'}
    param.update()
    token_builder = URLSafeTimedSerializer(
        current_app.config['SECRET_KEY'],
        salt='ListRecords',
    )

    site_url = current_app.config['THEME_SITEURL']
    while token is not None:
        with current_app.test_request_context(site_url):
            e_tree = listrecords(**param)

            ns = e_tree.getroot().nsmap
            current_app.logger.debug('format: {0} page: {1}'.format(
                format, num))
            for rec in e_tree.getroot().findall('./ListRecords/record',
                                                namespaces=ns):

                identifier = rec.find('./header/identifier', namespaces=ns)
                datestamp = rec.find('./header/datestamp', namespaces=ns)
                setspecs = rec.findall('./header/setSpec', namespaces=ns)

                item_json = {}
                item_json.update(identifier=identifier.text)
                item_json.update(datestamp=datestamp.text)
                if setspecs is not None:
                    setspec_attr = []
                    for setspec in setspecs:
                        setspec_attr.append(setspec.text)
                    item_json.update(setSpec=setspec_attr)

                # rec delete sets
                for child in rec.iter():
                    if child.attrib.get('status') == 'deleted':
                        for setspec in setspecs:
                            child.remove(setspec)

                file_name = identifier.text.replace(
                    ':', '_').replace('.', '_') + ".xml"
                item_json.update(file_name=file_name)
                index_json['items'].append(item_json)

                file_bytes = io.BytesIO(bytes(
                    etree.tostring(rec, encoding='unicode'), encoding="utf-8"))
                try:
                    ObjectVersion.create(bucket, '{0}/{1}/{2}/{3}'.format(
                        OAIPMH_FOLDER_NAME, batch_time_str, format, file_name),
                        stream=file_bytes)
                except Exception as e:
                    current_app.logger.error(e)
                    current_app.logger.error(traceback.format_exc())
                    current_app.logger.error('ERR_IOS-002: IO error occurred.')
                    raise e

            resumption_token = e_tree.getroot().find(
                './ListRecords/resumptionToken',
                namespaces=e_tree.getroot().nsmap)

            if resumption_token is not None:
                token = resumption_token.text
                current_app.logger.debug('token : {0}'.format(token))
                if token is not None:
                    resumption_token_param = token_builder.loads(
                        resumption_token.text, max_age=current_app.config[
                            'OAISERVER_RESUMPTION_TOKEN_EXPIRE_TIME'])
                    resumption_token_param.update(token=token)
                    param.update(resumptionToken=resumption_token_param)
            else:
                token = None
            db.session.commit()
        num += 1

    index_bytes = io.BytesIO(bytes(json.dumps(
        index_json, indent=4, sort_keys=True, separators=(',', ': ')),
        encoding="utf-8"))
    try:
        ObjectVersion.create(bucket, '{0}/{1}/{2}/index.json'.format(
            OAIPMH_FOLDER_NAME, batch_time_str, format), stream=index_bytes)
        db.session.commit()

    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        current_app.logger.error('ERR_IOS-002: IO error occurred.')
        raise e


def update_data_json_data(data_json_obj, data_json, batch_time,
                          batch_time_str):
    """ Update information in data.json after file creation.

        Args:
            data_json_obj: Version object in data.json
            data_json:  Dictionary type representation in data.json
            batch_time:  The time the batch was executed.
            batch_time_str:  Batch run identifier..
    """

    expiry = current_app.config['OAISERVER_FILE_BATCH_FILE_EXPIRY']
    expiry_time = batch_time + datetime.timedelta(hours=expiry)

    add_json = {
        'id': batch_time_str,
        'create_time': datetime_to_datestamp(batch_time),
        'expired_time': datetime_to_datestamp(expiry_time)
    }

    data_json.update(current_data=batch_time_str)
    if 'datas' not in data_json:
        data_json.update(datas=[])

    data_json['datas'].append(add_json)

    file_bytes = io.BytesIO(bytes(json.dumps(
        data_json, indent=4, sort_keys=True, separators=(',', ': ')),
        encoding="utf-8"))
    try:
        ObjectVersion.create(data_json_obj.bucket, '{0}/data.json'.format(
            OAIPMH_FOLDER_NAME), stream=file_bytes)
        data_json_obj.remove()
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        current_app.logger.error(traceback.format_exc())
        current_app.logger.error('ERR_IOS-002: IO error occurred.')
        raise e
