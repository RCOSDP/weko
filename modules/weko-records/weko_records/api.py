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

"""Record API."""

import urllib.parse
import pickle
from typing import Union
import json
import re
import sys
import traceback

from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl.query import QueryString
from flask import current_app, request
from flask_babelex import gettext as _
from invenio_db import db
from invenio_pidstore.models import PersistentIdentifier, PIDStatus
from invenio_records.api import Record
from invenio_records.errors import MissingModelError
from invenio_records.models import RecordMetadata
from invenio_records.signals import after_record_delete, after_record_insert, \
    after_record_revert, after_record_update, before_record_delete, \
    before_record_insert, before_record_revert, before_record_update
from invenio_search import RecordsSearch
from jsonpatch import apply_patch
from sqlalchemy import desc, cast, String
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.expression import desc
from werkzeug.local import LocalProxy
from weko_authors.models import Authors


from .fetchers import weko_record_fetcher
from .models import (
    FeedbackMailList as _FeedbackMailList,
    RequestMailList as _RequestMailList,
    ItemApplication as _ItemApplication,
    FileMetadata, ItemMetadata, ItemReference, ItemType,
    ItemTypeEditHistory as ItemTypeEditHistoryModel,
    ItemTypeMapping, ItemTypeName, ItemTypeProperty,
    ItemTypeJsonldMapping, SiteLicenseInfo, SiteLicenseIpAddress
)


_records_state = LocalProxy(
    lambda: current_app.extensions['invenio-records'])


class RecordBase(dict):
    """Base class for Record and RecordBase."""

    def __init__(self, data, model=None):
        """Initialize instance with dictionary data and SQLAlchemy model.

        :param data: Dict with record metadata.
        :param model: :class:`~weko_records.models.MappingMetadata` instance.
        """
        self.model = model
        super(RecordBase, self).__init__(data or {})

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

    def validate(self, **kwargs):
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
            A :class:`jsonschema.IValidator` class used for record validation.
            It will be used as `cls` argument when calling
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
        if '$schema' in self and self['$schema'] is not None:
            kwargs['cls'] = kwargs.pop('validator', None)
            _records_state.validate(self, self['$schema'], **kwargs)

    def replace_refs(self):
        """Replace the ``$ref`` keys within the JSON."""
        return _records_state.replace_refs(self)

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        return pickle.loads(pickle.dumps(dict(self), -1))


