# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Permissions for files using Invenio-Access."""

from functools import partial

from invenio_access.permissions import DynamicPermission, \
    ParameterizedActionNeed

from .models import Bucket, MultipartObject, ObjectVersion

#
# Action needs
#

LocationUpdate = partial(
    ParameterizedActionNeed, 'files-rest-location-update')
"""Action needed: location update."""

BucketRead = partial(
    ParameterizedActionNeed, 'files-rest-bucket-read')
"""Action needed: list objects in bucket."""

BucketReadVersions = partial(
    ParameterizedActionNeed, 'files-rest-bucket-read-versions')
"""Action needed: list object versions in bucket."""

BucketUpdate = partial(
    ParameterizedActionNeed, 'files-rest-bucket-update')
"""Action needed: create objects and multipart uploads in bucket."""

BucketListMultiparts = partial(
    ParameterizedActionNeed, 'files-rest-bucket-listmultiparts')
"""Action needed: list multipart uploads in bucket."""

ObjectRead = partial(
    ParameterizedActionNeed, 'files-rest-object-read')
"""Action needed: get object in bucket."""

ObjectReadVersion = partial(
    ParameterizedActionNeed, 'files-rest-object-read-version')
"""Action needed: get object version in bucket."""

ObjectDelete = partial(
    ParameterizedActionNeed, 'files-rest-object-delete')
"""Action needed: delete object in bucket."""

ObjectDeleteVersion = partial(
    ParameterizedActionNeed, 'files-rest-object-delete-version')
"""Action needed: permanently delete specific object version in bucket."""

MultipartRead = partial(
    ParameterizedActionNeed, 'files-rest-multipart-read')
"""Action needed: list parts of a multipart upload in a bucket."""

MultipartDelete = partial(
    ParameterizedActionNeed, 'files-rest-multipart-delete')
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
    'location-update': LocationUpdate,
    'bucket-read': BucketRead,
    'bucket-read-versions': BucketReadVersions,
    'bucket-update': BucketUpdate,
    'bucket-listmultiparts': BucketListMultiparts,
    'object-read': ObjectRead,
    'object-read-version': ObjectReadVersion,
    'object-delete': ObjectDelete,
    'object-delete-version': ObjectDeleteVersion,
    'multipart-read': MultipartRead,
    'multipart-delete': MultipartDelete,
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
    :returns: A :class:`invenio_access.permissions.DynamicPermission` instance.
    """
    need_class = _action2need_map[action]

    if obj is None:
        return DynamicPermission(need_class(None))

    arg = None
    if isinstance(obj, Bucket):
        arg = str(obj.id)
    elif isinstance(obj, ObjectVersion):
        arg = str(obj.bucket_id)
    elif isinstance(obj, MultipartObject):
        arg = str(obj.bucket_id)
    else:
        raise RuntimeError('Unknown object')

    return DynamicPermission(need_class(arg))
