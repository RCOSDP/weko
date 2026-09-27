# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Permissions for the IIIF API."""


def _get_record_of_bucket(bucket_id):
    """Get the metadata of the record linked to a bucket."""
    from invenio_records.models import RecordMetadata
    from invenio_records_files.models import RecordsBuckets

    rb = RecordsBuckets.query.filter_by(bucket_id=bucket_id).first()
    if not rb:
        return None
    rm = RecordMetadata.query.filter_by(id=rb.record_id).first()
    return rm.json if rm else None


def _get_file_metadata(record, version_id):
    """Get the file metadata of a record by the object version id."""
    version_id = str(version_id)
    for value in record.values():
        if not isinstance(value, dict) or \
                value.get('attribute_type') != 'file':
            continue
        for item in value.get('attribute_value_mlt') or []:
            if isinstance(item, dict) and \
                    item.get('version_id') == version_id:
                return item
    return None


def iiif_object_permission_factory(obj, record=None):
    """Permission factory for reading an object through the IIIF API.

    When the object is a file of a record, the permissions of the record and
    of the file are checked. Otherwise the Invenio-Files-REST permission
    factory is used.

    :param obj: A :class:`invenio_files_rest.models.ObjectVersion` instance.
    :param record: The metadata of the record owning the object. It is looked
        up from the bucket of the object when not given.
    """
    def can(self):
        from invenio_files_rest.proxies import current_permission_factory
        from weko_records_ui.permissions import \
            check_file_download_permission, page_permission_factory

        record_json = record
        if record_json is None:
            record_json = _get_record_of_bucket(obj.bucket_id)
        if record_json:
            fjson = _get_file_metadata(record_json, obj.version_id)
            if fjson is not None:
                return bool(
                    page_permission_factory(record_json).can()
                    and check_file_download_permission(record_json, fjson))
        return bool(current_permission_factory(obj, 'object-read').can())

    return type('IIIFObjectPermissionChecker', (), {'can': can})()
