# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2020 CERN.
# Copyright (C) 2021 RERO.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record API."""


import inspect
import warnings
from copy import deepcopy

from flask import current_app
from invenio_db import db
from jsonpatch import apply_patch
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy_continuum.utils import parent_class
from werkzeug.local import LocalProxy

from .dictutils import clear_none, dict_lookup
from .dumpers import Dumper
from .errors import MissingModelError
from .models import RecordMetadata
from .signals import (
    after_record_delete,
    after_record_insert,
    after_record_revert,
    after_record_update,
    before_record_delete,
    before_record_insert,
    before_record_revert,
    before_record_update,
)

_records_state = LocalProxy(lambda: current_app.extensions["invenio-records"])


class RecordBase(dict):
    """Base class for Record and RecordRevision to share common features."""

    model_cls = RecordMetadata
    """SQLAlchemy model class defining which table stores the records."""

    format_checker = None
    """Class-level attribute to specify a default JSONSchema format checker."""

    validator = None
    """Class-level attribute to specify a JSONSchema validator class."""

    dumper = Dumper()
    """Class-level attribute to specify the default data dumper/loader.

    For backward compatibility the dumper used here just produces a deep copy
    of the record.
    """

    enable_jsonref = True
    """Class-level attribute to control if JSONRef replacement is supported."""

    _extensions = []
    """Record extensions registry.

    Allows extensions (like system fields) to be registered on the record.
    """

    def __init__(self, data, model=None, **kwargs):
        """Initialize instance with dictionary data and SQLAlchemy model.

        :param data: Dict with record metadata.
        :param model: :class:`~invenio_records.models.RecordMetadata` instance.
        """
        self.model = model
        for e in self._extensions:
            e.pre_init(self, data, model=model, **kwargs)
        super(RecordBase, self).__init__(data or {})
        for e in self._extensions:
            e.post_init(self, data, model=model, **kwargs)

    @property
    def id(self):
        """Get model identifier."""
        return self.model.id if self.model else None

    @property
    def revision_id(self):
        """Get revision identifier."""
        return self.model.version_id - 1 if self.model else None

    @property
    def created(self):
        """Get creation timestamp."""
        return self.model.created if self.model else None

    @property
    def updated(self):
        """Get last updated timestamp."""
        return self.model.updated if self.model else None

    @property
    def is_deleted(self):
        """Get creation timestamp."""
        return self.model.is_deleted if self.model else None

    def validate(self, format_checker=None, validator=None, **kwargs):
        r"""Validate record according to schema defined in ``$schema`` key.

        :Keyword Arguments:
          * **format_checker** --
            A ``format_checker`` is an instance of class
            :class:`jsonschema.FormatChecker` containing business logic to
            validate arbitrary formats. For example:

            >>> from jsonschema import FormatChecker
            >>> from jsonschema.validators import validate
            >>> checker = FormatChecker()
            >>> checker.checks('foo')(lambda el: el.startswith('foo'))
            <function <lambda> at ...>
            >>> validate('foo', {'format': 'foo'}, format_checker=checker)

            returns ``None``, which means that the validation was successful,
            while

            >>> validate('bar', {'format': 'foo'},
            ...    format_checker=checker)  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
              ...
            ValidationError: 'bar' is not a 'foo'
              ...

            raises a :class:`jsonschema.exceptions.ValidationError`.

          * **validator** --
            A :class:`jsonschema.protocols.Validator` class used for record
            validation. It will be used as `cls` argument when calling
            :func:`jsonschema.validate`. For example

            >>> from jsonschema.validators import extend, Draft4Validator
            >>> NoRequiredValidator = extend(
            ...     Draft4Validator,
            ...     validators={'required': lambda v, r, i, s: None}
            ... )
            >>> schema = {
            ...     'type': 'object',
            ...     'properties': {
            ...         'name': { 'type': 'string' },
            ...         'email': { 'type': 'string' },
            ...         'address': {'type': 'string' },
            ...         'telephone': { 'type': 'string' }
            ...     },
            ...     'required': ['name', 'email']
            ... }
            >>> from jsonschema.validators import validate
            >>> validate({}, schema, NoRequiredValidator)

            returns ``None``, which means that the validation was successful,
            while

            >>> validate({}, schema)  # doctest: +IGNORE_EXCEPTION_DETAIL
            Traceback (most recent call last):
            ...
            ValidationError: 'name' is a required property
            ...

            raises a :class:`jsonschema.exceptions.ValidationError`.
        """
        # 1) For backward compatibility we do not change the method signature
        # (i.e. return a ``None`` value on successful validation).
        # The actual implementation of the validation method is implemented
        # below in _validate() which is also the one used internally to avoid
        # double encoding of the dict to JSON.
        # 2) We ignore **kwargs (but keep it for backward compatibility) as
        # the jsonschema.protocols.Validator only takes the two keyword
        # arguments formater_checker and cls (i.e. validator).
        self._validate(format_checker=format_checker, validator=validator)

    def _validate(self, format_checker=None, validator=None, use_model=False):
        """Implementation of the JSONSchema validation."""
        # Use the encoder to transform Python dictionary into JSON document
        # prior to validation unless we explicitly ask to use the already
        # encoded JSON in the model.
        if use_model:
            json = self.model.json
        else:
            json = self.model_cls.encode(dict(self))

        if "$schema" in self and self["$schema"] is not None:
            # Validate (an error will raise an exception)
            _records_state.validate(
                json,
                self["$schema"],
                # Use defaults of class if not specified by user.
                format_checker=format_checker or self.format_checker,
                cls=validator or self.validator,
            )

        # Return encoded data, so we don't have to double encode.
        return json

    def replace_refs(self):
        """Replace the ``$ref`` keys within the JSON."""
        if self.enable_jsonref:
            return _records_state.replace_refs(self)
        else:
            return self

    def clear_none(self, key=None):
        """Helper method to clear None, empty dict and list values.

        Modifications are done in place.
        """
        clear_none(dict_lookup(self, key) if key else self)

    def dumps(self, dumper=None):
        """Make a dump of the record (defaults to a deep copy of the dict).

        This method produces a version of a record that can be persisted on
        storage such as the database, search or other mediums depending
        on the dumper class used.

        :param dumper: Dumper to use when dumping the record.
        :returns: A ``dict``.
        """
        dumper = dumper or self.dumper

        data = {}

        # Run pre dump extensions
        for e in self._extensions:
            pre_dump_params = inspect.signature(e.pre_dump).parameters
            if "data" in pre_dump_params:
                e.pre_dump(self, data, dumper=dumper)
            else:
                # TODO: Remove in v1.6.0 or later
                warnings.warn(
                    "The pre_dump hook must take a positional argument data.",
                    DeprecationWarning,
                )
                e.pre_dump(self, dumper=dumper)

        dump_params = inspect.signature(dumper.dump).parameters
        if "data" in dump_params:
            # Execute the dump - for backwards compatibility we use the default
            # dumper which returns a deepcopy.
            data = dumper.dump(self, data)
        else:
            # TODO: Remove in v1.6.0 or later
            warnings.warn(
                "The dumper.dump() must take a positional argument data.",
                DeprecationWarning,
            )
            data = dumper.dump(self)

        for e in self._extensions:
            e.post_dump(self, data, dumper=dumper)

        return data

    @classmethod
    def loads(cls, data, loader=None):
        """Load a record dump.

        :param loader: Loader class to use when loading the record.
        :returns: A new :class:`Record` instance.
        """
        # The method is named with in plural to align with dumps (which is
        # named with s even if it should probably have been called "dump"
        # instead.
        loader = loader or cls.dumper

        data = deepcopy(data)  # avoid mutating the original object
        # Run pre load extensions
        for e in cls._extensions:
            e.pre_load(data, loader=loader)

        record = loader.load(data, cls)

        # Run post load extensions
        for e in cls._extensions:
            post_load_params = inspect.signature(e.post_load).parameters
            if "data" in post_load_params:
                e.post_load(record, data, loader=loader)
            else:
                # TODO: Remove in v1.6.0 or later
                warnings.warn(
                    "The post_load hook must take a positional argument data.",
                    DeprecationWarning,
                )
                e.post_load(record, loader=loader)

        return record


