# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Admin model views for Communities."""

from __future__ import absolute_import, print_function

import os
import json
import re
import sys
import traceback

from flask import request, abort, jsonify, redirect, url_for, flash
from flask.globals import current_app
from flask_admin.contrib.sqla import ModelView
from flask_admin import expose
from flask_login import current_user
from invenio_accounts.models import Role
from invenio_db import db
from sqlalchemy import func, or_
from weko_index_tree.models import Index
from wtforms.validators import ValidationError
from wtforms import FileField, RadioField, StringField
from wtforms.utils import unset_value
from invenio_i18n.ext import current_i18n
from weko_gridlayout.services import WidgetDesignPageServices
from weko_handle.api import Handle
from weko_workflow.config import WEKO_SERVER_CNRI_HOST_LINK
from b2handle.clientcredentials import PIDClientCredentials
from wtforms.ext.sqlalchemy.fields import QuerySelectField

from .models import Community, FeaturedCommunity, InclusionRequest
from .utils import get_user_role_ids, delete_empty


def _(x):
    """Identity function for string extraction."""
    return x


class CommunityModelView(ModelView):
    """ModelView for the Community."""

    can_edit = True
    can_delete = True
    can_view_details = True
    column_display_all_relations = True
    form_columns = ('id', 'cnri', 'owner', 'index', 'group', 'title', 'description', 'page',
                    'curation_policy', 'ranking', 'fixed_points','content_policy', 'thumbnail','login_menu_enabled')

    column_list = (
        'id',
        'title',
        'owner.name',
        'index',
        'deleted_at',
        'last_record_accepted',
        'ranking',
        'fixed_points',
    )

    column_searchable_list = ('id', 'title', 'description')
    edit_template = "invenio_communities/admin/edit.html"

    @expose('/new/', methods=['GET', 'POST'])
    def create_view(self):

        def validate_input_id(id):
            the_patterns = {
                "ASCII_LETTER_PATTERN": "[a-zA-Z0-9_-]+$",
                "FIRST_LETTER_PATTERN1": "^[a-zA-Z_-].*",
                "FIRST_LETTER_PATTERN2": "^[-]+[0-9]+",
            }
            the_result = {
                "ASCII_LETTER_PATTERN": "Don't use space or special "
                                        "character except `-` and `_`.",
                "FIRST_LETTER_PATTERN1": 'The first character cannot '
                                        'be a number or special character. '
                                        'It should be an '
                                        'alphabet character, "-" or "_"',
                "FIRST_LETTER_PATTERN2": "Cannot set negative number to ID.",
            }

            m = re.match(the_patterns['FIRST_LETTER_PATTERN1'], id)
            if m is None:
                raise ValidationError(the_result['FIRST_LETTER_PATTERN1'])
            m = re.match(the_patterns['FIRST_LETTER_PATTERN2'], id)
            if m is not None:
                raise ValidationError(the_result['FIRST_LETTER_PATTERN2'])
            m = re.match(the_patterns['ASCII_LETTER_PATTERN'], id)
            if m is None:
                raise ValidationError(the_result['ASCII_LETTER_PATTERN'])

        if self.can_create is False:
            abort(403)

        form = self.create_form()

        if(request.method == 'POST'):
            try:
                pageaddFlag = True
                form_data = request.form.to_dict()
                model = Community()
                validate_input_id(form_data['id'])
                model.id = form_data['id']
                model.id_role = form_data['owner']
                model.root_node_id = form_data['index']
                model.title = form_data['title']
                model.description = form_data['description']
                model.page = form_data['page']
                model.curation_policy = form_data['curation_policy']
                model.ranking = form_data['ranking']
                model.fixed_points = form_data['fixed_points']
                model.content_policy = form_data['content_policy']
                if form_data['login_menu_enabled'] == 'True':
                    model.login_menu_enabled = True
                else:
                    model.login_menu_enabled = False
                if form_data.get('group') != "__None":
                    model.group_id = form_data.get('group')
                the_result = {
                    "FILE_PATTERN": "Thumbnail file only 'jpeg', 'jpg', 'png' format.",
                }
                fp = request.files.get('thumbnail')
                if '' != fp.filename:
                    directory = os.path.join(
                        current_app.instance_path,
                        current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'],
                        'c')
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                    ext = os.path.splitext(fp.filename)[1].lower()
                    allowed_extensions = {'.png', '.jpg', '.jpeg'}
                    if ext not in allowed_extensions:
                        raise ValidationError(the_result['FILE_PATTERN'])
                    filename = os.path.join(
                        directory,
                        model.id + '_' + fp.filename)
                    file_uri = '/data/' + 'c/' + model.id + '_' + fp.filename
                    fp.save(filename)
                    model.thumbnail_path = file_uri

                catalog_json = json.loads(form_data['catalog_data'])
                flg, result_json = delete_empty(catalog_json['metainfo'])
                if flg:
                    model.catalog_json = result_json['parentkey']
                else:
                    model.catalog_json = None
                model.id_user = current_user.get_id()
                model.cnri = None

                comm = Community.create(
                    community_id=model.id,
                    role_id=model.id_role,
                    id_user=model.id_user,
                    root_node_id=model.root_node_id,
                    group_id=model.group_id,
                    title=model.title,
                    description=model.description,
                    page=model.page,
                    curation_policy=model.curation_policy,
                    ranking=model.ranking,
                    fixed_points=model.fixed_points,
                    content_policy=model.content_policy,
                    login_menu_enabled=model.login_menu_enabled,
                    thumbnail_path=model.thumbnail_path,
                    catalog_json=model.catalog_json,
                    cnri=model.cnri
                )
                db.session.commit()

                # get CNRI handle
                if current_app.config.get('WEKO_HANDLE_ALLOW_REGISTER_CNRI'):
                    weko_handle = Handle()
                    url = request.url.split('/admin/')[0] + '/c/' + str(model.id)
                    credential = PIDClientCredentials.load_from_JSON(
                        current_app.config.get('WEKO_HANDLE_CREDS_JSON_PATH'))
                    hdl = credential.get_prefix() + '/c/' + str(model.id)
                    handle = weko_handle.register_handle(location=url, hdl=hdl)
                    if handle:
                        model_for_handle = self.get_one(model.id)
                        model_for_handle.cnri = WEKO_SERVER_CNRI_HOST_LINK + str(handle)
                        db.session.commit()
                    else:
                        current_app.logger.info('Cannot connect Handle server!')

                data = [
                    {
                        "is_edit": False,
                        "page_id": 0,
                        "repository_id": model.id,
                        "title": "About",
                        "url": "/c/" + model.id + "/page/about",
                        "content": "",
                        "settings": "",
                        "multi_lang_data": {"en": "About"},
                        "is_main_layout": False,
                    },
                    {
                        "is_edit": False,
                        "page_id": 0,
                        "repository_id": model.id,
                        "title": "Editorial board",
                        "url": "/c/" + model.id + "/page/eb",
                        "content": "",
                        "settings": "",
                        "multi_lang_data": {"en": "Editorial board"},
                        "is_main_layout": False,
                    },
                    {
                        "is_edit": False,
                        "page_id": 0,
                        "repository_id": model.id,
                        "title": "OA Policy",
                        "url": "/c/" + model.id + "/page/oapolicy",
                        "content": "",
                        "settings": "",
                        "multi_lang_data": {"en": "OA Policy"},
                        "is_main_layout": False,
                    }
                ]
                for page in data:
                    addPageResult = WidgetDesignPageServices.add_or_update_page(page)
                    if addPageResult['result'] == False:
                        current_app.logger.error(page['url'] + " page add failed.")
                        pageaddFlag = False

                if pageaddFlag == False:
                    return redirect(url_for('.index_view', pageaddFlag=pageaddFlag))
                else:
                    return redirect(url_for('.index_view'))
            except Exception as e:
                traceback.print_exc()
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify({"Unexpected error": str(e)}), 400

        else:
            form.login_menu_enabled.data = 'False'

            return  self.render(
                "invenio_communities/admin/edit.html",
                form=form,
                jsonschema="/admin/community/jsonschema",
                schemaform="/admin/community/schemaform",
                pid=None,
                record=None,
                type = 'create',

                return_url=request.args.get('url'),
                c_id=id,
            )

    @expose('/edit/<string:id>/', methods=['GET', 'POST'])
    def edit_view(self, id):
        model = self.get_one(id)
        if model is None:
            abort(404)

        form=super(CommunityModelView, self).edit_form(id)
        form.id.data = model.id or ''
        form.cnri.data = model.cnri or ''
        form.title.data = model.title or ''
        form.owner.data = model.owner or ''
        form.index.data = model.index or ''
        form.group.data = model.group or ''
        form.description.data = model.description or ''
        form.page.data = model.page or ''
        form.curation_policy.data = model.curation_policy or ''
        form.ranking.data = model.ranking or '0'
        form.fixed_points.data = model.fixed_points or '0'
        form.content_policy.data = model.content_policy or ''
        if model.login_menu_enabled:
            form.login_menu_enabled.data = 'True'
        else:
            form.login_menu_enabled.data = 'False'

        if(request.method == 'POST'):
            form_data = request.form.to_dict()
            try:
                model.id_role = form_data['owner']
                model.root_node_id = form_data['index']
                model.title = form_data['title']
                model.description = form_data['description']
                model.page = form_data['page']
                model.curation_policy = form_data['curation_policy']
                model.ranking = form_data['ranking']
                model.fixed_points = form_data['fixed_points']
                model.content_policy = form_data['content_policy']
                if form_data['login_menu_enabled'] == 'True':
                    model.login_menu_enabled = True
                else:
                    model.login_menu_enabled = False
                if form_data.get('group') != "__None":
                    model.group_id = form_data.get('group')
                the_result = {
                    "FILE_PATTERN": "Thumbnail file only 'jpeg', 'jpg', 'png' format.",
                }
                fp = request.files.get('thumbnail')
                if '' != fp.filename:
                    directory = os.path.join(
                        current_app.instance_path,
                        current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'],
                        'c')
                    if not os.path.exists(directory):
                        os.makedirs(directory)

                    ext = os.path.splitext(fp.filename)[1].lower()
                    allowed_extensions = {'.png', '.jpg', '.jpeg'}
                    if ext not in allowed_extensions:
                        raise ValidationError(the_result['FILE_PATTERN'])
                    filename = os.path.join(
                        directory,
                        model.id + '_' + fp.filename)
                    file_uri = '/data/' + 'c/' + model.id  + '_' +  fp.filename
                    if model.thumbnail_path:
                        currentfile = os.path.join(
                            current_app.instance_path,
                            current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'],
                            'c',
                            model.thumbnail_path[8:])
                        try:
                            os.remove(currentfile)
                            current_app.logger.info(f"{currentfile} deleted.")
                        except Exception as e:
                            current_app.logger.error(f"file delete failed.: {e}")
                    fp.save(filename)
                    model.thumbnail_path = file_uri

                catalog_json = json.loads(form_data['catalog_data'])
                flg, result_json = delete_empty(catalog_json['metainfo'])
                if flg:
                    model.catalog_json = result_json['parentkey']
                else:
                    model.catalog_json = None

                # get CNRI handle
                if current_app.config.get('WEKO_HANDLE_ALLOW_REGISTER_CNRI') and not model.cnri:
                    weko_handle = Handle()
                    credential = PIDClientCredentials.load_from_JSON(
                        current_app.config.get('WEKO_HANDLE_CREDS_JSON_PATH'))
                    url = request.url.split('/admin/')[0] + '/c/' + str(id)
                    hdl = credential.get_prefix() + '/c/' + str(id)
                    handle = weko_handle.register_handle(location=url, hdl=hdl)
                    if handle:
                        model.cnri = WEKO_SERVER_CNRI_HOST_LINK + str(handle)
                    else:
                        current_app.logger.info('Cannot connect Handle server!')

                db.session.commit()
                return redirect(url_for('.index_view'))
            except Exception as e:
                traceback.print_exc()
                current_app.logger.error(e)
                db.session.rollback()
                return jsonify({"Unexpected error": str(e)}), 400

        else:
            # request method GET
            record = {}
            if model.catalog_json is not None:
                record['parentkey'] = model.catalog_json
            else:
                record = None
            return  self.render(
                "invenio_communities/admin/edit.html",
                form=form,
                jsonschema="/admin/community/jsonschema",
                schemaform="/admin/community/schemaform",
                pid=None,
                record=record,
                type = 'edit',

                return_url=request.args.get('url'),
                c_id=id,
            )


    @expose('/jsonschema', methods=['GET'])
    def get_json_schema(self):
        """Get json schema.

        :return: The json object.
        """
        try:
            json_schema = None
            # cur_lang = current_i18n.language

            """Log error for output info of journal, level: ERROR, status code: 101,
            content: Invalid setting file error"""
            filepath = "schemas/jsonschema.json"
            if (filepath
                != filepath)\
                or (filepath
                    == ""
                    or (current_app.config[
                        'WEKO_INDEXTREE_JOURNAL_SCHEMA_JSON_FILE'
                    ] is None)):
                current_app.logger.error(
                    '[{0}] Invalid setting file error'.format(101)
                )

            schema_file = os.path.join(
                os.path.dirname(__file__),
                filepath)

            json_schema = json.load(open(schema_file))
            if json_schema == {}:
                return '{}'

            result = db.session.execute("SELECT schema FROM item_type_property WHERE id = 1057;").fetchone()
            catalogschema = result[0]
            tempschema = catalogschema["properties"]
            keys_to_keep = [ 'catalog_contributors', 'catalog_identifiers', 'catalog_subjects', 'catalog_licenses', 'catalog_rights', 'catalog_access_rights']
            keys_to_remove = [k for k in tempschema.keys() if k not in keys_to_keep]
            for key in keys_to_remove:
                tempschema.pop(key)

            json_schema["properties"]["parentkey"]["items"]["properties"] = tempschema

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

            result = db.session.execute("SELECT forms FROM item_type_property WHERE id = 1057;").fetchone()
            temp_schema_form = [result[0]]

            schema_form = temp_schema_form

            i = 1
            for elem in schema_form:
                if 'title_i18n' in elem:
                    if cur_lang in elem['title_i18n']:
                        if len(elem['title_i18n'][cur_lang]) > 0:
                            elem['title'] = elem['title_i18n'][cur_lang]
                if 'items' in elem:
                    for sub_elem in elem['items'][:]:
                        if sub_elem['key'] in ['parentkey[].catalog_contributors', 'parentkey[].catalog_identifiers', 'parentkey[].catalog_subjects', 'parentkey[].catalog_licenses', 'parentkey[].catalog_rights', 'parentkey[].catalog_access_rights']:
                            if 'title_i18n' in sub_elem:
                                if cur_lang in sub_elem['title_i18n']:
                                    if len(sub_elem['title_i18n']
                                        [cur_lang]) > 0:
                                        sub_elem['title'] = sub_elem['title_i18n'][
                                            cur_lang]
                            if 'items' in sub_elem:
                                for sub_sub_elem in sub_elem['items'][:]:
                                    if 'title_i18n' in sub_sub_elem:
                                        if cur_lang in sub_sub_elem['title_i18n']:
                                            if len(sub_sub_elem['title_i18n']
                                                [cur_lang]) > 0:
                                                sub_sub_elem['title'] = sub_sub_elem['title_i18n'][
                                                    cur_lang]
                                    if 'items' in sub_sub_elem:
                                        for sub_sub_sub_elem in sub_sub_elem['items'][:]:
                                            if 'title_i18n' in sub_sub_sub_elem:
                                                if cur_lang in sub_sub_sub_elem['title_i18n']:
                                                    if len(sub_sub_sub_elem['title_i18n']
                                                        [cur_lang]) > 0:
                                                        sub_sub_sub_elem['title'] = sub_sub_sub_elem['title_i18n'][
                                                            cur_lang]
                        else:
                            elem['items'].remove(sub_elem)

        except BaseException:
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
            abort(500)
        return jsonify(schema_form)

    def on_model_delete(self, model):
        if model.cnri:
            from .tasks import delete_handle
            hdl = model.cnri.split(WEKO_SERVER_CNRI_HOST_LINK)[-1]
            delete_handle.delay(hdl)

        if model.thumbnail_path:
            currentfile = os.path.join(
                current_app.instance_path,
                current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'],
                'c',
                model.thumbnail_path[8:])
            try:
                os.remove(currentfile)
                current_app.logger.info(f"{currentfile} deleted.")
            except Exception as e:
                current_app.logger.error(f"file delete failed.: {e}")

    def on_model_change(self, form, model, is_created):
        """Perform some actions before a model is created or updated.

        Called from create_model and update_model in the same transaction
        (if it has any meaning for a store backend).
        By default does nothing.

        :param form:
            Form used to create/update model
        :param model:
            Model that will be created/updated
        :param is_created:
            Will be set to True if model was created and to False if edited
        """
        model.id_user = current_user.get_id()

    def _validate_input_id(self, field):
        the_patterns = {
            "ASCII_LETTER_PATTERN": "[a-zA-Z0-9_-]+$",
            "FIRST_LETTER_PATTERN1": "^[a-zA-Z_-].*",
            "FIRST_LETTER_PATTERN2": "^[-]+[0-9]+",
        }
        the_result = {
            "ASCII_LETTER_PATTERN": "Don't use space or special "
                                    "character except `-` and `_`.",
            "FIRST_LETTER_PATTERN1": 'The first character cannot '
                                     'be a number or special character. '
                                     'It should be an '
                                     'alphabet character, "-" or "_"',
            "FIRST_LETTER_PATTERN2": "Cannot set negative number to ID.",
        }

        m = re.match(the_patterns['FIRST_LETTER_PATTERN1'], field.data)
        if m is None:
            raise ValidationError(the_result['FIRST_LETTER_PATTERN1'])
        m = re.match(the_patterns['FIRST_LETTER_PATTERN2'], field.data)
        if m is not None:
            raise ValidationError(the_result['FIRST_LETTER_PATTERN2'])
        m = re.match(the_patterns['ASCII_LETTER_PATTERN'], field.data)
        if m is None:
            raise ValidationError(the_result['ASCII_LETTER_PATTERN'])
        field.data = field.data.lower()

    form_args = {
        'id': {
            'validators': [_validate_input_id]
        },
        'group': {
            'allow_blank': False,
            'query_factory': lambda: db.session.query(Role).filter(Role.name.like("%_groups_%")).all(),
        }
    }
    form_extra_fields = {
        'cnri': StringField(),
        'thumbnail': FileField(description='ファイルタイプ: JPG ,JPEG, PNG'),
        'login_menu_enabled': RadioField('login_menu_enabled', choices=[('False', 'Disabled'), ('True', 'Enabled')] ),
    }

    form_widget_args = {
        'id': {
            'placeholder': 'Please select ID',
            'maxlength': 100,
        }
    }

    @property
    def can_create(self):
        """Check permission for creating."""
        role_ids = get_user_role_ids()
        return  min(role_ids) <= \
                current_app.config['COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT']

    def role_query_cond(self, role_ids):
        """Query conditions by role_id and user_id."""
        if role_ids:
            return Community.group_id.in_(role_ids)

    def get_query(self):
        """Return a query for the model type.

        This method can be used to set a "persistent filter" on an index_view.
        If you override this method, don't forget to also override
        `get_count_query`,
        for displaying the correct
        item count in the list view, and `get_one`,
        which is used when retrieving records for the edit view.
        """
        role_ids = get_user_role_ids()

        if min(role_ids) <= \
                current_app.config['COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT']:
            return self.session.query(self.model).filter()

        return self.session.query(
            self.model).filter(self.role_query_cond(role_ids))

    def get_count_query(self):
        """Return a the count query for the model type.

        A ``query(self.model).count()`` approach produces an excessive
        subquery, so ``query(func.count('*'))`` should be used instead.
        """
        role_ids = get_user_role_ids()

        if min(role_ids) <= \
                current_app.config['COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT']:
            return self.session.query(func.count('*')).select_from(self.model)

        return self.session.query(
            func.count('*')
        ).select_from(self.model).filter(self.role_query_cond(role_ids))

    def edit_form(self, obj):
        """
        Instantiate model editing form and return it.

        Override to implement custom behavior.

        :param obj: input object
        """
        role_ids = get_user_role_ids()

        if min(role_ids) <= \
                current_app.config['COMMUNITIES_LIMITED_ROLE_ACCESS_PERMIT']:
            return super(CommunityModelView, self).edit_form(obj)
        else:
            return self._use_append_repository_edit(
                super(CommunityModelView, self).edit_form(obj),
                str(obj.index.id)
            )

    def _use_append_repository_edit(self, form, index_id: str):
        """Modified query_factory of index column.

        The query_factory callable passed to the field constructor will be
        called to obtain a query.
        """
        setattr(self, 'index_id', index_id)
        form.index.query_factory = self._get_child_index_list
        setattr(form, 'action', 'edit')
        return form

    def _get_child_index_list(self):
        """Query child indexes."""
        from weko_index_tree.api import Indexes
        index_id = str(getattr(self, 'index_id', ''))

        with db.session.no_autoflush:
            _query = list(
                item.cid for item in Indexes.get_recursive_tree(index_id))
            query = Index.query.filter(
                Index.id.in_(_query)).order_by(Index.id.asc()).all()

        return query


class FeaturedCommunityModelView(ModelView):
    """ModelView for the FeaturedCommunity."""

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    column_display_all_relations = True
    column_list = (
        'community',
        'start_date',
    )


class InclusionRequestModelView(ModelView):
    """ModelView of the InclusionRequest."""

    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    column_list = (
        'id_community',
        'id_record',
        'expires_at',
        'id_user'
    )


community_adminview = dict(
    model=Community,
    modelview=CommunityModelView,
    category=_('Communities'),
)

request_adminview = dict(
    model=InclusionRequest,
    modelview=InclusionRequestModelView,
    category=_('Communities'),
)

featured_adminview = dict(
    model=FeaturedCommunity,
    modelview=FeaturedCommunityModelView,
    category=_('Communities'),
)
