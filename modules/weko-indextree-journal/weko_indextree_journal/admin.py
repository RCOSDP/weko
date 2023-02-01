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

"""Weko Index Tree Journal admin."""

from __future__ import absolute_import, print_function

import json
import os
import sys

from flask import abort, current_app, json, jsonify, session
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_login import login_required
from invenio_i18n.ext import current_i18n
from weko_records.api import ItemTypes

from .api import Journals
from .permissions import indextree_journal_permission


class IndexJournalSettingView(BaseView):
    """Index journal setting view."""

    @indextree_journal_permission.require(http_exception=403)
    @expose('/', methods=['GET'])
    @expose('/<int:index_id>', methods=['GET'])
    def index(self, index_id=0):
        """Render a basic view."""
        lists = ItemTypes.get_latest()
        if lists is None or len(lists) == 0:
            return self.render(
                current_app.config['WEKO_ITEMS_UI_ERROR_TEMPLATE']
            )

        # Get journal info.
        journal = []
        journal_id = None
        if index_id > 0:
            journal = Journals.get_journal_by_index_id(index_id)
            if journal is not None:
                journal_id = journal.get("id")

        json_record = journal

        """Log error for output info of journal, level: ERROR, status code: 101,
        content: Invalid setting file error."""
        if (current_app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_API']
                != "/admin/indexjournal/jsonschema") \
            or (current_app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_API'] == ""
                or (current_app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_API']
                    is None)):
            current_app.logger.error(
                '[{0}] Invalid setting file error'.format(101)
            )

        """Log error for output info of journal, level: ERROR, status code: 101,
        content: Invalid setting file error."""
        if (current_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_API']
                != "/admin/indexjournal/schemaform") \
            or (current_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_API'] == ""
                or (current_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_API']
                    is None)):
            current_app.logger.error(
                '[{0}] Invalid setting file error'.format(101)
            )

        return self.render(
            current_app.config['WEKO_INDEXTREE_JOURNAL_ADMIN_INDEX_TEMPLATE'],
            get_tree_json=current_app.config['WEKO_INDEX_TREE_LIST_API'],
            upt_tree_json='',
            mod_tree_detail=current_app.config['WEKO_INDEX_TREE_API'],
            mod_journal_detail=current_app.config['WEKO_INDEXTREE_JOURNAL_API'],
            record=json_record,
            jsonschema=current_app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_API'],
            schemaform=current_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_API'],
            lists=lists,
            links=None,
            pid=None,
            index_id=index_id,
            journal_id=journal_id,
            lang_code=session.get('selected_language', 'en')  # Set default
        )

    # TODO: Delete if not used.
    @expose('/index/<int:index_id>', methods=['GET'])
    def get_journal_by_index_id(self, index_id=0):
        """Get journal by index id."""
        try:
            result = None
            if index_id > 0:
                journal = Journals.get_journal_by_index_id(index_id)

            if journal is None:
                journal = '{}'
            return jsonify(journal)
        except BaseException:
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
        return abort(400)

    @expose('/jsonschema', methods=['GET'])
    def get_json_schema(self):
        """Get json schema.

        :return: The json object.
        """
        try:
            json_schema = None
            cur_lang = current_i18n.language

            """Log error for output info of journal, level: ERROR, status code: 101,
            content: Invalid setting file error"""
            if (current_app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE']
                != "schemas/jsonschema.json")\
                or (current_app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE']
                    == ""
                    or (current_app.config[
                        'WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE'
                    ] is None)):
                current_app.logger.error(
                    '[{0}] Invalid setting file error'.format(101)
                )

            schema_file = os.path.join(
                os.path.dirname(__file__),
                current_app.config['WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE'])

            json_schema = json.load(open(schema_file))
            if json_schema is None:
                return '{}'

            properties = json_schema.get('properties')

            for key, value in properties.items():
                if 'validationMessage_i18n' in value:
                    msg = {}
                    for k, v in value['validationMessage_i18n'].items():
                        msg[k] = v[cur_lang]
                    value['validationMessage'] = msg

        except BaseException:
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
            abort(500)
        return jsonify(json_schema)

    @expose('/schemaform', methods=['GET'])
    def get_schema_form(self):
        """Get schema form.

        :return: The json object.
        """
        try:
            schema_form = None
            cur_lang = current_i18n.language

            """Log error for output info of journal, level: ERROR, status code: 101,
            content: Invalid setting file error."""
            if (current_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE']
                    != "schemas/schemaform.json") or \
                    (current_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE'] == ""
                     or (current_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE']
                         is None)):
                current_app.logger.error(
                    '[{0}] Invalid setting file error'.format(101)
                )

            form_file = os.path.join(
                os.path.dirname(__file__),
                current_app.config['WEKO_INDEXTREE_JOURNAL_FORM_JSON_FILE'])

            schema_form = json.load(open(form_file))
            if schema_form is None:
                return '["*"]'

            if 'default' != cur_lang:
                for elem in schema_form:
                    if 'title_i18n' in elem:
                        if cur_lang in elem['title_i18n']:
                            if len(elem['title_i18n'][cur_lang]) > 0:
                                elem['title'] = elem['title_i18n'][cur_lang]
                    if 'items' in elem:
                        for sub_elem in elem['items']:
                            if 'title_i18n' in sub_elem:
                                if cur_lang in sub_elem['title_i18n']:
                                    if len(sub_elem['title_i18n']
                                           [cur_lang]) > 0:
                                        sub_elem['title'] = sub_elem['title_i18n'][
                                            cur_lang]
        except BaseException:
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
            abort(500)
        return jsonify(schema_form)


index_journal_adminview = {
    'view_class': IndexJournalSettingView,
    'kwargs': {
        'category': _('Index Tree'),
        'name': _('Journal Information'),
        'endpoint': 'indexjournal'
    }
}

__all__ = (
    'index_journal_adminview',
)