class ItemTypeNames(RecordBase):
    """Define API for ItemTypeName creation and manipulation."""

    @classmethod
    def update(cls, obj):
        """Update method."""
        def commit(olst, flg):
            with db.session.begin_nested():
                for lst in olst:
                    lst.has_site_license = flg
                    flag_modified(lst, 'has_site_license')
                    db.session.merge(lst)

        if isinstance(obj, dict):
            for k, v in obj.items():
                if v and isinstance(v, list):
                    ids = []
                    for lst in v:
                        id = lst.get('id')
                        if id:
                            ids.append(id)
                    olst = cls.get_all_by_id(ids)
                    commit(olst, True if 'allow' in k else False)

    @classmethod
    def get_all_by_id(cls, ids, with_deleted=False):
        """Retrieve item types by ids.

        :param ids: List of item type IDs.
        :returns: A list of :class:`ItemTypeName` instances.
        """
        with db.session.no_autoflush:
            query = ItemTypeName.query.filter(ItemTypeName.id.in_(ids))
            if not with_deleted:
                query = query.filter_by(is_active=True)
            return query.all()

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Retrieve the item type name by id.

        :param id_: Identifier of item type name.
        :param with_deleted: If `True` then it includes deleted item type name.
        :returns: The :class:`ItemTypeName` instance.
        """
        with db.session.no_autoflush:
            query = ItemTypeName.query.filter_by(id=id_)
            if not with_deleted:
                query = query.filter_by(is_active=True)  # noqa
            return query.one_or_none()

    @classmethod
    def get_name_and_id_all(cls):
        """get name and id all."""
        query = db.session.query(ItemTypeName).with_entities(ItemTypeName.name, ItemTypeName.id)
        return query.all()

    def delete(self, force=False):
        """Delete an item type name.

        If `force` is ``False``, the record is soft-deleted: record data will
        be deleted but the record identifier and the history of the record will
        be kept. This ensures that the same record identifier cannot be used
        twice, and that you can still retrieve its history. If `force` is
        ``True``, then the record is completely deleted from the database.

        #. Send a signal :data:`weko_records.signals.before_record_delete`
           with the current record as parameter.

        #. Delete or soft-delete the current record.

        #. Send a signal :data:`weko_records.signals.after_record_delete`
           with the current deleted record as parameter.

        :param force: if ``True``, deletes the current item type name
               from the database, otherwise soft-deletes it.
        :returns: The deleted :class:`ItemTypeName` instance.
        """
        with db.session.begin_nested():
            before_record_delete.send(
                current_app._get_current_object(),
                record=self
            )

            if force:
                db.session.delete(self)
            else:
                self.is_active = False
                db.session.merge(self)

        after_record_delete.send(
            current_app._get_current_object(),
            record=self
        )
        return self

    def restore(self):
        """Restore an logically deleted item type name.

        #. Restore the current record.

        :returns: The restored :class:`ItemTypeName` instance.
        """
        with db.session.begin_nested():
            self.is_active = True
            db.session.merge(self)

        return self


class ItemTypes(RecordBase):
    """Define API for item type creation and manipulation."""

    @classmethod
    def create(cls, item_type_name=None, name=None, schema=None, form=None,
               render=None, tag=1):
        r"""Create a new item type instance and store it in the database.

        #. Send a signal :data:`weko_records.signals.before_record_insert`
           with the new record as parameter.

        #. Validate the new record data.

        #. Add the new record in the database.

        #. Send a signal :data:`weko_records.signals.after_record_insert`
           with the new created record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

          * **validator** --
            A :class:`jsonschema.IValidator` class that will be used to
            validate the record. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

        :param item_type_name: Instance of class:`ItemTypeName`.
        :param name: Name of item type.
        :param schema: Schema in JSON format.
        :param form: Schema form in JSON format.
        :param render: Page render information in JSON format.
        :param tag: Tag of item type.
        :returns: A new :class:`ItemTypes` instance.
        """
        if not name:
            raise ValueError('Item type name cannot be empty.')
        cur_names = map(lambda itemtype: itemtype.name, cls.get_latest(True))
        if name in cur_names:
            raise ValueError('Item type name is already in use.')

        with db.session.begin_nested():
            record = cls(schema)

            before_record_insert.send(
                current_app._get_current_object(),
                record=record,
            )
            if item_type_name is None:
                item_type_name = ItemTypeName(name=name)

            # record.validate(**kwargs)

            record.model = ItemType(item_type_name=item_type_name,
                                    schema=record, form=form, render=render,
                                    tag=tag)
            db.session.add(item_type_name)

        after_record_insert.send(
            current_app._get_current_object(),
            record=record,
        )
        return record

    @classmethod
    def update(cls, id_=0, name=None, schema=None, form=None, render=None,
               tag=1):
        r"""Update an item type instance and store it in the database.

        :param id_: Identifier of item type.
        :param name: Name of item type.
        :param schema: Schema in JSON format.
        :param form: Schema form in JSON format.
        :param render: Page render information in JSON format.
        :param tag: Tag of item type.
        :returns: The :class:`ItemTypes` instance.
        """
        assert name
        item_type_name = None
        # Create a new record
        if not id_ or id_ <= 0:
            return cls.create(item_type_name=item_type_name, name=name,
                              schema=schema, form=form, render=render, tag=tag)
        # Update for existed record
        else:
            with db.session.no_autoflush:
                # Get the item type by identifier
                result = cls.get_by_id(id_=id_)
                if result is None:
                    current_app.logger.debug('Invalid id: {}'.format(id_))
                    raise ValueError(_('Invalid id.'))
                return cls.update_item_type(
                    form, id_, name, render, result, schema
                )

    @classmethod
    def update_item_type(cls, form, id_, name, render, result, schema):
        """Update Item Type.

        :param form: Schema form in JSON format.
        :param id_: Identifier of item type.
        :param name: Name of item type.
        :param render: Page render information in JSON format.
        :param result: Item Type.
        :param schema: Schema in JSON format.
        :return:
        """
        # Get the latest tag of item type by name identifier
        result = cls.get_by_name_id(name_id=result.name_id)
        old_render = pickle.loads(pickle.dumps(result[0].render, -1))
        new_render = pickle.loads(pickle.dumps(render, -1))

        updated_name = False
        tag = result[0].tag + 1
        # Check if the name has been changed
        item_type_name = result[0].item_type_name
        if name != item_type_name.name:
            # Check if the new name has been existed
            result = ItemTypeName.query.filter_by(
                name=name).filter_by(is_active=True).one_or_none()
            if result is not None:
                current_app.logger.debug(
                    'Invalid name: {}'.format(name))
                raise ValueError(_('Invalid name.'))
            item_type_name.name = name
            updated_name = True

        upgrade_version = current_app.config[
            'WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED'
        ]
        if not upgrade_version and not updated_name:
            cls.__update_metadata(id_, item_type_name.name, old_render,
                                  new_render)
            return cls.__update_item_type(id_, schema, form, render)

        from weko_records.utils import check_to_upgrade_version
        upgrade_version = True if \
            check_to_upgrade_version(old_render, new_render) else False

        if upgrade_version:
            return cls.create(item_type_name=item_type_name, name=name,
                              schema=schema, form=form, render=render,
                              tag=tag)
        else:
            return cls.__update_item_type(id_, schema, form, render)

    @classmethod
    def __update_item_type(cls, id_, schema, form, render):
        current_item_type = cls.get_record(id_)
        current_item_type.model.schema = schema
        current_item_type.model.form = form
        current_item_type.model.render = render
        return current_item_type.commit()

    @classmethod
    def __update_metadata(
        cls, item_type_id, item_type_name, old_render, new_render
    ):
        """Update metadata.

        :param item_type_id: Item type identifiers.
        :param item_type_name: Item type name.
        :param old_render: Old render.
        :param new_render: New render.
        """
        def __diff(list1, list2):
            """Compare list.

            :param list1: List 1.
            :param list2: List 2.
            :return:
            """
            return list(list(set(list1) - set(list2)))

        def __del_data(_json, diff_keys):
            """Delete metadata.

            :param _json: Metadata.
            :param diff_keys: Diff key list.
            :return:
            """
            is_del = False
            for k in diff_keys:
                if k in _json:
                    del _json[k]
                    is_del = True
            return is_del

        def __get_delete_mapping_key(item_type_mapping, _delete_list):
            """Get mapping key of deleted key.

            :param item_type_mapping: item_type_mapping.
            :param _delete_list: _delete_list.
            :return:
            """
            result = []
            for key in _delete_list:
                prop_mapping = item_type_mapping.get(key, {}).get("jpcoar_mapping", {})
                if prop_mapping and isinstance(prop_mapping, dict):
                    result.extend(list(prop_mapping.keys()))
            return result

        def __update_es_data(_es_data, _delete_list):
            """Update metadata on ElasticSearch.

            :param _es_data: Elasticsearch data.
            :param _delete_list: delete list
            """
            item_type_mapping = Mapping.get_record(item_type_id=item_type_id)
            delete_mapping_key_list = __get_delete_mapping_key(item_type_mapping, _delete_list)
            es_updated_data = []
            for _data in _es_data:
                source = _data.get('_source', {})
                item_metadata = _data.get('_source', {}).get('_item_metadata',
                                                             {})
                is_update = False
                if __del_data(item_metadata, _delete_list):
                    is_update = True
                if __del_data(source, delete_mapping_key_list):
                    is_update = True
                if is_update:
                    es_updated_data.append(_data)

            from weko_deposit.api import WekoIndexer
            WekoIndexer().bulk_update(es_updated_data)

        def __update_db(db_records, _delete_list):
            """Update metadata in Database.

            :param db_records:Db data
            :param _delete_list: delete list
            """
            try:
                with db.session.begin_nested():
                    for db_record in db_records:
                        record_json = pickle.loads(pickle.dumps(db_record.json, -1))
                        if __del_data(record_json, _delete_list):
                            db_record.json = record_json
                            db.session.merge(db_record)
                db.session.commit()
            except SQLAlchemyError as e:
                db.session.rollback()
                current_app.logger.error(e)
                raise e

        def __update_record_metadata(_record_ids, _delete_list):
            """Update Record Metadata table.

            :param _record_ids: Record identifiers.
            :param _delete_list: Delete list
            :return:
            """
            query = db.session.query(RecordMetadata).filter(
                RecordMetadata.id.in_(_record_ids))
            db_records = query.all()
            if len(db_records) == 0:
                return
            __update_db(db_records, _delete_list)

        def __update_item_metadata(_record_ids, _delete_list):
            """Update Item Metadata table.

            :param _record_ids: Record identifiers.
            :param _delete_list: Delete list.
            :return:
            """
            query = db.session.query(ItemMetadata).filter(
                ItemMetadata.id.in_(_record_ids))
            db_records = query.all()
            if len(db_records) == 0:
                return
            __update_db(db_records, _delete_list)

        # Get deleted properties
        old_meta_list = old_render.get('table_row')
        new_meta_list = new_render.get('table_row')
        delete_list = __diff(old_meta_list, new_meta_list)
        if len(delete_list) == 0:
            return

        # Get records on ElasticSearch based on Item Type Name
        records = cls.__get_records_by_item_type_name(item_type_name)
        record_ids = []
        es_data = []
        for record in records:
            rec_id = record.get("_id")
            _source = record.get("_source", {})
            _item_type_id = _source.get("_item_metadata", {}).get(
                "item_type_id")
            if rec_id and _source and str(item_type_id) == str(_item_type_id):
                record_ids.append(rec_id)
                es_data.append(dict(
                    _id=rec_id,
                    _source=_source
                ))
        if len(record_ids) == 0:
            return

        # Update record metadata in DB based on data from ES.
        __update_record_metadata(record_ids, delete_list)
        # Update item metadata in DB based on data from ES.
        __update_item_metadata(record_ids, delete_list)
        # Update Elasticsearch data
        __update_es_data(es_data, delete_list)

    @classmethod
    def __get_records_by_item_type_name(cls, item_type_name):
        """Get records on Elasticsearch by Item Type Name.

        :param item_type_name: Item Type Name.
        :return: Record list.
        """
        from weko_search_ui.utils import execute_search_with_pagination
        result = []
        try:
            search = RecordsSearch(
                index=current_app.config['SEARCH_UI_SEARCH_INDEX'])
            search = search.query('term', **{"itemtype.keyword": item_type_name})
            search = search.sort('-publish_date', '-_updated')
            result = execute_search_with_pagination(search, -1)
        except NotFoundError as e:
            current_app.logger.debug("Indexes do not exist yet: ", str(e))
        return result

    @classmethod
    def get_record(cls, id_, with_deleted=False):
        """Retrieve the item type by id.

        :param id_: Identifier of item type.
        :param with_deleted: If `True` then it includes deleted item types.
        :returns: The :class:`ItemTypes` instance.
        """
        with db.session.no_autoflush:
            query = ItemType.query.filter_by(id=id_)
            if not with_deleted:
                query = query.filter(ItemType.is_deleted.is_(False))  # noqa
            obj = query.one_or_none()
            if obj is None:
                return None
            return cls(obj.schema, model=obj)

    @classmethod
    def get_records(cls, ids, with_deleted=False):
        """Retrieve multiple item types by id.

        :param ids: List of item type IDs.
        :param with_deleted: If `True` then it includes deleted item types.
        :returns: A list of :class:`ItemTypes` instances.
        """
        with db.session.no_autoflush:
            query = ItemType.query.filter(ItemType.id.in_(ids))
            if not with_deleted:
                query = query.filter(ItemType.is_deleted.is_(False))  # noqa
            return [cls(obj.schema, model=obj) for obj in query.all()]

    @classmethod
    def get_by_id(cls, id_, with_deleted=False):
        """Retrieve the item type by id.

        Args:
            id_ (int): Identifier of item type.
            with_deleted (bool): If `True` then it includes deleted item types.

        Returns:
            ItemType: Item type model instance.
        """
        with db.session.no_autoflush:
            query = ItemType.query.filter_by(id=id_)
            if not with_deleted:
                query = query.filter(ItemType.is_deleted.is_(False))  # noqa
            obj = query.one_or_none()
        return obj if isinstance(obj, ItemType) else None

    @classmethod
    def get_by_name(cls, name_, with_deleted=False):
        """Retrieve the item type by item type name.

        Args:
            name_ (str): Name of item type.
        with_deleted (bool): If `True` then it includes deleted item types.

        Returns:
            ItemType: Item type model instance.
        """
        with db.session.no_autoflush:
            query = ItemTypeName.query.filter_by(name=name_)
            if not with_deleted:
                query = query.filter(ItemType.is_deleted.is_(False))  # noqa
            itemTypeName = query.one_or_none()
            query = ItemType.query.filter_by(name_id=itemTypeName.id)
            if not with_deleted:
                query = query.filter(ItemType.is_deleted.is_(False))  # noqa
            obj = query.one_or_none()
        return obj if isinstance(obj, ItemType) else None

    @classmethod
    def get_by_name_id(cls, name_id, with_deleted=False):
        """Retrieve multiple item types by name identifier.

        :param name_id: Name identifier of item type.
        :param with_deleted: If `True` then it includes deleted item types.
        :returns: A list of :class:`ItemTypes` instance.
        """
        with db.session.no_autoflush:
            query = ItemType.query.filter_by(name_id=name_id)
            if not with_deleted:
                query = query.filter(ItemType.is_deleted.is_(False))  # noqa
            return query.order_by(desc(ItemType.tag)).all()

    @classmethod
    def get_records_by_name_id(cls, name_id, with_deleted=False):
        """Retrieve multiple item types by name identifier.

        :param name_id: Name identifier of item type.
        :param with_deleted: If `True` then it includes deleted item types.
        :returns: A list of :class:`ItemTypes` instance.
        """
        with db.session.no_autoflush:
            query = ItemType.query.filter_by(name_id=name_id)
            if not with_deleted:
                query = query.filter(ItemType.is_deleted.is_(False))  # noqa
            return [cls(obj.schema, model=obj) for obj in query.all()]

    @classmethod
    def get_latest(cls, with_deleted=False):
        """Retrieve the latest item types.

        :param with_deleted: If `True` then it includes deleted item types.
        :returns: A list of :class:`ItemTypes` instances.
        """
        with db.session.no_autoflush:
            query = ItemTypeName.query
            if not with_deleted:
                query = query.join(ItemType).filter(
                    ItemType.is_deleted.is_(False))
            return query.order_by(ItemTypeName.id).all()

    @classmethod
    def get_latest_with_item_type(cls, with_deleted=False):
        """Retrieve the latest item types with all its associated data.

        :param with_deleted: If `True` then it includes deleted item types.
        :returns: A list of :class:`ItemTypeName` joined w/ :class:`ItemType`.
        """
        with db.session.no_autoflush:
            query = ItemTypeName.query.join(ItemType) \
                .add_columns(ItemTypeName.name, ItemType.id,
                             ItemType.harvesting_type, ItemType.is_deleted,
                             ItemType.tag)
            if not with_deleted:
                query = query.filter(ItemType.is_deleted.is_(False))
            return query.order_by(ItemTypeName.id).all()

    @classmethod
    def get_latest_custorm_harvesting(cls, with_deleted=False,
                                      harvesting_type=False):
        """Retrieve the latest item types.

        :param
        with_deleted: If `True` then it includes deleted item types.
        harvesting_type: If `True` then it includes multy item types.
        :returns: A list of :class:`ItemTypes` instances.
        """
        with db.session.no_autoflush:
            query = ItemTypeName.query
            if not with_deleted:
                query = query.join(ItemType).filter(
                    ItemType.is_deleted.is_(False),
                    ItemType.harvesting_type.is_(harvesting_type)
                )
            return query.order_by(ItemTypeName.id).all()

    @classmethod
    def get_all(cls, with_deleted=False):
        """Retrieve all item types.

        :param with_deleted: If `True` then it includes deleted item types.
        :returns: A list of :class:`ItemTypes` instances.
        """
        with db.session.no_autoflush:
            query = ItemType.query
            if not with_deleted:
                query = query.filter(ItemType.is_deleted.is_(False))  # noqa
            return query.order_by(ItemType.name_id, ItemType.tag).all()

    def patch(self, patch):
        """Patch item type metadata.

        :params patch: Dictionary of item type metadata.
        :returns: A new :class:`ItemTypes` instance.
        """
        data = apply_patch(dict(self), patch)
        return self.__class__(data, model=self.model)

    def commit(self, **kwargs):
        r"""Store changes of the current item type instance in the database.

        #. Send a signal :data:`weko_records.signals.before_record_update`
           with the current record to be committed as parameter.

        #. Validate the current record data.

        #. Commit the current record in the database.

        #. Send a signal :data:`weko_records.signals.after_record_update`
            with the committed record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

          * **validator** --
            A :class:`jsonschema.IValidator` class that will be used to
            validate the record. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

        :returns: The :class:`ItemTypes` instance.
        """
        if self.model is None:
            raise MissingModelError()

        with db.session.begin_nested():
            before_record_update.send(
                current_app._get_current_object(),
                record=self
            )

            # self.validate(**kwargs)

            # self.model.json = dict(self)
            # flag_modified(self.model, 'schema')
            # flag_modified(self.model, 'form')
            # flag_modified(self.model, 'render')

            db.session.merge(self.model)

        after_record_update.send(
            current_app._get_current_object(),
            record=self
        )
        return self

    def delete(self, force=False):
        """Delete an item type.

        If `force` is ``False``, the record is soft-deleted: record data will
        be deleted but the record identifier and the history of the record will
        be kept. This ensures that the same record identifier cannot be used
        twice, and that you can still retrieve its history. If `force` is
        ``True``, then the record is completely deleted from the database.

        #. Send a signal :data:`weko_records.signals.before_record_delete`
           with the current record as parameter.

        #. Delete or soft-delete the current record.

        #. Send a signal :data:`weko_records.signals.after_record_delete`
           with the current deleted record as parameter.

        :param force: if ``True``, deletes the current item type from
               the database, otherwise soft-deletes it.
        :returns: The deleted :class:`ItemTypes` instance.
        """
        if self.model is None:
            raise MissingModelError()

        with db.session.begin_nested():
            before_record_delete.send(
                current_app._get_current_object(),
                record=self
            )

            if force:
                db.session.delete(self.model)
            else:
                self.model.is_deleted = True
                db.session.merge(self.model)

        after_record_delete.send(
            current_app._get_current_object(),
            record=self
        )
        return self

    def revert(self, revision_id):
        """Revert the item type to a specific revision.

        #. Send a signal :data:`weko_records.signals.before_record_revert`
           with the current record as parameter.

        #. Revert the record to the revision id passed as parameter.

        #. Send a signal :data:`weko_records.signals.after_record_revert`
           with the reverted record as parameter.

        :param revision_id: Specify the item type revision id
        :returns: The :class:`ItemTypes` instance corresponding to the revision
        id
        """
        if self.model is None:
            raise MissingModelError()

        revision = self.revisions[revision_id]

        with db.session.begin_nested():
            before_record_revert.send(
                current_app._get_current_object(),
                record=self
            )

            self.model.json = dict(revision)

            db.session.merge(self.model)

        after_record_revert.send(
            current_app._get_current_object(),
            record=self
        )
        return self.__class__(self.model.json, model=self.model)

    def restore(self):
        """Restore an logically deleted item type.

        #. Restore the current record.

        :returns: The restored :class:`ItemTypes` instance.
        """
        if self.model is None:
            raise MissingModelError()

        with db.session.begin_nested():
            self.model.is_deleted = False
            db.session.merge(self.model)

        return self

    @property
    def revisions(self):
        """Get revisions iterator."""
        if self.model is None:
            raise MissingModelError()

        return RevisionsIterator(self.model)

    @classmethod
    def reload(cls, itemtype_id, specified_list=[], renew_value='None'):
        """reload itemtype properties.

        Args:
            itemtype_id (_type_): _description_
            specified_list: renew properties id list
            renew_value: None, ALL, VAL, LOC
        """
        # with db.session.begin_nested():
        result = {"msg":"Update ItemType({})".format(itemtype_id),"code":0}
        item_type = ItemTypes.get_by_id(itemtype_id)
        data = pickle.loads(pickle.dumps(item_type.render, -1))

        pat1 = re.compile(r'cus_(\d+)')
        for idx, i in enumerate(data['table_row_map']['form']):
            if isinstance(i,dict) and 'key' in i:
                _prop_id = i['key']
                if _prop_id.startswith('item_'):
                    _tmp = data['meta_list'][_prop_id]['input_type']
                    multiple_flg = data['meta_list'][_prop_id]['option']['multiple']
                    if pat1.match(_tmp):
                        _tmp = int(_tmp.replace('cus_', ''))
                        if specified_list and _tmp not in specified_list:
                            continue
                        _prop = ItemTypeProps.get_record(_tmp)
                        if _prop:
                            # data['meta_list'][_prop_id] = json.loads('{"input_maxItems": "9999","input_minItems": "1","input_type": "cus_'+str(_prop.id)+'","input_value": "","option": {"crtf": false,"hidden": false,"multiple": true,"oneline": false,"required": false,"showlist": false},"title": "'+_prop.name+'","title_i18n": {"en": "", "ja": "'+_prop.name+'"}}')
                            # data['schemaeditor']['schema'][_prop_id]=pickle.loads(pickle.dumps(_prop.schema, -1))
                            if multiple_flg:
                                data['table_row_map']['schema']['properties'][_prop_id]['items']=pickle.loads(pickle.dumps(_prop.schema, -1))
                                data['table_row_map']['schema']['properties'][_prop_id]['type']="array"
                                if 'maxItems' not in data['table_row_map']['schema']['properties'][_prop_id]:
                                    data['table_row_map']['schema']['properties'][_prop_id]['maxItems']=9999
                                if 'minItems' not in data['table_row_map']['schema']['properties'][_prop_id]:
                                    data['table_row_map']['schema']['properties'][_prop_id]['minItems']=1
                                if 'properties' in data['table_row_map']['schema']['properties'][_prop_id]:
                                    data['table_row_map']['schema']['properties'][_prop_id].pop('properties')
                                if 'format' in data['table_row_map']['schema']['properties'][_prop_id]:
                                    data['table_row_map']['schema']['properties'][_prop_id].pop('format')

                                tmp_data = pickle.loads(pickle.dumps(data['table_row_map']['form'][idx], -1))
                                _forms = json.loads(json.dumps(pickle.loads(pickle.dumps(_prop.forms, -1))).replace('parentkey',_prop_id))
                                data['table_row_map']['form'][idx]=pickle.loads(pickle.dumps(_forms, -1))
                                cls.update_attribute_options(tmp_data, data['table_row_map']['form'][idx], renew_value)
                                cls.update_property_enum(item_type.render['table_row_map']['schema']['properties'][_prop_id],data['table_row_map']['schema']['properties'][_prop_id])
                            else:
                                tmp_data = pickle.loads(pickle.dumps(data['table_row_map']['form'][idx], -1))
                                data['table_row_map']['schema']['properties'][_prop_id]=pickle.loads(pickle.dumps(_prop.schema, -1))
                                # cls.update_property_enum(item_type.render['table_row_map']['schema']['properties'],data['table_row_map']['schema']['properties'][_prop_id])
                                _form = json.loads(json.dumps(pickle.loads(pickle.dumps(_prop.form, -1))).replace('parentkey',_prop_id))
                                data['table_row_map']['form'][idx]=pickle.loads(pickle.dumps(_form, -1))
                                cls.update_attribute_options(tmp_data, data['table_row_map']['form'][idx], renew_value)
                                cls.update_property_enum(item_type.render['table_row_map']['schema']['properties'][_prop_id],data['table_row_map']['schema']['properties'][_prop_id])

        from weko_itemtypes_ui.utils import fix_json_schema,update_required_schema_not_exist_in_form, update_text_and_textarea

        table_row_map = data.get('table_row_map')
        json_schema = fix_json_schema(table_row_map.get('schema'))

        json_form = table_row_map.get('form')
        json_schema = update_required_schema_not_exist_in_form(
            json_schema, json_form)

        if itemtype_id != 0:
            json_schema, json_form = update_text_and_textarea(
                itemtype_id, json_schema, json_form)

        if 'schemaeditor' in data:
            if 'schema' in data['schemaeditor']:
                data['schemaeditor']['schema'] = json_schema

        # item_type_mapping = (
        #             ItemTypeMapping.query.filter(ItemTypeMapping.item_type_id == itemtype_id)
        #             .order_by(desc(ItemTypeMapping.created))
        #             .first()
        #         )
        # data['table_row_map']['mapping'] = item_type_mapping.mapping if item_type_mapping else {}

        # current_app.logger.error("Update ItemType({})".format(itemtype_id))
        # current_app.logger.error("Update data({})".format(data))
        # current_app.logger.error("Update json_schema({})".format(json_schema))

        # print(data)

        record = cls.update(id_=itemtype_id,
                                      name=item_type.item_type_name.name,
                                      schema=json_schema,
                                      form=table_row_map.get('form'),
                                      render=data)
        mapping = Mapping.get_record(itemtype_id)
        if mapping:
            _a = [p for p in data.get("table_row") if p in mapping]
            if len(_a) is not len(data.get("table_row")):
                mapping.model.mapping = table_row_map.get('mapping')
                flag_modified(mapping.model, 'mapping')
                db.session.add(mapping.model)
                result['msg'] = "Fix ItemType({}) mapping".format(itemtype_id)
                result['code'] = 0

        ItemTypeEditHistory.create_or_update(
            item_type_id=record.model.id,
            user_id=1,
            notes=data.get('edit_notes', {})
        )

        return result

    @classmethod
    def update_property_enum(cls, old_value, new_value):
        managed_key_list = current_app.config.get("WEKO_RECORDS_MANAGED_KEYS")
        if isinstance(old_value, dict):
            for key, value in old_value.items():
                if isinstance(old_value[key], dict):
                    if key in new_value and key in old_value:
                        if "enum" in old_value[key]:
                            if key not in managed_key_list:
                                if old_value[key]["enum"] != [None]:
                                    new_value[key]["enum"] = old_value[key]["enum"]
                        if "currentEnum" in old_value[key]:
                            if key not in managed_key_list:
                                if old_value[key]["currentEnum"] != [None]:
                                    new_value[key]["currentEnum"] = old_value[key]["currentEnum"]
                        # if "title" in old_value[key]:
                        #     if old_value[key]["title"] != "":
                        #         new_value[key]["title"] = old_value[key]["title"]
                        # if "title_i18n" in old_value[key]:
                        #     if old_value[key]["title_i18n"] != "":
                        #         new_value[key]["title_i18n"] = old_value[key]["title_i18n"]
                        if "enum" not in old_value[key] and "currentEnum" not in old_value[key]:
                            if key in new_value and key in old_value:
                                cls.update_property_enum(old_value[key], new_value[key])

    @classmethod
    def update_attribute_options(cls, old_value, new_value, renew_value = 'None'):
        managed_key_list = current_app.config.get("WEKO_RECORDS_MANAGED_KEYS")
        if isinstance(old_value, list):
           for i in old_value:
               cls.update_attribute_options(i, new_value, renew_value)
        elif isinstance(old_value, dict):
            if "key" in old_value:
                key = old_value["key"]
                new_item = cls.getItemByItemsKey(new_value,key)
                if new_item is not None:
                    isHide = False
                    isShowList = False
                    isNonDisplay = False
                    isSpecifyNewline = False
                    isRequired = False
                    title_i18n = None
                    title_i18n_temp = None
                    titleMap = None
                    title = None

                    if "title" in old_value:
                        title = old_value["title"]
                    if "isHide" in old_value:
                        isHide = old_value["isHide"]
                    if "isShowList" in old_value:
                        isShowList = old_value["isShowList"]
                    if "isNonDisplay" in old_value:
                        isNonDisplay = old_value["isNonDisplay"]
                    if "isSpecifyNewline" in old_value:
                        isSpecifyNewline = old_value["isSpecifyNewline"]
                    if "required" in old_value:
                        isRequired = old_value["required"]
                    if "title_i18n" in old_value and renew_value not in ["ALL", "LOC"]:
                        title_i18n_temp = old_value["title_i18n"]
                        title_i18n = title_i18n_temp
                    if "title_i18n_temp" in old_value and renew_value not in ["ALL", "LOC"]:
                        title_i18n_temp = old_value["title_i18n_temp"]
                    if ("titleMap" in old_value and key.split(".")[-1] not in managed_key_list) or ("titleMap" in old_value and renew_value not in ["ALL", "VAL"]) :
                        titleMap = old_value["titleMap"]

                    new_item["isHide"] = isHide
                    new_item["isShowList"] = isShowList
                    new_item["isNonDisplay"] = isNonDisplay
                    new_item["isSpecifyNewline"] = isSpecifyNewline
                    new_item["required"] = isRequired
                    if title:
                        new_item["title"] = title
                    if title_i18n:
                        new_item["title_i18n"] = title_i18n
                    if title_i18n_temp:
                        new_item["title_i18n_temp"] = title_i18n_temp
                    if titleMap:
                        new_item["titleMap"] = titleMap
                    if 'items' in old_value:
                        cls.update_attribute_options(old_value["items"], new_item, renew_value)

    @classmethod
    def getItemByItemsKey(cls,prop,key):
        if isinstance(prop, list):
            for i in prop:
                ret = cls.getItemByItemsKey(i,key)
                if ret is not None:
                    return ret
        elif isinstance(prop, dict):
            if "key" in prop and prop["key"] == key:
                return prop
            elif "items" in prop:
                for item in prop["items"]:
                    if "key" in item and item["key"] == key:
                        return item
                    if "items" in item:
                        ret = cls.getItemByItemsKey(item,key)
                        if ret is not None:
                            return ret
        return None


class ItemTypeEditHistory(object):
    """Define API for Itemtype Property creation and manipulation."""

    @classmethod
    def create_or_update(cls, id=0, item_type_id=None, user_id=None,
                         notes={}):
        r"""Create or update ItemTypeEditHistory and store it in the database.

        :param id: ID of Itemtype property.
        :param item_type_id: Existing ItemType model id.
        :param user_id: Existing user format.
        :param notes: map of notes in JSON format.
        :returns: A new :class:`` instance.
        """
        with db.session.begin_nested():
            existing = ItemTypeEditHistoryModel.query \
                .filter_by(id=id).one_or_none()
            new_edit_history = existing or \
                ItemTypeEditHistoryModel(
                    item_type_id=item_type_id,
                    user_id=user_id,
                )

            if new_edit_history.notes != notes:
                new_edit_history.notes = notes
                db.session.add(new_edit_history)
        return new_edit_history

    @classmethod
    def get_by_item_type_id(cls, item_type_id):
        """Retrieve record by id.

        :param item_type_id: ItemType id.
        :returns: ItemTypeEditHistory record or None.
        """
        with db.session.no_autoflush:
            return ItemTypeEditHistoryModel.query \
                .filter_by(item_type_id=item_type_id).one_or_none()


class Mapping(RecordBase):
    """Define API for Mapping creation and manipulation."""

    @classmethod
    def create(cls, item_type_id=None, mapping=None):
        r"""Create a new record instance and store it in the database.

        #. Send a signal :data:`weko_records.signals.before_record_insert`
           with the new record as parameter.

        #. Validate the new record data.

        #. Add the new record in the database.

        #. Send a signal :data:`weko_records.signals.after_record_insert`
           with the new created record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

          * **validator** --
            # A :class:`jsonschema.IValidator` class that will be used to
            validate the record. See
            :func:`~weko_records.api.RecordBase.validate` for more details.


        :param item_type_id: ID of item type.
        :param mapping: Mapping in JSON format.
        :returns: A new :class:`Record` instance.
        """
        with db.session.begin_nested():
            record = cls(mapping)

            before_record_insert.send(
                current_app._get_current_object(),
                record=record
            )

            # record.validate(**kwargs)

            record.model = ItemTypeMapping(item_type_id=item_type_id,
                                           mapping=record)

            db.session.add(record.model)

        after_record_insert.send(
            current_app._get_current_object(),
            record=record
        )
        return record

    @classmethod
    def get_record(cls, item_type_id, with_deleted=False):
        """Retrieve the record by id.

        Raise a database exception if the record does not exist.

        :param item_type_id: ID of item type.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: The :class:`Record` instance.
        """
        with db.session.no_autoflush:
            query = ItemTypeMapping.query.filter_by(item_type_id=item_type_id)
            if not with_deleted:
                query = query.filter(ItemTypeMapping.mapping != None)  # noqa
            obj = query.order_by(desc(ItemTypeMapping.created)).first()
            if obj is None:
                return None
            return cls(obj.mapping, model=obj)

    @classmethod
    def get_records(cls, ids, with_deleted=False):
        """Retrieve multiple records by id.

        :param ids: List of record IDs.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: A list of :class:`Record` instances.
        """
        with db.session.no_autoflush:
            query = ItemTypeMapping.query.filter(ItemTypeMapping.id.in_(ids))
            if not with_deleted:
                query = query.filter(ItemTypeMapping.mapping != None)  # noqa
            return [cls(obj.json, model=obj) for obj in query.all()]

    def patch(self, patch):
        """Patch record metadata.

        :params patch: Dictionary of record metadata.
        :returns: A new :class:`Record` instance.
        """
        data = apply_patch(dict(self), patch)
        return self.__class__(data, model=self.model)

    def commit(self, **kwargs):
        r"""Store changes of the current record instance in the database.

        #. Send a signal :data:`weko_records.signals.before_record_update`
           with the current record to be committed as parameter.

        #. Validate the current record data.

        #. Commit the current record in the database.

        #. Send a signal :data:`weko_records.signals.after_record_update`
            with the committed record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

          * **validator** --
            A :class:`jsonschema.IValidator` class that will be used to
            validate the record. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

        :returns: The :class:`Record` instance.
        """
        if self.model is None or self.model.json is None:
            raise MissingModelError()

        with db.session.begin_nested():
            before_record_update.send(
                current_app._get_current_object(),
                record=self
            )

            self.validate(**kwargs)

            self.model.json = dict(self)
            flag_modified(self.model, 'json')

            db.session.merge(self.model)

        after_record_update.send(
            current_app._get_current_object(),
            record=self
        )
        return self

    def delete(self, force=False):
        """Delete a record.

        If `force` is ``False``, the record is soft-deleted: record data will
        be deleted but the record identifier and the history of the record will
        be kept. This ensures that the same record identifier cannot be used
        twice, and that you can still retrieve its history. If `force` is
        ``True``, then the record is completely deleted from the database.

        #. Send a signal :data:`weko_records.signals.before_record_delete`
           with the current record as parameter.

        #. Delete or soft-delete the current record.

        #. Send a signal :data:`weko_records.signals.after_record_delete`
           with the current deleted record as parameter.

        :param force: if ``True``, completely deletes the current record from
               the database, otherwise soft-deletes it.
        :returns: The deleted :class:`Record` instance.
        """
        if self.model is None:
            raise MissingModelError()

        with db.session.begin_nested():
            before_record_delete.send(
                current_app._get_current_object(),
                record=self
            )

            if force:
                db.session.delete(self.model)
            else:
                self.model.json = None
                db.session.merge(self.model)

        after_record_delete.send(
            current_app._get_current_object(),
            record=self
        )
        return self

    def revert(self, revision_id):
        """Revert the record to a specific revision.

        #. Send a signal :data:`weko_records.signals.before_record_revert`
           with the current record as parameter.

        #. Revert the record to the revision id passed as parameter.

        #. Send a signal :data:`weko_records.signals.after_record_revert`
           with the reverted record as parameter.

        :param revision_id: Specify the record revision id
        :returns: The :class:`Record` instance corresponding to the revision id
        """
        if self.model is None:
            raise MissingModelError()

        revision = self.revisions[revision_id]

        with db.session.begin_nested():
            before_record_revert.send(
                current_app._get_current_object(),
                record=self
            )

            self.model.json = dict(revision)

            db.session.merge(self.model)

        after_record_revert.send(
            current_app._get_current_object(),
            record=self
        )
        return self.__class__(self.model.json, model=self.model)

    @property
    def revisions(self):
        """Get revisions iterator."""
        if self.model is None:
            raise MissingModelError()

        return RevisionsIterator(self.model)

    @classmethod
    def get_mapping_by_item_type_ids(cls, item_type_ids: list) -> list:
        """Get mapping by item type id.

        Args:
            item_type_ids (list): Item type identifier list.

        Returns:
            list: Mappings

        """
        with db.session.no_autoflush:
            query = ItemTypeMapping.query \
                .distinct(ItemTypeMapping.item_type_id) \
                .filter(ItemTypeMapping.item_type_id.in_(item_type_ids)) \
                .order_by(
                    ItemTypeMapping.item_type_id.desc(),
                    ItemTypeMapping.id.desc()
                )

            return [cls(obj.mapping, model=obj) for obj in query.all()]


class JsonldMapping():
    @classmethod
    def create(cls, name, mapping, item_type_id):
        """Create mapping.

        Create new mapping for item type. ID is autoincremented.
        mapping dict is dumped to JSON format.

        Args:
            name (str): Name of the mapping.
            mapping (dict): Mapping in JSON format.
            item_type_id (str): Target itemtype of the mapping.

        Returns:
            ItemTypeJsonldMapping: Created mapping object.

        Raises:
            SQLAlchemyError: An error occurred while creating the mapping.
        """
        obj = ItemTypeJsonldMapping(
            name=name,
            mapping=mapping or {},
            item_type_id=item_type_id,
        )

        try:
            with db.session.begin_nested():
                db.session.add(obj)
            db.session.commit()
        except SQLAlchemyError as ex:
            db.session.rollback()
            raise

        return obj


    @classmethod
    def update(cls, id, name, mapping, item_type_id):
        """Update mapping.

        Update mapping by ID. Specify the value to be updated.
        The verion_id is incremented and the previousmapping moves to
        the history table.

        Args:
            id (int): Mapping ID.
            name (str, optional): Name of the mapping. Not required.
            mapping (dict, optional): Mapping in JSON format. Not required.
            item_type_id (str, optional):
                Target itemtype of the mapping. Not required.

        Returns:
            ItemTypeJsonldMapping: Updated mapping object.

        Raises:
            WekoSwordserverException: When mapping not found.
            SQLAlchemyError: An error occurred while updating the mapping.
        """
        obj = cls.get_mapping_by_id(id)
        if not isinstance(obj, ItemTypeJsonldMapping):
            return None

        obj.name = name
        obj.mapping = mapping or {}
        obj.item_type_id = item_type_id

        try:
            db.session.commit()
        except SQLAlchemyError as ex:
            db.session.rollback()
            raise

        return obj


    @classmethod
    def delete(cls, id):
        """Delete mapping.

        Soft-delete mapping by ID.

        Args:
            id (int): Mapping ID.

        Returns:
            ItemTypeJsonldMapping: Deleted mapping object.
        """
        obj = cls.get_mapping_by_id(id)
        if not isinstance(obj, ItemTypeJsonldMapping):
            return None
        obj.is_deleted = True
        db.session.commit()
        return obj


    @classmethod
    def get_mapping_by_id(cls, id, with_deleted=False):
        """Get mapping by mapping_id.

        Get mapping latest version by mapping_id.
        If include_deleted=False, return None if the mapping is deleted(default).
        Specify include_deleted=True to get the mapping even if it is deleted.

        Args:
            id (int): Mapping ID.
            with_deleted (bool, optional):
                Include deleted mapping. Default is False.

        Returns:
            ItemTypeJsonldMapping:
            Mapping object. If not found or deleted, return `None`.
        """
        query = ItemTypeJsonldMapping.query.filter_by(id=id)
        if not with_deleted:
            query = query.filter_by(is_deleted=False)
        obj = query.first()

        return obj if isinstance(obj, ItemTypeJsonldMapping) else None

    @classmethod
    def get_by_itemtype_id(cls, item_type_id, with_deleted=False):
        """Get mapping by itemtype_id.

        Get mapping latest version by itemtype_id.
        If include_deleted=False, return None if the mapping is deleted(default).
        Specify include_deleted=True to get the mapping even if it is deleted.

        Args:
            item_type_id (int): Itemtype ID.
            include_deleted (bool, optional):
                Include deleted mapping. Default is False.

        Returns:
            list[ItemTypeJsonldMapping]:
            List of mapping objects. If not found or deleted, return empty list.
        """
        query = (
            ItemTypeJsonldMapping.query
            .filter_by(item_type_id=item_type_id)
            .order_by(ItemTypeJsonldMapping.updated.desc())
        )
        if not with_deleted:
            query = query.filter_by(is_deleted=False)

        return [
            mapping for mapping in query.all()
            if isinstance(mapping, ItemTypeJsonldMapping)
        ]

    @classmethod
    def get_all(cls, with_deleted=False):
        """Get all mapping.

        Get all mapping. If include_deleted=False, return only active mapping.
        Specify include_deleted=True to get all mapping including deleted.

        Args:
            include_deleted (bool, optional):
                Include deleted mapping. Default is False.

        Returns:
            list[ItemTypeJsonldMapping]: List of mapping objects.
        """
        query = ItemTypeJsonldMapping.query
        if not with_deleted:
            query = query.filter_by(is_deleted=False)
        return [
            mapping for mapping in query.all()
            if isinstance(mapping, ItemTypeJsonldMapping)
        ]


class ItemTypeProps(RecordBase):
    """Define API for Itemtype Property creation and manipulation."""

    @classmethod
    def create(cls, property_id=None, name=None, schema=None, form_single=None,
               form_array=None):
        """Create a new ItemTypeProperty instance and store it in the database.

        :param property_id: ID of Itemtype property.
        :param name: Property name.
        :param schema: Property in JSON format.
        :param form_single: form (single) in JSON format.
        :param form_array: form (array) in JSON format.
        :returns: A new :class:`Record` instance.
        """
        if not name:
            raise ValueError(
                'The property name is required and cannot be empty.'
            )

        duplicated_prop = ItemTypeProperty.query.filter(
            ItemTypeProperty.name == name,
            ItemTypeProperty.id != property_id
        ).first()
        if duplicated_prop:
            raise ValueError(
                f'The property name "{name}" already exists.'
            )

        with db.session.begin_nested():
            record = cls(schema)

            before_record_insert.send(
                current_app._get_current_object(),
                record=record
            )

            record.model = None
            if property_id > 0:
                obj = ItemTypeProperty.query.filter_by(id=property_id,
                                                       delflg=False).first()
                if obj is not None:
                    obj.name = name
                    obj.schema = schema
                    obj.form = form_single
                    obj.forms = form_array
                    record.model = obj
            if record.model is None:
                record.model = ItemTypeProperty(name=name,
                                                schema=schema,
                                                form=form_single,
                                                forms=form_array)

            db.session.add(record.model)

        after_record_insert.send(
            current_app._get_current_object(),
            record=record
        )
        return record

    @classmethod
    def create_with_property_id(cls, property_id=None, name=None, schema=None,
                                form_single=None, form_array=None):
        """Create a new ItemTypeProperty instance and store it in the database.

        :param property_id: ID of Itemtype property.
        :param name: Property name.
        :param schema: Property in JSON format.
        :param form_single: form (single) in JSON format.
        :param form_array: form (array) in JSON format.
        :returns: A new :class:`Record` instance.
        """
        if not name:
            raise ValueError(
                'The property name is required and cannot be empty.'
            )

        duplicated_prop = ItemTypeProperty.query.filter(
            ItemTypeProperty.name == name,
            ItemTypeProperty.id != property_id
        ).first()
        if duplicated_prop:
            raise ValueError(
                f'The property name "{name}" already exists.'
            )

        with db.session.begin_nested():
            record = cls(schema)

            before_record_insert.send(
                current_app._get_current_object(),
                record=record
            )

            record.model = ItemTypeProperty(name=name,
                                            schema=schema,
                                            form=form_single,
                                            forms=form_array,
                                            id=property_id)
            db.session.add(record.model)

        after_record_insert.send(
            current_app._get_current_object(),
            record=record
        )
        return record

    @classmethod
    def get_record(cls, property_id):
        """Retrieve the record by id.

        Raise a database exception if the record does not exist.

        :param property_id: ID of item type property.
        :returns: The :class:`Record` instance.
        """
        with db.session.no_autoflush:
            obj = ItemTypeProperty.query.filter_by(id=property_id,
                                                   delflg=False).first()
            if obj is None:
                return None
            cls.helper_remove_empty_required(obj.schema)
            return obj

    @classmethod
    def helper_remove_empty_required(cls, data):
        """Help to remove required key if it is empty.

        Arguments:
            data {dict} -- schema to remove required key

        """
        if "required" in data and not data.get("required"):
            data.pop("required", None)
        if "properties" in data:
            for k, v in data.get("properties").items():
                if v.get("items"):
                    cls.helper_remove_empty_required(v.get("items"))

    @classmethod
    def get_records(cls, ids):
        """Retrieve multiple records by id.

        :param ids: List of record IDs.
        :returns: A list of :class:`Record` instances.
        """
        with db.session.no_autoflush:
            query = None
            if len(ids) > 0:
                query = ItemTypeProperty.query.filter_by(
                    ItemTypeMapping.id.in_(ids))
                query = query.filter_by(delflg=False)  # noqa
            else:
                query = ItemTypeProperty.query.filter_by(delflg=False)

            return query.all()

    @property
    def revisions(self):
        """Get revisions iterator."""
        if self.model is None:
            raise MissingModelError()

        return RevisionsIterator(self.model)


class ItemsMetadata(RecordBase):
    """Define API for ItemsMetadata creation and manipulation."""

    @classmethod
    def create(cls, data, id_=None, **kwargs):
        r"""Create a new record instance and store it in the database.

        #. Send a signal :data:`weko_records.signals.before_record_insert`
           with the new record as parameter.

        #. Validate the new record data.

        #. Add the new record in the database.

        #. Send a signal :data:`weko_records.signals.after_record_insert`
           with the new created record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

          * **validator** --
            A :class:`jsonschema.IValidator` class that will be used to
            validate the record. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

        :param data: Dict with the record metadata.
        :param id_: Specify a UUID to use for the new record, instead of
                    automatically generated.
        :returns: A new :class:`Record` instance.
        """
        with db.session.begin_nested():
            record = cls(data)

            before_record_insert.send(
                current_app._get_current_object(),
                record=record
            )

            # record.validate(**kwargs)

            record.model = ItemMetadata(
                id=id_,
                item_type_id=kwargs.get('item_type_id'),
                json=record
            )

            db.session.add(record.model)

        after_record_insert.send(
            current_app._get_current_object(),
            record=record
        )
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
            query = ItemMetadata.query.filter_by(id=id_)
            if not with_deleted:
                query = query.filter(ItemMetadata.json != None)  # noqa
            obj = query.one()
            cls.__custom_item_metadata(obj.json)
            return cls(obj.json, model=obj)

    @classmethod
    def __custom_item_metadata(cls, item_metadata: dict):
        """Custom item metadata.

        Args:
            item_metadata (dict): Item metadata.
        """
        for k, v in item_metadata.items():
            if isinstance(v, (list, dict)):
                cls.__replace_fqdn_of_file_metadata(v)

    @classmethod
    def __replace_fqdn_of_file_metadata(cls, item_metadata: Union[list, dict]):
        """Replace FQDN of file metadata.

        Args:
            item_metadata (Union[list, dict]): Item metadata.
        """
        from .utils import replace_fqdn
        if isinstance(item_metadata, dict) and \
            item_metadata.get('version_id') and \
                item_metadata.get('url', {}).get('url'):
            item_metadata['url']['url'] = replace_fqdn(
                item_metadata['url']['url'])
        elif isinstance(item_metadata, list):
            for metadata in item_metadata:
                cls.__replace_fqdn_of_file_metadata(metadata)

    @classmethod
    def get_records(cls, ids, with_deleted=False):
        """Retrieve multiple records by id.

        :param ids: List of record IDs.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: A list of :class:`Record` instances.
        """
        with db.session.no_autoflush:
            query = ItemMetadata.query.filter(ItemMetadata.id.in_(ids))
            if not with_deleted:
                query = query.filter(ItemMetadata.json != None)  # noqa

            return [cls(obj.json, model=obj) for obj in query.all()]

    @classmethod
    def get_by_item_type_id(cls, item_type_id, with_deleted=False):
        """Retrieve multiple records by item types identifier.

        :param item_type_id: Identifier of item type.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: A list of :class:`Record` instance.
        """
        with db.session.no_autoflush:
            query = ItemMetadata.query.filter_by(item_type_id=item_type_id)
            if not with_deleted:
                query = query.filter(ItemMetadata.json != None)  # noqa
            return query.all()

    @classmethod
    def get_registered_item_metadata(cls, item_type_id):
        """Retrieve multiple records by item types identifier.

        :param item_type_id: Identifier of item type.
        :returns: A list of :class:`Record` instance.
        """
        with db.session.no_autoflush:
            # Get all item metadata registered by item_type_id
            items = ItemMetadata.query.filter_by(item_type_id=item_type_id).all()
            item_metadata_array = [str(item.id) for item in items]
            # Get all persistent identifier which are not deleted.
            persistent_identifier = PersistentIdentifier.query.filter(
                PersistentIdentifier.object_uuid.in_(item_metadata_array),
                PersistentIdentifier.pid_type == 'recid',
                PersistentIdentifier.status == PIDStatus.REGISTERED
            ).all()
            return persistent_identifier

    @classmethod
    def get_by_object_id(cls, object_id):
        """Retrieve ItemMetadata data by item identifier.

        :param object_id: Pidstore Identifier of item.
        :returns: A :class:`Record` instance.
        """
        with db.session.no_autoflush:
            query = ItemMetadata.query.filter_by(id=object_id)

            return query.one_or_none()

    def patch(self, patch):
        """Patch record metadata.

        :params patch: Dictionary of record metadata.
        :returns: A new :class:`Record` instance.
        """
        data = apply_patch(dict(self), patch)
        return self.__class__(data, model=self.model)

    def commit(self, **kwargs):
        r"""Store changes of the current record instance in the database.

        #. Send a signal :data:`weko_records.signals.before_record_update`
           with the current record to be committed as parameter.

        #. Validate the current record data.

        #. Commit the current record in the database.

        #. Send a signal :data:`weko_records.signals.after_record_update`
            with the committed record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

          * **validator** --
            A :class:`jsonschema.IValidator` class that will be used to
            validate the record. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

        :returns: The :class:`Record` instance.
        """
        if self.model is None or self.model.json is None:
            raise MissingModelError()

        with db.session.begin_nested():
            before_record_update.send(
                current_app._get_current_object(),
                record=self
            )

            # self.validate(**kwargs)

            self.model.json = dict(self)
            flag_modified(self.model, 'json')

            db.session.merge(self.model)

        after_record_update.send(
            current_app._get_current_object(),
            record=self
        )
        return self

    def delete(self, force=False):
        """Delete a record.

        If `force` is ``False``, the record is soft-deleted: record data will
        be deleted but the record identifier and the history of the record will
        be kept. This ensures that the same record identifier cannot be used
        twice, and that you can still retrieve its history. If `force` is
        ``True``, then the record is completely deleted from the database.

        #. Send a signal :data:`weko_records.signals.before_record_delete`
           with the current record as parameter.

        #. Delete or soft-delete the current record.

        #. Send a signal :data:`weko_records.signals.after_record_delete`
           with the current deleted record as parameter.

        :param force: if ``True``, completely deletes the current record from
               the database, otherwise soft-deletes it.
        :returns: The deleted :class:`Record` instance.
        """
        if self.model is None:
            raise MissingModelError()

        with db.session.begin_nested():
            before_record_delete.send(
                current_app._get_current_object(),
                record=self
            )

            if force:
                db.session.delete(self.model)
            else:
                self.model.json = None
                db.session.merge(self.model)

        after_record_delete.send(
            current_app._get_current_object(),
            record=self
        )
        return self

    def revert(self, revision_id):
        """Revert the record to a specific revision.

        #. Send a signal :data:`weko_records.signals.before_record_revert`
           with the current record as parameter.

        #. Revert the record to the revision id passed as parameter.

        #. Send a signal :data:`weko_records.signals.after_record_revert`
           with the reverted record as parameter.

        :param revision_id: Specify the record revision id
        :returns: The :class:`Record` instance corresponding to the revision id
        """
        if self.model is None:
            raise MissingModelError()

        revision = self.revisions[revision_id]

        with db.session.begin_nested():
            before_record_revert.send(
                current_app._get_current_object(),
                record=self
            )

            self.model.json = dict(revision)

            db.session.merge(self.model)

        after_record_revert.send(
            current_app._get_current_object(),
            record=self
        )
        return self.__class__(self.model.json, model=self.model)

    @property
    def revisions(self):
        """Get revisions iterator."""
        if self.model is None:
            raise MissingModelError()

        return RevisionsIterator(self.model)


class FilesMetadata(RecordBase):
    """Define API for FilesMetadata creation and manipulation."""

    @classmethod
    def create(cls, data, id_=None, **kwargs):
        r"""Create a new record instance and store it in the database.

        #. Send a signal :data:`weko_records.signals.before_record_insert`
           with the new record as parameter.

        #. Validate the new record data.

        #. Add the new record in the database.

        #. Send a signal :data:`weko_records.signals.after_record_insert`
           with the new created record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

          * **validator** --
            A :class:`jsonschema.IValidator` class that will be used to
            validate the record. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

        :param data: Dict with the record metadata.
        :param id_: Specify a UUID to use for the new record, instead of
                    automatically generated.
        :returns: A new :class:`Record` instance.
        """
        with db.session.begin_nested():
            record = cls(data)

            # before_record_insert.send(
            #     current_app._get_current_object(),
            #     record=record
            # )

            # record.validate(**kwargs)

            record.model = FileMetadata(
                pid=kwargs.get('pid'),
                json=record, contents=kwargs.get('con'))

            db.session.add(record.model)

        # after_record_insert.send(
        #     current_app._get_current_object(),
        #     record=record
        # )
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
            query = FileMetadata.query.filter_by(pid=id_)
            if not with_deleted:
                query = query.filter(FileMetadata.contents != None)  # noqa
            obj = query.one()
            return cls(obj.json, model=obj)

    @classmethod
    def get_records(cls, ids, with_deleted=False):
        """Retrieve multiple records by id.

        :param ids: List of record IDs.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: A list of :class:`Record` instances.
        """
        with db.session.no_autoflush:
            query = FileMetadata.query.filter_by(pid=ids)
            if not with_deleted:
                query = query.filter(FileMetadata.contents != None)  # noqa

            return [cls(obj.json, model=obj) for obj in query.all()]

    def patch(self, patch):
        """Patch record metadata.

        :params patch: Dictionary of record metadata.
        :returns: A new :class:`Record` instance.
        """
        data = apply_patch(dict(self), patch)
        return self.__class__(data, model=self.model)

    def update_data(id, jsn):
        """Patch record metadata.

        :params patch: Dictionary of record metadata.
        :returns: A new :class:`Record` instance.
        """
        from sqlalchemy import update
        with db.session.begin_nested():
            stmt = update(FileMetadata).where(
                FileMetadata.id == id).values(json=jsn)
            db.session.execute(stmt)

    def commit(self, **kwargs):
        r"""Store changes of the current record instance in the database.

        #. Send a signal :data:`weko_records.signals.before_record_update`
           with the current record to be committed as parameter.

        #. Validate the current record data.

        #. Commit the current record in the database.

        #. Send a signal :data:`weko_records.signals.after_record_update`
            with the committed record as parameter.

        :Keyword Arguments:
          * **format_checker** --
            An instance of the class :class:`jsonschema.FormatChecker`, which
            contains validation rules for formats. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

          * **validator** --
            A :class:`jsonschema.IValidator` class that will be used to
            validate the record. See
            :func:`~weko_records.api.RecordBase.validate` for more details.

        :returns: The :class:`Record` instance.
        """
        if self.model is None or self.model.json is None:
            raise MissingModelError()

        with db.session.begin_nested():
            before_record_update.send(
                current_app._get_current_object(),
                record=self
            )

            self.validate(**kwargs)

            self.model.json = dict(self)
            flag_modified(self.model, 'json')

            db.session.merge(self.model)

        after_record_update.send(
            current_app._get_current_object(),
            record=self
        )
        return self

    def delete(self, force=False):
        """Delete a record.

        If `force` is ``False``, the record is soft-deleted: record data will
        be deleted but the record identifier and the history of the record will
        be kept. This ensures that the same record identifier cannot be used
        twice, and that you can still retrieve its history. If `force` is
        ``True``, then the record is completely deleted from the database.

        #. Send a signal :data:`weko_records.signals.before_record_delete`
           with the current record as parameter.

        #. Delete or soft-delete the current record.

        #. Send a signal :data:`weko_records.signals.after_record_delete`
           with the current deleted record as parameter.

        :param force: if ``True``, completely deletes the current record from
               the database, otherwise soft-deletes it.
        :returns: The deleted :class:`Record` instance.
        """
        if self.model is None:
            raise MissingModelError()

        with db.session.begin_nested():
            before_record_delete.send(
                current_app._get_current_object(),
                record=self
            )

            if force:
                db.session.delete(self.model)
            else:
                self.model.json = None
                db.session.merge(self.model)

        after_record_delete.send(
            current_app._get_current_object(),
            record=self
        )
        return self

    def revert(self, revision_id):
        """Revert the record to a specific revision.

        #. Send a signal :data:`weko_records.signals.before_record_revert`
           with the current record as parameter.

        #. Revert the record to the revision id passed as parameter.

        #. Send a signal :data:`weko_records.signals.after_record_revert`
           with the reverted record as parameter.

        :param revision_id: Specify the record revision id
        :returns: The :class:`Record` instance corresponding to the revision id
        """
        if self.model is None:
            raise MissingModelError()

        revision = self.revisions[revision_id]

        with db.session.begin_nested():
            before_record_revert.send(
                current_app._get_current_object(),
                record=self
            )

            self.model.json = dict(revision)

            db.session.merge(self.model)

        after_record_revert.send(
            current_app._get_current_object(),
            record=self
        )
        return self.__class__(self.model.json, model=self.model)

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
        super(RecordRevision, self).__init__(model.json, model=model)


class SiteLicense(RecordBase):
    """Define API for SiteLicense creation and manipulation."""

    @classmethod
    def get_records(cls, user=None):
        """Retrieve multiple records.

        :returns: A list of :class:`Record` instances.
        """
        from invenio_communities.models import Community
        with db.session.no_autoflush:
            if not user:
                sl_obj = SiteLicenseInfo.query.order_by(
                    SiteLicenseInfo.organization_id).all()
            else:
                if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in user.roles):
                    sl_obj = SiteLicenseInfo.query.order_by(
                        SiteLicenseInfo.organization_id).all()
                else:
                    repositories = Community.get_repositories_by_user(user)
                    repository_ids = [repository.id for repository in repositories]
                    sl_obj = SiteLicenseInfo.query.filter(SiteLicenseInfo.repository_id.in_(repository_ids)).order_by(
                        SiteLicenseInfo.organization_id).all()
            return [cls(dict(obj)) for obj in sl_obj]

    @classmethod
    def update(cls, obj):
        """Update method."""
        def get_repository_ids():
            """Get repository ID based on user's roles."""
            from flask_login import current_user
            from invenio_communities.models import Community
            if any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles):
                return ["Root Index"]
            repositories = Community.get_repositories_by_user(current_user)
            if repositories:
                return [repository.id for repository in repositories]
            raise Exception("No repository found for the user")

        def get_existing_entries(repository_ids):
            """Get existing site license entries for the repository."""
            if "Root Index" in repository_ids:
                return {info.organization_name: info for info in SiteLicenseInfo.query.all()}
            return {info.organization_name: info for info in SiteLicenseInfo.query.filter(SiteLicenseInfo.repository_id.in_(repository_ids)).all()}

        def get_addr(lst, organization_id):
            """Convert address list to SiteLicenseIpAddress instances."""
            if not lst or not isinstance(lst, list):
                return []

            return [
                SiteLicenseIpAddress(
                    organization_id=organization_id,
                    organization_no=j + 1,
                    start_ip_address='.'.join(item.get('start_ip_address')),
                    finish_ip_address='.'.join(item.get('finish_ip_address'))
                )
                for j, item in enumerate(lst)
            ]
        # update has_site_license field on item type name tbl
        ItemTypeNames.update(obj.get('item_type'))
        repository_ids = get_repository_ids()

        site_license = obj.get('site_license')
        if not isinstance(site_license, list):
            return

        existing_entries = get_existing_entries(repository_ids)
        new_entries = {}

        for lst in site_license:
            org_name = lst.get('organization_name')
            receive_mail_flag = lst.get('receive_mail_flag', 'F') if lst.get('mail_address') else 'F'

            if org_name in existing_entries:
                # Update existing entry
                slif = existing_entries[org_name]
                slif.receive_mail_flag = receive_mail_flag
                slif.mail_address = lst.get('mail_address')
                slif.domain_name = lst.get('domain_name')

                # Update addresses
                for addr in slif.addresses:
                    db.session.delete(addr)
                new_addresses = get_addr(lst.get('addresses'), slif.organization_id)
                slif.addresses = new_addresses

                new_entries[org_name] = slif
            else:
                # Create new entry
                slif = SiteLicenseInfo(
                    organization_name=org_name,
                    receive_mail_flag=receive_mail_flag,
                    mail_address=lst.get('mail_address'),
                    domain_name=lst.get('domain_name'),
                    repository_id=lst.get('repository_id') if lst.get('repository_id') else repository_ids[0]
                )
                slif.addresses = get_addr(lst.get('addresses'), slif.organization_id)
                new_entries[org_name] = slif
                db.session.add(slif)

        # Remove obsolete entries
        obsolete_entries = set(existing_entries.keys()) - set(new_entries.keys())
        for org_name in obsolete_entries:
            target = existing_entries[org_name]
            for addr in target.addresses:
                db.session.delete(addr)
            db.session.delete(target)


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

    def next(self):
        """Python 2.7 compatibility."""
        return self.__next__()  # pragma: no cover

    def __next__(self):
        """Get next revision item."""
        return RecordRevision(next(self._it))

    def __getitem__(self, revision_id):
        """Get a specific revision.

        :param revision_id: Specify the record revision id
        """
        return RecordRevision(self.model.versions[revision_id])

    def __contains__(self, revision_id):
        """Test if revision exists.

        :param revision_id: Specify the record revision id
        """
        try:
            self[revision_id]
            return True
        except IndexError:
            return False


