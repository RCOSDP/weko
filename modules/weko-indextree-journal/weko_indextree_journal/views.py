# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# WEKO-Indextree-Journal is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Module of weko-indextree-journal."""

# TODO: This is an example file. Remove it if you do not need it, including
# the templates and static folders as well as the test case.

from __future__ import absolute_import, print_function
import sys
import json
import numpy

from flask import (
    Blueprint, render_template, current_app, json, abort, jsonify)
from flask_login import login_required
from invenio_i18n.ext import current_i18n
from flask_babelex import gettext as _
from weko_records.api import ItemTypes
from weko_groups.api import Group
from .api import Journals
from .tasks import export_journal_task

from .permissions import indextree_journal_permission

blueprint = Blueprint(
    'weko_indextree_journal',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/indextree/journal',
)

@blueprint.route("/")
@blueprint.route("/<int:index_id>")
@login_required
def index(index_id = 0):
    """Render a basic view."""
    item_type_id = 20 # item tpye's journal = 21
    lists = ItemTypes.get_latest()
    if lists is None or len(lists) == 0:
        return render_template(
            current_app.config['WEKO_ITEMS_UI_ERROR_TEMPLATE']
        )
    item_type = ItemTypes.get_by_id(item_type_id)
    if item_type is None:
        return
    json_schema = '/indextree/journal/jsonschema/{}'.format(item_type_id)
    schema_form = '/indextree/journal/schemaform/{}'.format(item_type_id)
    
    # Get journal info.
    journal = []
    journal_id = None
    if index_id > 0:
        journal = Journals.get_journal_by_index_id(index_id)
        if journal is not None:
            journal_id = journal.get("id")

    json_record = journal

    return render_template(
        current_app.config['WEKO_INDEXTREE_JOURNAL_INDEX_TEMPLATE'],
        get_tree_json=current_app.config['WEKO_INDEX_TREE_LIST_API'],
        upt_tree_json='',
        mod_tree_detail=current_app.config['WEKO_INDEX_TREE_API'],
        mod_journal_detail=current_app.config['WEKO_INDEXTREE_JOURNAL_API'],
        record=json_record,
        jsonschema=json_schema,
        schemaform=schema_form,
        lists=lists,
        links=None,
        id=item_type_id,
        files=None,
        pid=None,
        index_id = index_id,
        journal_id = journal_id
    )

@blueprint.route("/index/<int:index_id>")
def get_journal_by_index_id(index_id = 0):
    try:
        result = None
        if index_id > 0:
            journal = Journals.get_journal_by_index_id(index_id)

        if journal is None:
            journal = '{}'
        return jsonify(journal)
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)

@blueprint.route("/export", methods=['GET'])
@login_required
def export_journals():
    try:
        # Get all journal records in journal table.
        journals = Journals.get_all_journals()
        results = [obj.__dict__ for obj in journals]
        data = numpy.asarray(results)
        numpy.savetxt("journal.tsv", data, delimiter=",")

        # jsonList = json.dumps({"results" : results})
        # Save journals information to file
        return jsonify({"result" : True})
    except Exception as ex:
        current_app.logger.debug(ex)
    return jsonify({"result" : False})

def obj_dict(obj):
    return obj.__dict__
    
@blueprint.route("/right-content", methods=['GET'])
def get_journal_content():
    """Render a content of journal."""
    item_type_id = 19 # item tpye's journal = 21
    lists = ItemTypes.get_latest()
    if lists is None or len(lists) == 0:
        return render_template(
            current_app.config['WEKO_ITEMS_UI_ERROR_TEMPLATE']
        )
    item_type = ItemTypes.get_by_id(item_type_id)
    if item_type is None:
        return
    json_schema = '/indextree/journal/jsonschema/{}'.format(item_type_id)
    schema_form = '/indextree/journal/schemaform/{}'.format(item_type_id)

    return render_template(
        current_app.config['WEKO_INDEXTREE_JOURNAL_CONTENT_TEMPLATE'],
        record=None,
        jsonschema=json_schema,
        schemaform=schema_form,
        lists=lists,
        links=None,
        id=item_type_id,
        files=None,
        pid=None
    )


@blueprint.route('/jsonschema/<int:item_type_id>', methods=['GET'])
@login_required
# @item_permission.require(http_exception=403)
def get_json_schema(item_type_id=0):
    """Get json schema.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The json object.
    """
    try:
        result = None
        cur_lang = current_i18n.language

        if item_type_id > 0:
            result = ItemTypes.get_by_id(item_type_id)

            if result is None:
                return '{}'
            
            json_schema = result.schema
            properties = json_schema.get('properties')

            for key, value in properties.items():
                if 'validationMessage_i18n' in value:
                    msg = {}
                    for k, v in value['validationMessage_i18n'].items():
                        msg[k] = v[cur_lang]
                    value['validationMessage'] = msg

        if result is None:
            return '{}'
        return jsonify(json_schema)
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)


@blueprint.route('/schemaform/<int:item_type_id>', methods=['GET'])
@login_required
# @item_permission.require(http_exception=403)
def get_schema_form(item_type_id=0):
    """Get schema form.

    :param item_type_id: Item type ID. (Default: 0)
    :return: The json object.
    """
    try:
        # cur_lang = 'default'
        # if current_app.config['I18N_SESSION_KEY'] in session:
        #     cur_lang = session[current_app.config['I18N_SESSION_KEY']]
        cur_lang = current_i18n.language
        result = None
        if item_type_id > 0:
            result = ItemTypes.get_by_id(item_type_id)
        if result is None:
            return '["*"]'
        schema_form = result.form
        filemeta_form = schema_form[0]
        if 'filemeta' == filemeta_form.get('key'):
            group_list = Group.get_group_list()
            filemeta_form_group = filemeta_form.get('items')[-1]
            filemeta_form_group['type'] = 'select'
            filemeta_form_group['titleMap'] = group_list
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
                                if len(sub_elem['title_i18n'][cur_lang]) > 0:
                                    sub_elem['title'] = sub_elem['title_i18n'][
                                        cur_lang]
        return jsonify(schema_form)
    except:
        current_app.logger.error('Unexpected error: ', sys.exc_info()[0])
    return abort(400)

@blueprint.route('/save/kbart', methods=['GET'])
@login_required
def check_view(item_type_id=0):
    """Render a check view."""
    result = export_journal_task(p_path = '')
    return jsonify(result)
