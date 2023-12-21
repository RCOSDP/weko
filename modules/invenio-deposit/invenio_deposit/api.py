# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016, 2017 CERN.
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

"""Deposit API."""

import inspect
import uuid
from contextlib import contextmanager
from copy import deepcopy
from functools import partial, wraps

from dictdiffer import patch
from dictdiffer.merge import Merger, UnresolvedConflictsException
from elasticsearch.exceptions import RequestError
from flask import current_app
from flask_login import current_user
from invenio_db import db
from invenio_files_rest.models import Bucket
from invenio_indexer.api import RecordIndexer
from invenio_pidstore import current_pidstore
from invenio_pidstore.errors import PIDInvalidAction
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_pidstore.resolver import Resolver
from invenio_records.signals import after_record_update, before_record_update
from invenio_records_files.api import Record
from invenio_records_files.models import RecordsBuckets
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.local import LocalProxy

from .errors import MergeConflict
from .fetchers import deposit_fetcher as default_deposit_fetcher
from .minters import deposit_minter as default_deposit_minter
from .utils import mark_as_action

current_jsonschemas = LocalProxy(
    lambda: current_app.extensions['invenio-jsonschemas']
)


def index(method=None, delete=False):
    """Decorator to update index.

    :param method: Function wrapped. (Default: ``None``)
    :param delete: If `True` delete the indexed record. (Default: ``None``)
    """
    if method is None:
        return partial(index, delete=delete)

    @wraps(method)
    def wrapper(self_or_cls, *args, **kwargs):
        """Send record for indexing."""
        result = method(self_or_cls, *args, **kwargs)
        try:
            if delete:
                self_or_cls.indexer.delete(result)
            else:
                self_or_cls.indexer.index(result)
        except RequestError:
            current_app.logger.exception('Could not index {0}.'.format(result))
        return result
    return wrapper


def has_status(method=None, status='draft'):
    """Check that deposit has a defined status (default: draft).

    :param method: Function executed if record has a defined status.
        (Default: ``None``)
    :param status: Defined status to check. (Default: ``'draft'``)
    """
    if method is None:
        return partial(has_status, status=status)

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Check current deposit status."""
        if status != self.status:
            raise PIDInvalidAction()

        return method(self, *args, **kwargs)
    return wrapper


def preserve(method=None, result=True, fields=None):
    """Preserve fields in deposit.

    :param method: Function to execute. (Default: ``None``)
    :param result: If `True` returns the result of method execution,
        otherwise `self`. (Default: ``True``)
    :param fields: List of fields to preserve (default: ``('_deposit',)``).
    """
    if method is None:
        return partial(preserve, result=result, fields=fields)

    fields = fields or ('_deposit', )

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Check current deposit status."""
        data = {field: self[field] for field in fields if field in self}
        result_ = method(self, *args, **kwargs)
        replace = result_ if result else self
        for field in data:
            replace[field] = data[field]
        return result_
    return wrapper