class WekoRecord(Record):
    """Weko Record."""

    record_fetcher = staticmethod(weko_record_fetcher)

    @classmethod
    def get_record(cls, pid, id_, with_deleted=False):
        """Retrieve the record by id.

        Raise a database exception if the record does not exist.

        :param id_: record ID.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: The :class:`Record` instance.
        """
        pr = super(WekoRecord, cls).get_record(id_)

        with db.session.no_autoflush:
            query = FileMetadata.query.filter_by(pid=pid)
            if not with_deleted:
                query = query.filter(FileMetadata.contents != None)  # noqa

            return [cls(obj.json, model=obj) for obj in query.all()]

    @property
    def pid(self):
        """Return an instance of record PID."""
        pid = self.record_fetcher(self.id, self)
        return PersistentIdentifier.get(pid.pid_type, pid.pid_value)

    @property
    def depid(self):
        """Return depid of the record."""
        return PersistentIdentifier.get(
            pid_type='depid',
            pid_value=self.get('_deposit', {}).get('id')
        )


class FeedbackMailList(object):
    """Feedback-Mail List API."""

    @classmethod
    def update(cls, item_id, feedback_maillist):
        """Create a new instance feedback_mail_list.

        :param item_id: Item Identifier
        :param feedback_maillist: list mail feedback
        :return boolean: True if success
        """
        from invenio_communities.utils import get_repository_id_by_item_id
        with db.session.begin_nested():
            query_object = _FeedbackMailList.query.filter_by(
                item_id=item_id).one_or_none()
            if not query_object:
                mail_list = []
                account_author_set = set()
                for d in feedback_maillist:
                    author_id = d.get("author_id")
                    email = d.get("email")
                    if author_id:
                        account_author_set.add(str(author_id))
                    elif email:
                        mail_list.append({"email": email})
                query_object = _FeedbackMailList(
                    item_id=item_id,
                    mail_list=mail_list,
                    account_author=",".join(list(account_author_set)),
                    repository_id=get_repository_id_by_item_id(item_id)
                )
                db.session.add(query_object)
            else:
                mail_list = []
                account_author_set = set()
                for d in feedback_maillist:
                    author_id = d.get("author_id")
                    email = d.get("email")
                    if author_id:
                        account_author_set.add(str(author_id))
                    elif email:
                        mail_list.append({"email": email})
                query_object.mail_list = mail_list
                query_object.account_author = ",".join(list(account_author_set))
                db.session.merge(query_object)

    @classmethod
    def update_by_list_item_id(cls, item_ids, feedback_maillist):
        """Create a new instance feedback_mail_list.

        :param item_ids: Item Identifiers
        :param feedback_maillist: list mail feedback
        """
        for item_id in item_ids:
            cls.update(item_id, feedback_maillist)

    @classmethod
    def get_mail_list_by_item_id(cls, item_id):
        """Get a FeedbackMail list by item_id.

        :param item_id:
        :return feedback_mail_list

        """
        try:
            with db.session.no_autoflush:
                query_object = _FeedbackMailList.query.filter_by(
                    item_id=item_id).one_or_none()
                if query_object:
                    data = []
                    list_author_id = []
                    if query_object.account_author:
                        list_author_id = query_object.account_author.split(',')
                        for author_id in list_author_id:
                            emails = Authors.get_emails_by_id(author_id)
                            for e in emails:
                                data.append({"email": e, "author_id": author_id})
                    if query_object.mail_list:
                        for m in query_object.mail_list:
                            author_id = m.get("author_id")
                            email = m.get("email")
                            if author_id: # if there is author_id (obsolete data formats only)
                                if author_id not in list_author_id:
                                    emails = Authors.get_emails_by_id(author_id)
                                    for e in emails:
                                        data.append({"email": e, "author_id": author_id})
                            else:
                                if email:
                                    data.append({"email": email, "author_id": ""})
                    return data
                else:
                    return []
        except SQLAlchemyError as e:
            current_app.logger.error(e)
            return []

    @classmethod
    def get_feedback_mail_list(cls, repo_id=None):
        """Get feedback mail list for send mail."""
        mail_list = {}
        checked_author_id = {}

        # get feedbak mail list from db
        data = db.session.query(
            _FeedbackMailList, PersistentIdentifier
        ).join(
            PersistentIdentifier,
            _FeedbackMailList.item_id == PersistentIdentifier.object_uuid
        ).filter(
            PersistentIdentifier.pid_type == 'recid',
            PersistentIdentifier.status == PIDStatus.REGISTERED,
            PersistentIdentifier.pid_value.notlike("%.%")
        )

        if repo_id:
            data = data.filter(_FeedbackMailList.repository_id == repo_id)
        data = data.all()

        # create return data
        for d in data:
            item_id = str(d.FeedbackMailList.item_id)
            emails_no_authorid = []
            list_author_id = d.FeedbackMailList.account_author.split(',')
            for m in d.FeedbackMailList.mail_list:
                if m.get("author_id"):
                    list_author_id.append(m.get("author_id"))
                else:
                    emails_no_authorid.append(m.get("email"))
            # there is author id
            for author_id in list(set(list_author_id)):
                if not author_id:
                    continue
                if author_id in checked_author_id:
                    emails = checked_author_id.get(author_id)
                    for e in emails:
                        mail_list[e]["items"].append(item_id)
                else:
                    emails = Authors.get_emails_by_id(author_id)
                    for e in emails:
                        if e and e not in mail_list:
                            mail_list[e] = {
                                "items": [item_id],
                                "author_id": author_id
                            }
                    checked_author_id[author_id] = emails
            # if no author id
            for e in emails_no_authorid:
                if e:
                    if e not in mail_list:
                        mail_list[e] = {
                            "items": [item_id],
                            "author_id": ""
                        }
                    else:
                        mail_list[e]["items"].append(item_id)

        return mail_list

    @classmethod
    def delete(cls, item_id):
        """Delete a feedback_mail_list by item_id.

        :param item_id: item_id of target feed_back_mail_list
        :return: bool: True if success
        """
        try:
            cls.delete_without_commit(item_id)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return False
        return True

    @classmethod
    def delete_without_commit(cls, item_id):
        """Delete a feedback_mail_list by item_id without commit.

        :param item_id: item_id of target feed_back_mail_list
        :return: bool: True if success
        """
        with db.session.begin_nested():
            _FeedbackMailList.query.filter_by(item_id=item_id).delete()

    @classmethod
    def delete_by_list_item_id(cls, item_ids):
        """Delete a feedback_mail_list by item_id.

        :param item_ids: item_id of target feed_back_mail_list
        """
        for item_id in item_ids:
            cls.delete(item_id)


