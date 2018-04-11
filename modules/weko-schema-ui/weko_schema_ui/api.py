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

"""Schema API."""

from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.expression import asc, desc

from invenio_db import db
from invenio_records.api import RecordBase
from invenio_records.errors import MissingModelError
from .models import OAIServerSchema


class WekoSchema(RecordBase):
    """Define API for Weko Schema creation and manipulation."""

    @classmethod
    def create(cls, uuid, sname, fdata, xsd, schema, ns=None, isvalid=True):
        """
        create a schema record stored in db
        :param uuid:
        :param sname:
        :param fdata:
        :param xsd:
        :param schema:
        :param ns:
        :param isvalid:
        :return:
        """
        with db.session.begin_nested():
            record = cls(fdata)
            record.model = OAIServerSchema(id=uuid, schema_name=sname, form_data=fdata, xsd=xsd,
                                           namespaces=ns, schema_location=schema, isvalid=isvalid)
            db.session.add(record.model)

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
            query = OAIServerSchema.query.filter_by(id=id_, isvalid=True)
            if not with_deleted:
                query = query.filter(OAIServerSchema.xsd != None)  # noqa
            obj = query.one()
            return cls(obj.form_data, model=obj)

    @classmethod
    def get_record_by_name(cls, name, with_deleted=False):
        """Retrieve the record by id.

        Raise a database exception if the record does not exist.

        :param id_: record ID.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: The :class:`Record` instance.
        """
        with db.session.no_autoflush:
            query = OAIServerSchema.query.filter_by(schema_name=name, isvalid=True)
            if not with_deleted:
                query = query.filter(OAIServerSchema.xsd != None)  # noqa
            obj = query.one_or_none()
            return cls(obj.form_data, model=obj) if obj else None

    @classmethod
    def get_records(cls, ids, with_deleted=False):
        """Retrieve multiple records by id.

        :param ids: List of record IDs.
        :param with_deleted: If `True` then it includes deleted records.
        :returns: A list of :class:`Record` instances.
        """
        with db.session.no_autoflush:
            query = OAIServerSchema.query.filter(OAIServerSchema.id.in_(ids))
            if not with_deleted:
                query = query.filter(OAIServerSchema.xsd != None)  # noqa

            return [cls(obj.form_data, model=obj) for obj in query.all()]

    @classmethod
    def get_all(cls, with_deleted=False):
        """Retrieve all records.

        :param with_deleted: If `True` then it includes deleted records.
        :returns: A list of :class:`Record` instances.
        """
        with db.session.no_autoflush:
            query = OAIServerSchema.query.order_by(OAIServerSchema.is_mapping)
            if not with_deleted:
                query = query.filter(OAIServerSchema.isvalid == True)  # noqa
            return query.all()


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
            # before_record_delete.send(
            #     current_app._get_current_object(),
            #     record=self
            # )

            if force:
                db.session.delete(self.model)
            else:
                self.model.json = None
                db.session.merge(self.model)

        # after_record_delete.send(
        #     current_app._get_current_object(),
        #     record=self
        # )
        return self

    @classmethod
    def delete_by_id(self, pid):
        """aaa"""

        with db.session.begin_nested():
            obj = OAIServerSchema.query.filter_by(id=pid).one()
        db.session.delete(obj)
        db.session.commit()
        return obj.schema_name

