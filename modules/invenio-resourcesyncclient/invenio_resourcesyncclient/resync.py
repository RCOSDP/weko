# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""WEKO3 module docstring."""
import orjson
import ssl

from flask import current_app
from resync.client import Client

from .config import INVENIO_RESYNC_MODE

ssl._create_default_https_context = ssl._create_unverified_context


class ResourceSyncClient(Client):
    """Class ResourceSyncClient base on Client."""

    def __init__(self, hashes=None, verbose=False, dryrun=False):
        """Overwrite Init."""
        super(ResourceSyncClient, self).__init__(hashes, verbose, dryrun)
        self.result = dict(
            created=[],
            updated=[],
            deleted=[],
            resource=[]
        )

    def update_resource(self, resource, filename, change=None):
        """Update Resource."""
        num_updated = super(ResourceSyncClient, self).update_resource(resource,
                                                                      filename,
                                                                      change)
        current_create = self.result.get('created')
        current_update = self.result.get('updated')
        current_resource = self.result.get('resource')

        if INVENIO_RESYNC_MODE:
            record_id = filename
        else:
            record_id = filename.rsplit('/', 1)[1]

        if change == 'created':
            current_create.append(record_id)
        elif change == 'updated':
            current_update.append(record_id)
        resource.link_add(href=record_id, rel='file')
        _resource = orjson.loads((repr(resource)).replace('\'', '"'))
        current_resource.append(_resource)
        self.result.update({'created': current_create})
        self.result.update({'updated': current_update})
        self.result.update({'resource': current_resource})

        return num_updated

    def delete_resource(self, resource, filename, change=None):
        """Delete Resource."""
        num_deleted = super(ResourceSyncClient, self).delete_resource(resource,
                                                                      filename,
                                                                      change)
        current_delete = self.result.get('deleted')
        #record_id = filename.rsplit('/', 1)[1]
        record_id = filename
        current_delete.append(record_id)
        self.result.update({'deleted': current_delete})
        return num_deleted

    def baseline_or_audit(self, allow_deletion=False, audit_only=False):
        """Overwrite Sync baseline or audit."""
        try:
            super(ResourceSyncClient, self).baseline_or_audit(allow_deletion,
                                                              audit_only)
            current_app.logger.debug(self)
        except PermissionError:
            pass
        return self.result

    def incremental(self, allow_deletion=False,
                    change_list_uri=None, from_datetime=None):
        """Overwrite Sync incrementail."""
        try:
            super(ResourceSyncClient, self).incremental(allow_deletion,
                                                        change_list_uri,
                                                        from_datetime)
        except PermissionError:
            pass
        return self.result

    def build_resource_list(self, paths=None, set_path=False):
        return super(ResourceSyncClient, self).build_resource_list(paths, set_path)