class RequestMailList(object):
    """Request-Mail List API."""

    @classmethod
    def update(cls, item_id, request_maillist):
        """Create a new instance request_mail_list.

        :param item_id: Item Identifier
        :param request_maillist: list of request mail
        :return boolean: True if success
        """
        try:
            with db.session.begin_nested():
                query_object = _RequestMailList.query.filter_by(
                    item_id=item_id).one_or_none()
                if not query_object:
                    query_object = _RequestMailList(
                        item_id=item_id,
                        mail_list=request_maillist
                    )
                    db.session.add(query_object)
                else:
                    query_object.mail_list = request_maillist
                    db.session.merge(query_object)

        except SQLAlchemyError:
            db.session.rollback()
            return False
        return True

    @classmethod
    def update_by_list_item_id(cls, item_ids, request_maillist):
        """Create a new instance reqeust_mail_list.

        :param item_ids: Item Identifiers
        :param request_maillist: Request mail list
        """
        for item_id in item_ids:
            cls.update(item_id, request_maillist)

    @classmethod
    def get_mail_list_by_item_id(cls, item_id):
        """Get a RequestMail list by item_id.

        :param item_id:
        :return request_mail_list

        """
        try:
            with db.session.no_autoflush:
                query_object = _RequestMailList.query.filter_by(
                    item_id=item_id).one_or_none()
                if query_object and query_object.mail_list:
                    return query_object.mail_list
                else:
                    return []
        except SQLAlchemyError:
            return []

    @classmethod
    def get_request_mail_by_mailaddress(cls, address):
        """Get a RequestMail list by mailaddress
        :param address: str, mailaddress
        :return request_mail_list
        """
        try:
            with db.session.no_autoflush:
                query_object = _RequestMailList.query.filter(
                    cast(_RequestMailList.mail_list, String).contains('"'+address+'"')).all()
                if query_object:
                    return query_object
                else:
                    return []
        except SQLAlchemyError:
            return []

    @classmethod
    def delete(cls, item_id):
        """Delete a request_mail_list by item_id.

        :param item_id: item_id of target request_mail_list
        :return: bool: True if success
        """
        try:
            cls.delete_without_commit(item_id)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return False
        return True

    @classmethod
    def delete_without_commit(cls, item_id):
        """Delete a request_mail_list by item_id without commit.

        :param item_id: item_id of target request_mail_list
        :return: bool: True if success
        """
        with db.session.begin_nested():
            _RequestMailList.query.filter_by(item_id=item_id).delete()

    @classmethod
    def delete_by_list_item_id(cls, item_ids):
        """Delete a request_mail_list by item_id.

        :param item_ids: item_id of target request_mail_list
        """
        for item_id in item_ids:
            cls.delete(item_id)

