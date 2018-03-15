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

"""Blueprint for weko-authors."""


from flask import Blueprint, current_app, jsonify, render_template, request
from flask_babelex import gettext as _
from invenio_indexer.api import RecordIndexer

blueprint = Blueprint(
    'weko_authors',
    __name__,
    url_prefix='/authors',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/")
def index():
    """Render a basic view."""
    return render_template(
        current_app.config['WEKO_AUTHORS_EDIT_TEMPLATE'])


@blueprint.route("/add", methods=['POST'])
# @blueprint.route("/<int:item_type_id>/register", methods=['POST'])
def add(item_type_id=0):
    """Register an item type."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg=_('Header Error'))

    data = request.get_json()

    indexer = RecordIndexer()
    indexer.client.index(
                         index="author",
                         doc_type="author",
                         body=data,
                         )
    # try:
    #     record = ItemTypes.update(id_=item_type_id,
    #                               name=data.get('table_row_map').get('name'),
    #                               schema=data.get('table_row_map').get(
    #                                   'schema'),
    #                               form=data.get('table_row_map').get('form'),
    #                               render=data)
    #     Mapping.create(item_type_id=record.model.id,
    #                    mapping=data.get('table_row_map').get('mapping'))
    #     db.session.commit()
    # except:
    #     db.session.rollback()
    #     return jsonify(msg=_('Fail'))
    # current_app.logger.debug('itemtype register: {}'.format(item_type_id))
    return jsonify(msg=_('Success'))