class Record(RecordBase):
    """Define API for metadata creation and manipulation."""

    send_signals = True
    """Class-level attribute to control if signals should be sent."""

    @classmethod
    def create(cls, data, id_=None, **kwargs):
        r"""Create a new record instance and store it in the database.

        #. Send a signal :data:`invenio_records.signals.before_record_insert`
           with the new record as parameter.

        #. Validate the new record data.

        #. Add the new record in the database.

        #. Send a signal :data:`invenio_records.signals.after_record_insert`
           with the new created record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~invenio_records.api.RecordBase.validate` for more details.

          * **validator** --
            A :class:`jsonschema.protocols.Validator` class that will be used
            to validate the record. See
            :func:`~invenio_records.api.RecordBase.validate` for more details.

        :param data: Dict with the record metadata.
        :param id_: Specify a UUID to use for the new record, instead of
                    automatically generated.
        :returns: A new :class:`Record` instance.
        """
        with db.session.begin_nested():
            # For backward compatibility we pop them here.
            format_checker = kwargs.pop("format_checker", None)
            validator = kwargs.pop("validator", None)

            # Create the record and the model
            record = cls(data, model=cls.model_cls(id=id_, data=data), **kwargs)

            if cls.send_signals:
                before_record_insert.send(
                    current_app._get_current_object(), record=record
                )

            # Run pre create extensions
            for e in cls._extensions:
                e.pre_create(record)

            # Validate also encodes the data
            record._validate(
                format_checker=format_checker,
                validator=validator,
                use_model=True,  # use model (already encoded) and didn't change
            )

            db.session.add(record.model)

        if cls.send_signals:
            after_record_insert.send(current_app._get_current_object(), record=record)

        # Run post create extensions
        for e in cls._extensions:
            e.post_create(record)

        return record

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Retrieve the record by id.

        Raise a database exception if the record does not exist.

        :param id_: record ID.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: The :class:`Record` instance.
        """
        with db.session.no_autoflush:
            query = cls.model_cls.query.filter_by(id=id_)
            if not with_deleted:
                query = query.filter(cls.model_cls.is_deleted != True)  # noqa
            obj = query.one()
            return cls(obj.data, model=obj)

    @classmethod
    def get_records(cls, ids, with_deleted=False):
        """Retrieve multiple records by id.

        :param ids: List of record IDs.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: A list of :class:`Record` instances.
        """
        with db.session.no_autoflush:
            query = cls.model_cls.query.filter(cls.model_cls.id.in_(ids))
            if not with_deleted:
                query = query.filter(cls.model_cls.is_deleted != True)  # noqa

            return [cls(obj.data, model=obj) for obj in query.all()]

    def patch(self, patch):
        """Patch record metadata.

        :params patch: Dictionary of record metadata.
        :returns: A new :class:`Record` instance.
        """
        warnings.warn(
            "The patch() method is deprecated and will be removed.", DeprecationWarning
        )
        data = apply_patch(dict(self), patch)
        return self.__class__(data, model=self.model)

    def commit(self, format_checker=None, validator=None, **kwargs):
        r"""Store changes of the current record instance in the database.

        #. Send a signal :data:`invenio_records.signals.before_record_update`
           with the current record to be committed as parameter.

        #. Validate the current record data.

        #. Commit the current record in the database.

        #. Send a signal :data:`invenio_records.signals.after_record_update`
            with the committed record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~invenio_records.api.RecordBase.validate` for more details.

          * **validator** --
            A :class:`jsonschema.protocols.Validator` class that will be used
            to validate the record. See
            :func:`~invenio_records.api.RecordBase.validate` for more details.

        :returns: The :class:`Record` instance.
        """
        if self.model is None or self.model.is_deleted:
            raise MissingModelError()

        with db.session.begin_nested():
            if self.send_signals:
                before_record_update.send(
                    current_app._get_current_object(), record=self
                )

            # Run pre commit extensions
            for e in self._extensions:
                e.pre_commit(self, **kwargs)

            # Validate also encodes the data
            json = self._validate(format_checker=format_checker, validator=validator)

            # Thus, we pass the encoded JSON directly to the model to avoid
            # double encoding.
            self.model.json = json
            flag_modified(self.model, "json")

            db.session.merge(self.model)

        if self.send_signals:
            after_record_update.send(current_app._get_current_object(), record=self)

        # Run post commit extensions
        for e in self._extensions:
            e.post_commit(self)

        return self

    def delete(self, force=False):
        """Delete a record.

        If `force` is ``False``, the record is soft-deleted: record data will
        be deleted but the record identifier and the history of the record will
        be kept. This ensures that the same record identifier cannot be used
        twice, and that you can still retrieve its history. If `force` is
        ``True``, then the record is completely deleted from the database.

        #. Send a signal :data:`invenio_records.signals.before_record_delete`
           with the current record as parameter.

        #. Delete or soft-delete the current record.

        #. Send a signal :data:`invenio_records.signals.after_record_delete`
           with the current deleted record as parameter.

        :param force: if ``True``, completely deletes the current record from
               the database, otherwise soft-deletes it.
        :returns: The deleted :class:`Record` instance.
        """
        if self.model is None:
            raise MissingModelError()

        with db.session.begin_nested():
            if self.send_signals:
                before_record_delete.send(
                    current_app._get_current_object(), record=self
                )

            # Run pre delete extensions
            for e in self._extensions:
                e.pre_delete(self, force=force)

            if force:
                db.session.delete(self.model)
            else:
                self.model.is_deleted = True
                db.session.merge(self.model)

        if self.send_signals:
            after_record_delete.send(current_app._get_current_object(), record=self)

        # Run post delete extensions
        for e in self._extensions:
            e.post_delete(self, force=force)

        return self

    def undelete(self):
        """Undelete a soft-deleted record."""
        if self.model is None:
            raise MissingModelError()

        self.model.is_deleted = False

        return self

    def revert(self, revision_id):
        """Revert the record to a specific revision.

        #. Send a signal :data:`invenio_records.signals.before_record_revert`
           with the current record as parameter.

        #. Revert the record to the revision id passed as parameter.

        #. Send a signal :data:`invenio_records.signals.after_record_revert`
           with the reverted record as parameter.

        :param revision_id: Specify the record revision id
        :returns: The :class:`Record` instance corresponding to the revision id
        """
        if self.model is None:
            raise MissingModelError()

        revision = self.revisions[revision_id]

        with db.session.begin_nested():
            if self.send_signals:
                # TODO: arguments to this signal does not make sense.
                # Ought to be both record and revision.
                before_record_revert.send(
                    current_app._get_current_object(), record=self
                )

            for e in self._extensions:
                e.pre_revert(self, revision)

            # Here we explicitly set the json column in order to not
            # encode/decode the json data via the ``data`` property.
            self.model.json = revision.model.json
            flag_modified(self.model, "json")

            db.session.merge(self.model)

        if self.send_signals:
            # TODO: arguments to this signal does not make sense.
            # Ought to be the class being returned just below and should
            # include the revision.
            after_record_revert.send(current_app._get_current_object(), record=self)

        record = self.__class__(self.model.data, model=self.model)

        for e in self._extensions:
            e.post_revert(record, revision)

        return record

    @property
    def revisions(self):
        """Get revisions iterator."""
        if self.model is None:
            raise MissingModelError()

        return RevisionsIterator(self.model)


class RecordRevision(RecordBase):
    """API for record revisions."""

    def __init__(self, model):
        """Initialize instance with the SQLAlchemy model."""
        super(RecordRevision, self).__init__(
            # The version model class does not have the properties of the
            # parent model class, and thus ``model.data`` won't work (which is
            # a Python property on RecordMetadataBase).
            parent_class(model.__class__).decode(model.json),
            model=model,
        )


class RevisionsIterator(object):
    """Iterator for record revisions."""

    def __init__(self, model):
        """Initialize instance with the SQLAlchemy model."""
        self._it = None
        self.model = model

    def __len__(self):
        """Get number of revisions."""
        return self.model.versions.count()

    def __iter__(self):
        """Get iterator."""
        self._it = iter(self.model.versions)
        return self

    def __next__(self):
        """Get next revision item."""
        return RecordRevision(next(self._it))

    def __getitem__(self, revision_id):
        """Get a specific revision.

        Revision id is always smaller by 1 from version_id. This was initially
        to ensure that record revisions was zero-indexed similar to arrays
        (e.g. you could do ``record.revisions[0]``). Due to SQLAlchemy
        increasing the version counter via Python instead of the SQL
        insert/update query it's possible to have an "array with holes" and
        thus having it zero-indexed does not make much sense (thus it's like
        this for historical reasons and has not been changed because it's
        diffcult to change - e.g. implies all indexed records in existing
        instances having to be updated.)
        """
        if revision_id < 0:
            return RecordRevision(self.model.versions[revision_id])
        try:
            return RecordRevision(
                self.model.versions.filter_by(version_id=revision_id + 1).one()
            )
        except NoResultFound:
            raise IndexError

    def __contains__(self, revision_id):
        """Test if revision exists."""
        try:
            self[revision_id]
            return True
        except IndexError:
            return False

    def __reversed__(self):
        """Allows to use reversed operator."""
        for version_index in range(self.model.versions.count()):
            yield RecordRevision(self.model.versions[-(version_index + 1)])