class ItemApplication(object):

    @classmethod
    def update(cls, item_id, item_application):
        try:
            with db.session.begin_nested():
                query_object = _ItemApplication.query.filter_by(
                    item_id=item_id).one_or_none()
                if not query_object:
                    query_object = _ItemApplication(
                        item_id=item_id,
                        item_application=item_application
                    )
                    db.session.add(query_object)
                else:
                    query_object.item_application = item_application
                    db.session.merge(query_object)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return False
        return True

    @classmethod
    def update_by_list_item_id(cls, item_ids, item_application):
        for item_id in item_ids:
            cls.update(item_id, item_application)

    @classmethod
    def get_item_application_by_item_id(cls, item_id):
        try:
            with db.session.no_autoflush:
                query_object = _ItemApplication.query.filter_by(
                    item_id=item_id).one_or_none()
                if query_object and query_object.item_application:
                    return query_object.item_application
                else:
                    return {}
        except SQLAlchemyError:
            return {}

    @classmethod
    def delete(cls, item_id):
        try:
            cls.delete_without_commit(item_id)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            return False
        return True

    @classmethod
    def delete_without_commit(cls, item_id):
        with db.session.begin_nested():
            _ItemApplication.query.filter_by(item_id=item_id).delete()

    @classmethod
    def delete_by_list_item_id(cls, item_ids):
        for item_id in item_ids:
            cls.delete(item_id)

