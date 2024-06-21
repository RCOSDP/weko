# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Permissions for files using Invenio-Access."""

from invenio_access import Permission, action_factory

from .models import Bucket, MultipartObject, ObjectVersion

#
# Action needs
#

LocationUpdate = action_factory("files-rest-location-update", parameter=True)
"""Action needed: location update."""

BucketRead = action_factory("files-rest-bucket-read", parameter=True)
"""Action needed: list objects in bucket."""

BucketReadVersions = action_factory("files-rest-bucket-read-versions", parameter=True)
"""Action needed: list object versions in bucket."""

BucketUpdate = action_factory("files-rest-bucket-update", parameter=True)
"""Action needed: create objects and multipart uploads in bucket."""

BucketListMultiparts = action_factory(
    "files-rest-bucket-listmultiparts", parameter=True
)
"""Action needed: list multipart uploads in bucket."""

ObjectRead = action_factory("files-rest-object-read", parameter=True)
"""Action needed: get object in bucket."""

ObjectReadVersion = action_factory("files-rest-object-read-version", parameter=True)
"""Action needed: get object version in bucket."""

ObjectDelete = action_factory("files-rest-object-delete", parameter=True)
"""Action needed: delete object in bucket."""

ObjectDeleteVersion = action_factory("files-rest-object-delete-version", parameter=True)
"""Action needed: permanently delete specific object version in bucket."""


MultipartRead = action_factory("files-rest-multipart-read", parameter=True)
"""Action needed: list parts of a multipart upload in a bucket."""

MultipartDelete = action_factory("files-rest-multipart-delete", parameter=True)
"""Action needed: abort a multipart upload."""


#
# Global action needs
#

location_update_all = LocationUpdate(None)
"""Action needed: update all locations."""

bucket_read_all = BucketRead(None)
"""Action needed: read all buckets."""

bucket_read_versions_all = BucketReadVersions(None)
"""Action needed: read all buckets versions."""

bucket_update_all = BucketUpdate(None)
"""Action needed: update all buckets"""

bucket_listmultiparts_all = BucketListMultiparts(None)
"""Action needed: list all buckets multiparts."""

object_read_all = ObjectRead(None)
"""Action needed: read all objects."""

object_read_version_all = ObjectReadVersion(None)
"""Action needed: read all objects versions."""

object_delete_all = ObjectDelete(None)
"""Action needed: delete all objects."""

object_delete_version_all = ObjectDeleteVersion(None)
"""Action needed: delete all objects versions."""

multipart_read_all = MultipartRead(None)
"""Action needed: read all multiparts."""

multipart_delete_all = MultipartDelete(None)
"""Action needed: delete all multiparts."""


_action2need_map = {
    "location-update": LocationUpdate,
    "bucket-read": BucketRead,
    "bucket-read-versions": BucketReadVersions,
    "bucket-update": BucketUpdate,
    "bucket-listmultiparts": BucketListMultiparts,
    "object-read": ObjectRead,
    "object-read-version": ObjectReadVersion,
    "object-delete": ObjectDelete,
    "object-delete-version": ObjectDeleteVersion,
    "multipart-read": MultipartRead,
    "multipart-delete": MultipartDelete,
}
"""Mapping of action names to action needs."""


def permission_factory(obj, action):
    """Get default permission factory.

    :param obj: An instance of :class:`invenio_files_rest.models.Bucket` or
        :class:`invenio_files_rest.models.ObjectVersion` or
        :class:`invenio_files_rest.models.MultipartObject` or ``None`` if
        the action is global.
    :param action: The required action.
    :raises RuntimeError: If the object is unknown.
    :returns: A :class:`invenio_access.permissions.Permission` instance.
    """
    need_class = _action2need_map[action]

    if obj is None:
        return Permission(need_class(None))

    arg = None
    if isinstance(obj, Bucket):
        arg = str(obj.id)
    elif isinstance(obj, ObjectVersion):
        arg = str(obj.bucket_id)
    elif isinstance(obj, MultipartObject):
        arg = str(obj.bucket_id)
    else:
        raise RuntimeError("Unknown object")

    return Permission(need_class(arg))