class Deposit(Record):
    """Define API for changing deposit state."""

    indexer = RecordIndexer()
    """Default deposit indexer."""

    published_record_class = Record
    """The Record API class used for published records."""

    deposit_fetcher = staticmethod(default_deposit_fetcher)
    """Function used to retrieve the deposit PID."""

    deposit_minter = staticmethod(default_deposit_minter)
    """Function used to mint the deposit PID."""

    @property
    def pid(self):
        """Return an instance of deposit PID."""
        pid = self.deposit_fetcher(self.id, self)
        return PersistentIdentifier.get(pid.pid_type,
                                        pid.pid_value)

    @property
    def record_schema(self):
        """Convert deposit schema to a valid record schema."""
        schema_path = current_jsonschemas.url_to_path(self['$schema'])
        schema_prefix = current_app.config['DEPOSIT_JSONSCHEMAS_PREFIX']
        if schema_path and schema_path.startswith(schema_prefix):
            return current_jsonschemas.path_to_url(
                schema_path[len(schema_prefix):]
            )

    def build_deposit_schema(self, record):
        """Convert record schema to a valid deposit schema.

        :param record: The record used to build deposit schema.
        :returns: The absolute URL to the schema or `None`.
        """
        schema_path = current_jsonschemas.url_to_path(record['$schema'])
        schema_prefix = current_app.config['DEPOSIT_JSONSCHEMAS_PREFIX']
        if schema_path:
            return current_jsonschemas.path_to_url(
                schema_prefix + schema_path
            )

    def fetch_published(self):
        """Return a tuple with PID and published record."""
        pid_type = self['_deposit']['pid']['type']
        pid_value = self['_deposit']['pid']['value']

        resolver = Resolver(
            pid_type=pid_type, object_type='rec',
            getter=partial(self.published_record_class.get_record,
                           with_deleted=True)
        )
        return resolver.resolve(pid_value)

    @preserve(fields=('_deposit', '$schema'))
    def merge_with_published(self):
        """Merge changes with latest published version."""
        pid, first = self.fetch_published()
        lca = first.revisions[self['_deposit']['pid']['revision_id']]
        # ignore _deposit and $schema field
        args = [lca.dumps(), first.dumps(), self.dumps()]
        for arg in args:
            del arg['$schema'], arg['_deposit']
        args.append({})
        m = Merger(*args)
        try:
            m.run()
        except UnresolvedConflictsException:
            raise MergeConflict()
        return patch(m.unified_patches, lca)

    @index
    def commit(self, *args, **kwargs):
        """Store changes on current instance in database and index it."""
        return super(Deposit, self).commit(*args, **kwargs)

    @classmethod
    @index
    def create(cls, data, id_=None, recid=None):
        """Create a deposit.

        Initialize the follow information inside the deposit:

        .. code-block:: python

            deposit['_deposit'] = {
                'id': pid_value,
                'status': 'draft',
                'owners': [user_id],
                'created_by': user_id,
            }

        The deposit index is updated.

        :param data: Input dictionary to fill the deposit.
        :param id_: Default uuid for the deposit.
        :returns: The new created deposit.
        """
        data.setdefault('$schema', current_jsonschemas.path_to_url(
            current_app.config['DEPOSIT_DEFAULT_JSONSCHEMA']
        ))
        if '_deposit' not in data:
            id_ = id_ or uuid.uuid4()
            if not recid:
                cls.deposit_minter(id_, data)
            else:
                cls.deposit_minter(id_, data, recid=recid)

        data['_deposit'].setdefault('owners', list())

        if current_user and current_user.is_authenticated:
            data['owner'] = int(current_user.get_id())
            data['owners'] = [int(data['owner'])]
            data['_deposit']['owner'] = int(data['owner'])
            data['_deposit']['owners'] = [int(data['owner'])]
            data['_deposit']['created_by'] = int(current_user.get_id())
        else:
            data['owner'] = 1
            data['owners'] = [1]
            data['_deposit']['owner'] = 1
            data['_deposit']['owners'] = [1]
        if 'weko_shared_ids' in data:
            data['_deposit']['weko_shared_ids'] = data['weko_shared_ids']
        else:
            data['weko_shared_ids'] = []
            data['_deposit']['weko_shared_ids'] = []
        
        return super(Deposit, cls).create(data, id_=id_)

    @contextmanager
    def _process_files(self, record_id, data):
        """Snapshot bucket and add files in record during first publishing."""
        if self.files:
            assert not self.files.bucket.locked
            self.files.bucket.locked = True
            snapshot = self.files.bucket.snapshot(lock=True)
            data['_files'] = self.files.dumps(bucket=snapshot.id)
            yield data
            db.session.add(RecordsBuckets(
                record_id=record_id, bucket_id=snapshot.id
            ))
        else:
            yield data

    def _publish_new(self, id_=None):
        """Publish new deposit.

        :param id_: The forced record UUID.
        """
        minter = current_pidstore.minters[
            current_app.config['DEPOSIT_PID_MINTER']
        ]
        id_ = id_ or uuid.uuid4()
        record_pid = minter(id_, self)

        self['_deposit']['pid'] = {
            'type': record_pid.pid_type,
            'value': record_pid.pid_value,
            'revision_id': 0,
        }

        data = dict(self.dumps())
        data['$schema'] = self.record_schema

        with self._process_files(id_, data):
            record = self.published_record_class.create(data, id_=id_)

        return record

    def _publish_edited(self):
        """Publish the deposit after for editing."""
        record_pid, record = self.fetch_published()
        if record.revision_id == self['_deposit']['pid']['revision_id']:
            data = dict(self.dumps())
        else:
            data = self.merge_with_published()

        data['$schema'] = self.record_schema
        data['_deposit'] = self['_deposit']
        record = record.__class__(data, model=record.model)
        return record

    @has_status
    @mark_as_action
    def publish(self, pid=None, id_=None):
        """Publish a deposit.

        If it's the first time:

        * it calls the minter and set the following meta information inside
            the deposit:

        .. code-block:: python

            deposit['_deposit'] = {
                'type': pid_type,
                'value': pid_value,
                'revision_id': 0,
            }

        * A dump of all information inside the deposit is done.

        * A snapshot of the files is done.

        Otherwise, published the new edited version.
        In this case, if in the mainwhile someone already published a new
        version, it'll try to merge the changes with the latest version.

        .. note:: no need for indexing as it calls `self.commit()`.

        Status required: ``'draft'``.

        :param pid: Force the new pid value. (Default: ``None``)
        :param id_: Force the new uuid value as deposit id. (Default: ``None``)
        :returns: Returns itself.
        """
        pid = pid or self.pid

        if not pid.is_registered():
            raise PIDInvalidAction()

        self['_deposit']['status'] = 'published'

        if self['_deposit'].get('pid') is None:  # First publishing
            # self._publish_new(id_=id_)
            self['_deposit']['pid'] = {
                'type': pid.pid_type,
                'value': pid.pid_value,
                'revision_id': 0,
            }
        else:  # Update after edit
            record = self._publish_edited()
            record.commit()
        self.commit()
        return self

    def _prepare_edit(self, record):
        """Update selected keys.

        :param record: The record to prepare.
        """
        data = record.dumps()
        # Keep current record revision for merging.
        data['_deposit']['pid']['revision_id'] = record.revision_id
        data['_deposit']['status'] = 'draft'
        data['$schema'] = self.build_deposit_schema(record)
        return data

    @has_status(status='published')
    @index
    @mark_as_action
    def edit(self, pid=None):
        """Edit deposit.

        #. The signal :data:`invenio_records.signals.before_record_update`
           is sent before the edit execution.

        #. The following meta information are saved inside the deposit:

        .. code-block:: python

            deposit['_deposit']['pid'] = record.revision_id
            deposit['_deposit']['status'] = 'draft'
            deposit['$schema'] = deposit_schema_from_record_schema

        #. The signal :data:`invenio_records.signals.after_record_update` is
            sent after the edit execution.

        #. The deposit index is updated.

        Status required: `published`.

        .. note:: the process fails if the pid has status
            :attr:`invenio_pidstore.models.PIDStatus.REGISTERED`.

        :param pid: Force a pid object. (Default: ``None``)
        :returns: A new Deposit object.
        """
        pid = pid or self.pid

        with db.session.begin_nested():
            before_record_update.send(
                current_app._get_current_object(), record=self)

            record_pid, record = self.fetch_published()
            assert PIDStatus.REGISTERED == record_pid.status
            assert record['_deposit'] == self['_deposit']

            self.model.json = self._prepare_edit(record)

            flag_modified(self.model, 'json')
            db.session.merge(self.model)

        after_record_update.send(
            current_app._get_current_object(), record=self)
        return self.__class__(self.model.json, model=self.model)

    @has_status
    @index
    @mark_as_action
    def discard(self, pid=None):
        """Discard deposit changes.

        #. The signal :data:`invenio_records.signals.before_record_update` is
            sent before the edit execution.

        #. It restores the last published version.

        #. The following meta information are saved inside the deposit:

        .. code-block:: python

            deposit['$schema'] = deposit_schema_from_record_schema

        #. The signal :data:`invenio_records.signals.after_record_update` is
            sent after the edit execution.

        #. The deposit index is updated.

        Status required: ``'draft'``.

        :param pid: Force a pid object. (Default: ``None``)
        :returns: A new Deposit object.
        """
        pid = pid or self.pid

        with db.session.begin_nested():
            before_record_update.send(
                current_app._get_current_object(), record=self)

            _, record = self.fetch_published()
            self.model.json = deepcopy(record.model.json)
            self.model.json['$schema'] = self.build_deposit_schema(record)

            flag_modified(self.model, 'json')
            db.session.merge(self.model)

        after_record_update.send(
            current_app._get_current_object(), record=self)
        return self.__class__(self.model.json, model=self.model)

    @has_status
    @index(delete=True)
    def delete(self, force=True, pid=None):
        """Delete deposit.

        Status required: ``'draft'``.

        :param force: Force deposit delete.  (Default: ``True``)
        :param pid: Force pid object.  (Default: ``None``)
        :returns: A new Deposit object.
        """
        pid = pid or self.pid

        if self['_deposit'].get('pid'):
            raise PIDInvalidAction()
        if pid:
            pid.delete()
        return super(Deposit, self).delete(force=force)

    @has_status
    @preserve(result=False)
    def clear(self, *args, **kwargs):
        """Clear only drafts.

        Status required: ``'draft'``.

        Meta information inside `_deposit` are preserved.
        """
        super(Deposit, self).clear(*args, **kwargs)

    @has_status
    @preserve(result=False)
    def update(self, *args, **kwargs):
        """Update only drafts.

        Status required: ``'draft'``.

        Meta information inside `_deposit` are preserved.
        """
        super(Deposit, self).update(*args, **kwargs)

    @has_status
    @preserve
    def patch(self, *args, **kwargs):
        """Patch only drafts.

        Status required: ``'draft'``.

        Meta information inside `_deposit` are preserved.
        """
        return super(Deposit, self).patch(*args, **kwargs)

    def _create_bucket(self):
        """Override bucket creation."""
        return Bucket.create(storage_class=current_app.config[
            'DEPOSIT_DEFAULT_STORAGE_CLASS'
        ])

    @property
    def status(self):
        """Property for accessing deposit status."""
        return self['_deposit']['status']

    @property
    def files(self):
        """List of Files inside the deposit.

        Add validation on ``sort_by`` method: if, at the time of files access,
        the record is not a ``'draft'`` then a
        :exc:`invenio_pidstore.errors.PIDInvalidAction` is rised.
        """
        files_ = super(Deposit, self).files

        if files_:
            sort_by_ = files_.sort_by

            def sort_by(*args, **kwargs):
                """Only in draft state."""
                if 'draft' != self.status:
                    raise PIDInvalidAction()
                return sort_by_(*args, **kwargs)

            files_.sort_by = sort_by

        return files_