class ItemLink(object):
    """Item Link API."""

    org_item_id = 0

    def __init__(self, recid: str):
        """Constructor."""
        self.org_item_id = recid

    @classmethod
    def get_item_link_info(cls, recid):
        """Get item link info of recid.

        Args:
            recid (str): Record Identifier.

        Returns:
            list(dict): Destination records info.
                - item_links: Destination item PID
                - item_title: Title of the destination item
                - value: Reference type
        """
        from weko_deposit.api import WekoRecord

        dst_relations = ItemReference.get_src_references(recid).all()
        ret = []

        for relation in dst_relations:
            record = WekoRecord.get_record_by_pid(relation.dst_item_pid)
            ret.append(dict(
                item_links=relation.dst_item_pid,
                item_title=record.get('item_title'),
                value=relation.reference_type
            ))

        return ret

    @staticmethod
    def __get_titles_key(item_type_mapping):
        """Get title keys in item type mapping.

        :param item_type_mapping: item type mapping.
        :return:
        """
        parent_key = None
        title_key = None
        language_key = None
        for mapping_key in item_type_mapping:
            property_data = item_type_mapping.get(mapping_key).get(
                'jpcoar_mapping')
            if (
                isinstance(property_data, dict)
                and property_data.get('title')
            ):
                title = property_data.get('title')
                parent_key = mapping_key
                title_key = title.get("@value")
                language_key = title.get("@attributes", {}).get("xml:lang")
        return parent_key, title_key, language_key

    @classmethod
    def __get_titles(cls, record):
        """Get titles of record.

        :param record:
        :return:
        """
        item_type_mapping = Mapping.get_record(record.get("item_type_id"))
        parent_key, title_key, language_key = cls.__get_titles_key(
            item_type_mapping)
        title_metadata = record.get(parent_key)
        titles = []
        if title_metadata:
            attribute_value = title_metadata.get('attribute_value_mlt')
            if isinstance(attribute_value, list):
                for attribute in attribute_value:
                    tmp = dict()
                    if attribute.get(title_key):
                        tmp['title'] = attribute.get(title_key)
                    if attribute.get(language_key):
                        tmp['language'] = attribute.get(language_key)
                    if tmp.get('title'):
                        titles.append(tmp.copy())
        return titles

    @classmethod
    def get_item_link_info_output_xml(cls, recid):
        """Get item link info of recid for output xml.

        :param recid: Record Identifier.
        :return ret: List destination records.
        """
        from weko_deposit.api import WekoRecord
        from weko_records_ui.utils import get_record_permalink

        def get_url(pid_value):
            wr = WekoRecord.get_record_by_pid(pid_value)
            permalink = get_record_permalink(wr)
            if not permalink:
                sid = 'system_identifier_doi'
                avm = 'attribute_value_mlt'
                ssi = 'subitem_systemidt_identifier'
                if wr.get(sid) and wr.get(sid).get(avm)[0]:
                    url = wr[sid][avm][0][ssi]
                else:
                    url = request.host_url + 'records/' + pid_value
            else:
                url = permalink

            if 'doi' in url:
                type = 'DOI'
            elif 'handle' in url:
                type = 'HDL'
            else:
                type = 'URI'
            return url, type

        dst_relations = ItemReference.get_src_references(recid).all()
        ret = []

        for relation in dst_relations:
            link, identifierType = get_url(relation.dst_item_pid)
            ret.append(dict(
                reference_type=relation.reference_type,
                url=link,
                identifierType=identifierType
            ))

        return ret

    def update(self, items, require_commit=True):
        """Update list item link of current record.

        This method updates the relationships between the current item
        (self.org_item_id) and a list of destination items (items).
        It handles creation, updating, and deletionof relationships,
        including special logic for supplement relationships.

        Args:
            items(list): List of dictionaries containing
                'item_id' and 'sele_id' (relationship type).
            require_commit (bool):
                If True, commit the transaction after processing.
        Returns:
            str: Error message if any, otherwise None.
        """
        from weko_logging.activity_logger import UserActivityLogger
        from weko_records_ui.utils import get_latest_version

        src_without_ver = self.org_item_id.split('.')[0]
        # Fetch all existing relationships where the current item is src
        dst_relations = ItemReference.get_src_references(self.org_item_id).all()
        # Fetch all existing relationships where the current item is dst
        src_relations = ItemReference.get_dst_references(src_without_ver).all()

        src_fixed_relations = {rel.dst_item_pid: rel for rel in dst_relations}
        dst_fixed_relations = {rel.src_item_pid: rel for rel in src_relations}
        # Initialize lists to track changes:
        # created: new items to be added
        # updated: items whose relationship type has changed
        # deleted: items to be deleted
        created = []
        updated = []
        deleted = []
        supplement_key = current_app.config["WEKO_RECORDS_REFERENCE_SUPPLEMENT"]
        # Iterate through each item in the input list
        is_src_integer = (self.org_item_id == src_without_ver)
        for item in items:
            item_id = str(item['item_id'])
            if item_id and not item_id.isdecimal():
                continue
            sele_id = item['sele_id']

            relation = {
                'src_item_pid': self.org_item_id,
                'dst_item_pid': item_id,
                'sele_id': sele_id
            }
            if item_id in src_fixed_relations:
                dst_item = src_fixed_relations.pop(item_id)
                if sele_id != dst_item.reference_type:
                    updated.append(relation)
            else:
                created.append(relation)

            # inverse link
            if is_src_integer:
                draft_pid = PersistentIdentifier.query.filter_by(
                    pid_type='recid',
                    pid_value=f"{item_id}.0"
                ).one_or_none()
                inv_src_ids = [item_id, get_latest_version(item_id)] + (
                    [draft_pid.pid_value] if draft_pid else []
                )
                if sele_id in supplement_key:
                    opposite_index = 0 if sele_id == supplement_key[1] else 1
                    inv_relation = supplement_key[opposite_index]
                    for inv_src_id in inv_src_ids:
                        relation = {
                            'src_item_pid': inv_src_id,
                            'dst_item_pid': src_without_ver,
                            'sele_id': inv_relation
                        }
                        if inv_src_id in dst_fixed_relations:
                            if (inv_relation !=
                                dst_fixed_relations[inv_src_id].reference_type):
                                updated.append(relation)
                        else:
                            created.append(relation)
                else:
                    deleted.extend([
                        {
                            'src_item_pid': inv_src_id,
                            'dst_item_pid': src_without_ver
                        }
                        for inv_src_id in inv_src_ids
                        if (
                            inv_src_id in dst_fixed_relations and
                            dst_fixed_relations[inv_src_id].reference_type
                            in supplement_key
                        )
                    ])

        # delete
        for deleted_dst, deleted_link in src_fixed_relations.items():
            deleted.append({
                'src_item_pid': self.org_item_id,
                'dst_item_pid': deleted_dst
            })
            sele_id = deleted_link.reference_type
            if sele_id in supplement_key and is_src_integer:
                inv_src_ids = [
                    deleted_dst,
                    f"{deleted_dst}.0",
                    get_latest_version(deleted_dst)
                ]
                deleted.extend([
                    {
                        'src_item_pid': inv_src_id,
                        'dst_item_pid': src_without_ver,
                    }
                    for inv_src_id in inv_src_ids
                        if inv_src_id in dst_fixed_relations
                ])

        try:
            # Perform all database operations within a nested transaction
            with db.session.begin_nested():
                # Delete relationships for removed items
                if deleted:
                    self.bulk_delete(deleted)
                # Update existing relationships
                if updated:
                    self.bulk_update(updated)
                # Create new relationships
                if created:
                    self.bulk_create(created)

            if require_commit:
                # Commit the transaction if all operations succeed
                db.session.commit()
            for deleted_link in deleted:
                UserActivityLogger.info(
                    operation="ITEM_DELETE_LINK",
                    target_key=deleted_link["dst_item_pid"],
                    required_commit=require_commit
                )
            for updated_link in updated:
                UserActivityLogger.info(
                    operation="ITEM_UPDATE_LINK",
                    target_key=updated_link["dst_item_pid"],
                    required_commit=require_commit
                )
            for created_link in created:
                UserActivityLogger.info(
                    operation="ITEM_CREATE_LINK",
                    target_key=created_link["dst_item_pid"],
                    required_commit=require_commit
                )
        except IntegrityError as ex:
            # Log and handle integrity errors (e.g., duplicate entries)
            current_app.logger.error(ex)
            db.session.rollback()
            exec_info = sys.exc_info()
            tb_info = traceback.format_tb(exec_info[2])
            UserActivityLogger.error(
                operation="ITEM_UPDATE_LINK",
                remarks=tb_info[0]
            )
            return str(ex)
        except SQLAlchemyError as ex:
            # Log and handle other SQLAlchemy errors
            current_app.logger.error(ex)
            db.session.rollback()
            exec_info = sys.exc_info()
            tb_info = traceback.format_tb(exec_info[2])
            UserActivityLogger.error(
                operation="ITEM_UPDATE_LINK",
                remarks=tb_info[0]
            )
            return str(ex)
        # Return None if no errors occurred
        return None


    def bulk_create(self, items):
        """Create a list of item links in bulk.

        Args:
            dst_items: List of dictionaries containing
                'src_item_pid', 'dst_item_pid' and 'sele_id' to be created.
        """
        # Create a list of ItemReference objects for bulk insertion
        objects = [
            ItemReference(
                src_item_pid=item['src_item_pid'],
                dst_item_pid=item['dst_item_pid'],
                reference_type=item['sele_id']
            ) for item in items
        ]
        # Save all objects in a single database operation
        db.session.bulk_save_objects(objects)

    def bulk_update(self, items):
        """Update a list of item links in bulk.

        Args:
            items(list): List of dictionaries containing
                'src_item_pid', 'dst_item_pid' and 'sele_id' to be updated.
        """
        # Update each item relationship by merging changes into the database
        for item in items:
            db.session.merge(ItemReference(
                src_item_pid=item['src_item_pid'],
                dst_item_pid=item['dst_item_pid'],
                reference_type=item['sele_id']
            ))

    def bulk_delete(self, items):
        """Delete a list of item links in bulk.

        Args:
            items(list): List of dictionaries containing
                'src_item_pid', 'dst_item_pid' to be deleted.
        """
        for item in items:
            db.session.query(ItemReference).filter(
                ItemReference.src_item_pid==item['src_item_pid'],
                ItemReference.dst_item_pid==item['dst_item_pid'],
            ).delete(synchronize_session='fetch')
