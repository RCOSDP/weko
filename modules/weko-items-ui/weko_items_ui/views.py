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

"""Blueprint for weko-items-ui."""

from flask import Blueprint, current_app, flash, json, jsonify, redirect, \
    render_template, request, url_for, Flask
from flask_babelex import gettext as _
from flask_babelex import Babel
from weko_records.api import ItemTypes

blueprint = Blueprint(
    'weko_items_ui',
    __name__,
    url_prefix='/items',
    template_folder='templates',
    static_folder='static',
)

app = Flask(__name__)
babel = Babel(app)


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(['ja', 'ja_JP', 'en'])


@blueprint.route("/", methods=['GET'])
@blueprint.route("/<int:item_type_id>", methods=['GET'])
def index(item_type_id=0):
    """Renders an item register view.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The rendered template.
    """
    current_app.logger.debug(item_type_id)
    lists = ItemTypes.get_latest()
    if lists is None or len(lists) == 0:
        return render_template(
            current_app.config['WEKO_ITEMS_UI_ERROR_TEMPLATE']
        )
    item_type = ItemTypes.get_by_id(item_type_id)
    if item_type is None:
        return redirect(url_for('.index', item_type_id=lists[0].item_type[0].id))
    json_schema = '/items/jsonschema/{}'.format(item_type_id)
    schema_form = '/items/schemaform/{}'.format(item_type_id)
    template = 'WEKO_ITEMS_UI_FORM_NOFILE_TEMPLATE'
    if 'filemeta' in json.dumps(item_type.schema):
        template = 'WEKO_ITEMS_UI_FORM_TEMPLATE'
    return render_template(
        current_app.config[template],
        record={},
        jsonschema=json_schema,
        schemaform=schema_form,
        lists=lists,
        id=item_type_id
    )


@blueprint.route('/jsonschema/<int:item_type_id>', methods=['GET'])
def get_json_schema(item_type_id=0):
    """Get json schema.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The json object.
    """
    current_app.logger.debug(item_type_id)
    result = None
    if item_type_id > 0:
        result = ItemTypes.get_record(item_type_id)
    current_app.logger.debug(result)
    if result is None:
        return '{}'
    return jsonify(result)


@blueprint.route('/schemaform/<int:item_type_id>', methods=['GET'])
def get_schema_form(item_type_id=0):
    """Get schema form.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The json object.
    """
    current_app.logger.debug(item_type_id)
    result = None
    if item_type_id > 0:
        result = ItemTypes.get_by_id(item_type_id)
    if result is None:
        return '["*"]'
    current_app.logger.debug(jsonify(result.form))
    return jsonify(result.form)
