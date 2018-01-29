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

"""Blueprint for weko-itemtypes-ui."""

from functools import wraps

from flask import Blueprint, abort, current_app, json, jsonify, redirect, \
    render_template, request, url_for, Flask
from flask_babelex import gettext as _
from flask_babelex import Babel
from flask_login import current_user
from invenio_db import db
from weko_records.api import ItemTypes, Mapping
from weko_records.proxies import current_permission_factory

blueprint = Blueprint(
    'weko_itemtypes_ui',
    __name__,
    url_prefix='/itemtypes',
    template_folder='templates',
    static_folder='static',
)

app = Flask(__name__)
babel = Babel(app)

def check_permission(permission, hidden=True):
    """Check if permission is allowed.

    If permission fails then the connection is aborted.

    :param permission: The permission to check.
    :param hidden: Determine if a 404 error (``True``) or 401/403 error
        (``False``) should be returned if the permission is rejected (i.e.
        hide or reveal the existence of a particular object).
    """
    if permission is not None and not permission().can():
        if hidden:
            abort(404)
        else:
            if current_user.is_authenticated:
                abort(403,
                      'You do not have a permission for itemtype')
            abort(401)


def need_permissions(hidden=False):
    """Get permission for buckets or abort.

    :param hidden: Determine which kind of error to return. (Default: ``False``)
    """
    def decorator_builder(f):
        @wraps(f)
        def decorate(*args, **kwargs):
            check_permission(current_permission_factory, hidden=hidden)
            return f(*args, **kwargs)
        return decorate
    return decorator_builder


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['ja', 'ja_JP', 'en'])


@blueprint.route("/", methods=['GET'])
@blueprint.route("/<int:item_type_id>", methods=['GET'])
@blueprint.route("/register", methods=['GET'])
@need_permissions()
def index(item_type_id=0):
    """Renders an item type register view."""
    lists = ItemTypes.get_latest()
    return render_template(
        current_app.config['WEKO_ITEMTYPES_UI_REGISTER_TEMPLATE'],
        lists=lists,
        id=item_type_id
    )


@blueprint.route("/<int:item_type_id>/render", methods=['GET'])
@need_permissions()
def render(item_type_id=0):
    result = None
    if item_type_id > 0:
        result = ItemTypes.get_by_id(id_=item_type_id)
    if result is None:
        result = {
            'table_row': [],
            'table_row_map': {},
            'meta_list': {},
            'schemaeditor': {
                'schema': {}
            }
        }
    return jsonify(result.render)


@blueprint.route("/register", methods=['POST'])
@blueprint.route("/<int:item_type_id>/register", methods=['POST'])
def register(item_type_id=0):
    """Register an item type."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    try:
        record = ItemTypes.update(id_=item_type_id,
                         name=data.get('table_row_map').get('name'),
                         schema=data.get('table_row_map').get('schema'),
                         form=data.get('table_row_map').get('form'),
                         render=data)
        if item_type_id == 0:
            item_type_id = record.model.id
        Mapping.create(item_type_id=item_type_id,
                       mapping=data.get('table_row_map').get('mapping'))
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify(msg=_('Fail'))
    current_app.logger.debug('itemtype register: {}'.format(item_type_id));
    return jsonify(msg=_('Success'))


@blueprint.route("/mapping", methods=['GET'])
@blueprint.route("/mapping/<int:ItemTypeID>", methods=['GET'])
def mapping_index(ItemTypeID=0):
    """Renders an item type mapping view.

    :param ItemTypeID: Item type ID. (Default: 0)
    :return: The rendered template.
    """
    lists = ItemTypes.get_all()
    if lists is None or len(lists) == 0:
        return render_template(
            current_app.config['WEKO_ITEMTYPES_UI_ERROR_TEMPLATE']
        )
    item_type = ItemTypes.get_by_id(ItemTypeID)
    if item_type is None:
        return redirect(url_for('.mapping_index', ItemTypeID=lists[0].id))
    item_type_mapping = Mapping.get_record(ItemTypeID)
    mapping = json.dumps(item_type_mapping, indent=4, ensure_ascii=False)
    current_app.logger.debug(mapping)
    return render_template(
        current_app.config['WEKO_ITEMTYPES_UI_MAPPING_TEMPLATE'],
        lists=lists,
        mapping=mapping,
        id=ItemTypeID
    )


@blueprint.route("/mapping", methods=['POST'])
def mapping_register():
    """Register an item type mapping."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()
    current_app.logger.debug(data)
    try:
        Mapping.create(item_type_id=data.get('item_type_id'),
                       mapping=json.loads(data.get('mapping')))
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify(msg=_('Fail'))
    return jsonify(msg=_('Success'))
