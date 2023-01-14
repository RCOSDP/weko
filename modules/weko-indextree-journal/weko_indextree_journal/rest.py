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

"""Blueprint for Weko index tree journal rest."""

from functools import wraps

from flask import Blueprint, abort, current_app, jsonify, make_response, \
    request
from invenio_communities.models import Community
from invenio_records_rest.utils import obj_or_import_string
from invenio_rest import ContentNegotiatedMethodView
from invenio_db import db

from .api import Journals
from .errors import JournalAddedRESTError, JournalBaseRESTError, \
    JournalDeletedRESTError, JournalInvalidDataRESTError, \
    JournalMovedRESTError, JournalNotFoundRESTError, JournalUpdatedRESTError
from .models import Journal


def need_record_permission(factory_name):
    """Decorator checking that the user has the required permissions on record.

    :param factory_name: name of the factory to retrieve.
    """
    def need_record_permission_builder(f):
        @wraps(f)
        def need_record_permission_decorator(self, *args,
                                             **kwargs):
            permission_factory = (getattr(self, factory_name))

            if permission_factory:
                if not permission_factory.can():
                    from flask_login import current_user
                    if not current_user.is_authenticated:
                        abort(401)
                    abort(403)

            return f(self, *args, **kwargs)
        return need_record_permission_decorator
    return need_record_permission_builder


def create_blueprint(app, endpoints):
    """Create Weko-IndexTree-Journal-REST blueprint.

    See: :data:`weko_indextree_journal.config.
    WEKO_INDEXTREE_JOURNAL_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_indextree_journal_rest',
        __name__,
        url_prefix='',
    )
    
    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("weko_indextree_journal dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    for endpoint, options in (endpoints or {}).items():
        if 'record_serializers' in options:
            record_serializers = options.get('record_serializers')
            record_serializers = {mime: obj_or_import_string(func)
                                  for mime, func in record_serializers.items()}
        else:
            record_serializers = {}

        record_class = obj_or_import_string(
            options.get('record_class'), default=Journals)

        ctx = dict(
            read_permission_factory=obj_or_import_string(
                options.get('read_permission_factory_imp')
            ),
            create_permission_factory=obj_or_import_string(
                options.get('create_permission_factory_imp')
            ),
            update_permission_factory=obj_or_import_string(
                options.get('update_permission_factory_imp')
            ),
            delete_permission_factory=obj_or_import_string(
                options.get('delete_permission_factory_imp')
            ),
            record_class=record_class,
            loaders={
                options.get('default_media_type'): lambda: request.get_json()},
        )

        iar = JournalActionResource.as_view(
            JournalActionResource.view_name.format(endpoint),
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )

        # ita = IndexTreeActionResource.as_view(
        #     IndexTreeActionResource.view_name.format(endpoint),
        #     ctx=ctx,
        #     record_serializers=record_serializers,
        #     default_media_type=options.get('default_media_type'),
        # )

        # blueprint.add_url_rule(
        #     options.pop('indextree_journal_route'),
        #     view_func=iar,
        #     methods=['GET', 'PUT', 'POST', 'DELETE'],
        # )

        # Moved to admin
        blueprint.add_url_rule(
            options.pop('admin_indexjournal_route'),
            view_func=iar,
            methods=['GET', 'PUT', 'POST', 'DELETE'],
        )

        # blueprint.add_url_rule(
        #     options.pop('tree_journal_route'),
        #     view_func=ita,
        #     methods=['GET'],
        # )

        # blueprint.add_url_rule(
        #     options.pop('item_tree_journal_route'),
        #     view_func=ita,
        #     methods=['GET'],
        # )

        # blueprint.add_url_rule(
        #     options.pop('journal_move_route'),
        #     view_func=ita,
        #     methods=['PUT'],
        # )

    return blueprint


class JournalActionResource(ContentNegotiatedMethodView):
    """Journal create update delete view."""

    view_name = '{0}_journal_action'

    def __init__(self, ctx, record_serializers=None,
                 default_media_type=None, **kwargs):
        """Constructor."""
        super(JournalActionResource, self).__init__(
            method_serializers={
                'GET': record_serializers,
                'PUT': record_serializers,
                'POST': record_serializers,
                'DELETE': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
                'PUT': default_media_type,
                'POST': default_media_type,
                'DELETE': record_serializers,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @need_record_permission('read_permission_factory')
    def get(self, journal_id, **kwargs):
        """Get a journal record."""
        try:
            if journal_id != 0:
                journal = self.record_class.get_journal(journal_id)

            if journal is None:
                journal = []

            return make_response(jsonify(journal), 200)
        except Exception as ex:
            current_app.logger.error(ex)
            raise JournalInvalidDataRESTError()

    # @pass_record
    @need_record_permission('create_permission_factory')
    def post(self, **kwargs):
        """Create a journal."""
        data = self.loaders[request.mimetype]()

        if not data:
            raise JournalInvalidDataRESTError()
        if not self.record_class.create(data):
            raise JournalAddedRESTError()

        status = 201
        msg = 'Journal created successfully.'

        return make_response(
            jsonify({'status': status, 'message': msg}), status)

    @need_record_permission('update_permission_factory')
    def put(self, journal_id, **kwargs):
        """Update a new journal."""
        data = self.loaders[request.mimetype]()
        if not data:
            raise JournalInvalidDataRESTError()
        if not self.record_class.update(journal_id, **data):
            raise JournalUpdatedRESTError()

        status = 200
        msg = 'Journal updated successfully.'
        return make_response(
            jsonify({'status': status, 'message': msg}), status)

    @need_record_permission('delete_permission_factory')
    def delete(self, journal_id, **kwargs):
        """Delete a journal."""
        if not journal_id or journal_id <= 0:
            raise JournalNotFoundRESTError()

        action = request.values.get('action', 'all')
        res = self.record_class.get_self_path(journal_id)
        if not res:
            raise JournalDeletedRESTError()

        if action in ('move', 'all'):
            result = self.record_class.\
                delete_by_action(action, journal_id)
            if not result:
                raise JournalBaseRESTError(
                    description='Could not delete data.')
        else:
            raise JournalInvalidDataRESTError()

        status = 200
        msg = 'Journal deleted successfully.'
        return make_response(
            jsonify({'status': status, 'message': msg}), status)
