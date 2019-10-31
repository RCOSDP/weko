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

"""Weko-Itemtype UI admin."""

import sys

from flask import abort, current_app, flash, json, jsonify, redirect, \
    request, session, url_for
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from invenio_db import db
from invenio_i18n.ext import current_i18n
from weko_admin.models import BillingPermission
from weko_records.api import ItemsMetadata, ItemTypeEditHistory, \
    ItemTypeNames, ItemTypeProps, ItemTypes, Mapping
from weko_schema_ui.api import WekoSchema

from .config import WEKO_BILLING_FILE_ACCESS, WEKO_BILLING_FILE_PROP_ID
from .permissions import item_type_permission
from .utils import fix_json_schema, has_system_admin_access, remove_xsd_prefix


class ItemTypeMetaDataView(BaseView):
    """ItemTypeMetaDataView."""

    @expose('/', methods=['GET'])
    @expose('/<int:item_type_id>', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def index(self, item_type_id=0):
        """Renders an item type register view.

        :param item_type_id: Item type i. Default 0.
        """
        lists = ItemTypes.get_latest(True)
        # Check that item type is already registered to an item or not
        for item in lists:
            # Get all versions
            all_records = ItemTypes.get_records_by_name_id(name_id=item.id)
            item.belonging_item_flg = False
            for item in all_records:
                metaDataRecords = ItemsMetadata.get_by_item_type_id(
                    item_type_id=item.id)
                item.belonging_item_flg = len(metaDataRecords) > 0
                if item.belonging_item_flg:
                    break
        is_sys_admin = has_system_admin_access()

        return self.render(
            current_app.config['WEKO_ITEMTYPES_UI_ADMIN_REGISTER_TEMPLATE'],
            lists=lists,
            id=item_type_id,
            is_sys_admin=is_sys_admin,
            lang_code=session.get('selected_language', 'en')  # Set default
        )

    @expose('/<int:item_type_id>/render', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def render_itemtype(self, item_type_id=0):
        """Renderer."""
        result = None
        if item_type_id > 0:
            result = ItemTypes.get_by_id(id_=item_type_id, with_deleted=True)
        if result is None:
            result = {
                'table_row': [],
                'table_row_map': {},
                'meta_list': {},
                'schemaeditor': {
                    'schema': {}
                },
                'edit_notes': {}
            }
        else:
            edit_notes = result.latest_edit_history
            result = result.render
            result['edit_notes'] = edit_notes

        return jsonify(result)

    @expose('/delete', methods=['POST'])
    @expose('/delete/', methods=['POST'])
    @expose('/delete/<int:item_type_id>', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def delete_itemtype(self, item_type_id=0):
        """Soft-delete an item type."""
        if item_type_id > 0:
            record = ItemTypes.get_record(id_=item_type_id)
            if record is not None:
                # Check harvesting_type
                if record.model.harvesting_type:
                    flash(_('Cannot delete Item type for Harvesting.'),
                          'error')
                    return jsonify(code=-1)
                # Get all versions
                all_records = ItemTypes.get_records_by_name_id(
                    name_id=record.model.name_id)
                # Check that item type is already registered to an item or not
                for item in all_records:
                    metaDataRecords = ItemsMetadata.get_by_item_type_id(
                        item_type_id=item.id)
                    if len(metaDataRecords) > 0:
                        flash(
                            _(
                                'Cannot delete due to child'
                                ' existing item types.'),
                            'error')
                        return jsonify(code=-1)
                # Get item type name
                item_type_name = ItemTypeNames.get_record(
                    id_=record.model.name_id)
                if all_records and item_type_name:
                    try:
                        # Delete item type name
                        ItemTypeNames.delete(item_type_name)
                        # Delete item typea
                        for k in all_records:
                            k.delete()
                        db.session.commit()
                    except BaseException:
                        db.session.rollback()
                        current_app.logger.error('Unexpected error: ',
                                                 sys.exc_info()[0])
                        flash(_('Failed to delete Item type.'), 'error')
                        return jsonify(code=-1)

                    current_app.logger.debug(
                        'Itemtype delete: {}'.format(item_type_id))
                    flash(_('Deleted Item type successfully.'))
                    return jsonify(code=0)

        flash(_('An error has occurred.'), 'error')
        return jsonify(code=-1)

    @expose('/register', methods=['POST'])
    @expose('/<int:item_type_id>/register', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def register(self, item_type_id=0):
        """Register an item type."""
        if request.headers['Content-Type'] != 'application/json':
            current_app.logger.debug(request.headers['Content-Type'])
            return jsonify(msg=_('Header Error'))

        data = request.get_json()
        try:
            json_schema = fix_json_schema(
                data.get(
                    'table_row_map').get(
                        'schema'))
            if not json_schema:
                raise ValueError('Schema is in wrong format.')

            record = ItemTypes.update(id_=item_type_id,
                                      name=data.get(
                                          'table_row_map').get('name'),
                                      schema=json_schema,
                                      form=data.get(
                                          'table_row_map').get('form'),
                                      render=data)

            Mapping.create(item_type_id=record.model.id,
                           mapping=data.get('table_row_map').get('mapping'))

            ItemTypeEditHistory.create_or_update(
                item_type_id=record.model.id,
                user_id=current_user.get_id(),
                notes=data.get('edit_notes', {})
            )

            db.session.commit()
        except BaseException:
            db.session.rollback()
            return jsonify(msg=_('Failed to register Item type.'))
        current_app.logger.debug('itemtype register: {}'.format(item_type_id))
        flash(_('Successfuly registered Item type.'))
        redirect_url = url_for('.index', item_type_id=record.model.id)
        return jsonify(msg=_('Successfuly registered Item type.'),
                       redirect_url=redirect_url)

    @expose('/restore', methods=['POST'])
    @expose('/restore/', methods=['POST'])
    @expose('/restore/<int:item_type_id>', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def restore_itemtype(self, item_type_id=0):
        """Restore logically deleted item types."""
        if item_type_id > 0:
            record = ItemTypes.get_record(id_=item_type_id, with_deleted=True)
            if record is not None and record.model.is_deleted:
                # Get all versions
                all_records = ItemTypes.get_records_by_name_id(
                    name_id=record.model.name_id, with_deleted=True)
                # Get item type name
                item_type_name = ItemTypeNames.get_record(
                    id_=record.model.name_id, with_deleted=True)
                if all_records and item_type_name:
                    try:
                        # Restore item type name
                        ItemTypeNames.restore(item_type_name)
                        # Restore item typea
                        for k in all_records:
                            k.restore()
                        db.session.commit()
                    except BaseException:
                        db.session.rollback()
                        current_app.logger.error('Unexpected error: ',
                                                 sys.exc_info()[0])
                        return jsonify(code=-1,
                                       msg=_('Failed to restore Item type.'))

                    current_app.logger.debug(
                        'Itemtype restore: {}'.format(item_type_id))
                    return jsonify(code=0,
                                   msg=_('Restored Item type successfully.'))

        return jsonify(code=-1, msg=_('An error has occurred.'))


class ItemTypePropertiesView(BaseView):
    """ItemTypePropertiesView."""

    @expose('/', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def index(self, property_id=0):
        """Renders an primitive property view."""
        lists = ItemTypeProps.get_records([])

        billing_perm = BillingPermission.get_billing_information_by_id(
            WEKO_BILLING_FILE_ACCESS)
        if not billing_perm or not billing_perm.is_active:
            for prop in lists:
                if prop.id == WEKO_BILLING_FILE_PROP_ID:
                    lists.remove(prop)

        return self.render(
            current_app.config['WEKO_ITEMTYPES_UI_ADMIN_CREATE_PROPERTY'],
            lists=lists,
            lang_code=session.get('selected_language', 'en')  # Set default
        )

    @expose('/list', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def get_property_list(self, property_id=0):
        """Renders an primitive property view."""
        lang = request.values.get('lang')

        props = ItemTypeProps.get_records([])

        billing_perm = BillingPermission.get_billing_information_by_id(
            WEKO_BILLING_FILE_ACCESS)
        if not billing_perm and not billing_perm.is_active:
            for prop in props:
                if prop.id == WEKO_BILLING_FILE_PROP_ID:
                    props.remove(prop)

        lists = {}
        for k in props:
            name = k.name
            if lang and 'title_i18n' in k.form and \
                lang in k.form['title_i18n'] and \
                    k.form['title_i18n'][lang]:
                name = k.form['title_i18n'][lang]
            is_file = False
            if (k.schema.get('properties')
                    and k.schema.get('properties').get('filename')):
                is_file = True
            tmp = {'name': name, 'schema': k.schema, 'form': k.form,
                   'forms': k.forms, 'sort': k.sort, 'is_file': is_file}
            lists[k.id] = tmp

        lists['defaults'] = current_app.config[
            'WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES']

        return jsonify(lists)

    @expose('/<int:property_id>', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def get_property(self, property_id=0):
        """Renders an primitive property view."""
        prop = ItemTypeProps.get_record(property_id)
        tmp = {'id': prop.id, 'name': prop.name, 'schema': prop.schema,
               'form': prop.form, 'forms': prop.forms}
        return jsonify(tmp)

    @expose('', methods=['POST'])
    @expose('/<int:property_id>', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def custom_property_new(self, property_id=0):
        """Register an item type."""
        if request.headers['Content-Type'] != 'application/json':
            current_app.logger.debug(request.headers['Content-Type'])
            return jsonify(msg=_('Header Error'))

        data = request.get_json()
        try:
            ItemTypeProps.create(property_id=property_id,
                                 name=data.get('name'),
                                 schema=data.get('schema'),
                                 form_single=data.get('form1'),
                                 form_array=data.get('form2'))
            db.session.commit()
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return jsonify(msg=_('Failed to save property.'))
        return jsonify(msg=_('Saved property successfully.'))


class ItemTypeMappingView(BaseView):
    """ItemTypeMappingView."""

    @expose('/', methods=['GET'])
    @expose('/<int:ItemTypeID>', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def index(self, ItemTypeID=0):
        """Renders an item type mapping view.

        :param ItemTypeID: Item type ID. (Default: 0)
        :return: The rendered template.
        """
        try:
            lists = ItemTypes.get_latest()    # ItemTypes.get_all()
            if lists is None or len(lists) == 0:
                return self.render(
                    current_app.config['WEKO_ITEMTYPE'
                                       'S_UI_ADMIN_ERROR_TEMPLATE']
                )
            item_type = ItemTypes.get_by_id(ItemTypeID)
            if item_type is None:
                current_app.logger.info(lists[0].item_type[0])
                return redirect(url_for('itemtypesmapping.index',
                                        ItemTypeID=lists[0].item_type[0].id))
            itemtype_list = []
            itemtype_prop = item_type.schema.get('properties')
            sys_admin = current_app.config['WEKO_ADMIN_PERMISSION_ROLE_SYSTEM']
            is_admin = False
            with db.session.no_autoflush:
                for role in list(current_user.roles or []):
                    if role.name == sys_admin:
                        is_admin = True
                        break

            cur_lang = current_i18n.language

            meta_system = item_type.render.get('meta_system')
            table_rows = ['pubdate']
            render_table_row = item_type.render.get('table_row')

            meta_system_items = ['updated_date', 'created_date',
                                 'persistent_identifier_doi',
                                 'persistent_identifier_h',
                                 'ranking_page_url', 'belonging_index_info']

            for key in meta_system_items:
                if isinstance(meta_system, dict) and \
                        isinstance(meta_system[key], dict):
                    if meta_system[key]['title_i18n'] and cur_lang in \
                        meta_system[key]['title_i18n'] and \
                        meta_system[key]['title_i18n'][cur_lang] and \
                            meta_system[key]['title_i18n'][cur_lang].strip():
                        meta_system[key]['title'] = \
                            meta_system[key]['title_i18n'][cur_lang]
                    else:
                        meta_system[key]['title'] = \
                            meta_system[key]['title_i18n']['en'] if \
                            meta_system[key]['title_i18n'] and \
                            meta_system[key]['title_i18n']['en'] else ''

            if isinstance(render_table_row, list):
                table_rows.extend(render_table_row)
            for key in table_rows:
                prop = itemtype_prop.get(key)
                schema_form = item_type.form
                elem_str = ''
                if 'default' != cur_lang:
                    for elem in schema_form:
                        if 'items' in elem:
                            if elem['key'] == key:
                                if 'title_i18n' in elem:
                                    if cur_lang in elem['title_i18n']:
                                        if len(elem['title_i18n']
                                               [cur_lang]) > 0:
                                            elem_str = elem['title_i18n'][
                                                cur_lang]
                                else:
                                    elem_str = elem['title']
                            for sub_elem in elem['items']:
                                if 'key' in sub_elem and \
                                        sub_elem['key'] == key:
                                    if 'title_i18n' in sub_elem:
                                        if cur_lang in sub_elem['title_i18n']:
                                            if len(
                                                sub_elem['title_i18n'][
                                                    cur_lang]) > 0:
                                                elem_str = \
                                                    sub_elem['title_i18n'][
                                                        cur_lang]
                                    else:
                                        elem_str = sub_elem['title']
                                    break
                        else:
                            if elem['key'] == key:
                                if 'title_i18n' in elem:
                                    if cur_lang in elem['title_i18n']:
                                        if len(elem['title_i18n']
                                               [cur_lang]) > 0:
                                            elem_str = elem['title_i18n'][
                                                cur_lang]
                                else:
                                    elem_str = elem['title']

                        if elem_str != '':
                            break

                if elem_str == '':
                    elem_str = prop.get('title')

                itemtype_list.append((key, elem_str))

            mapping_name = request.args.get('mapping_type', 'jpcoar_mapping')
            jpcoar_xsd = WekoSchema.get_all()
            jpcoar_lists = {}
            for item in jpcoar_xsd:
                jpcoar_lists[item.schema_name] = json.loads(item.xsd)

            item_type_mapping = Mapping.get_record(ItemTypeID)
            return self.render(
                current_app.config['WEKO_ITEMTYPES_UI_ADMIN_MAPPING_TEMPLATE'],
                lists=lists,
                hide_mapping_prop=item_type_mapping,
                mapping_name=mapping_name,
                hide_itemtype_prop=itemtype_prop,
                jpcoar_prop_lists=remove_xsd_prefix(jpcoar_lists),
                meta_system=meta_system,
                itemtype_list=itemtype_list,
                id=ItemTypeID,
                is_system_admin=is_admin,
                lang_code=session.get('selected_language', 'en')  # Set default
            )
        except BaseException as e:
            current_app.logger.error('Unexpected error: ', e)
        return abort(400)

    @expose('', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def mapping_register(self):
        """Register an item type mapping."""
        if request.headers['Content-Type'] != 'application/json':
            current_app.logger.debug(request.headers['Content-Type'])
            return jsonify(msg=_('Header Error'))

        data = request.get_json()
        try:
            Mapping.create(item_type_id=data.get('item_type_id'),
                           mapping=data.get('mapping'))
            db.session.commit()
        except BaseException:
            db.session.rollback()
            return jsonify(msg=_('Unexpected error occurred.'))
        return jsonify(msg=_('Successfully saved new mapping.'))

    @expose('/schema', methods=['GET'])
    @expose('/schema/<string:SchemaName>', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def schema_list(self, SchemaName=None):
        """Schema list."""
        jpcoar_lists = {}
        if SchemaName is None:
            jpcoar_xsd = WekoSchema.get_all()
            for item in jpcoar_xsd:
                jpcoar_lists[item.schema_name] = json.loads(item.xsd)
        else:
            jpcoar_xsd = WekoSchema.get_record_by_name(SchemaName)
            if jpcoar_xsd is not None:
                jpcoar_lists[SchemaName] = json.loads(jpcoar_xsd.model.xsd)
        return jsonify(remove_xsd_prefix(jpcoar_lists))


class ItemImportView(BaseView):
    """ItemImportView."""

    @expose('/', methods=['GET'])
    def index(self):
        """Renders an item import view.

        :param
        :return: The rendered template.
        """
        from .config import WEKO_ITEM_ADMIN_IMPORT_TEMPLATE
        from weko_workflow.api import WorkFlow
        workflow = WorkFlow()
        workflows = workflow.get_workflow_list()
        return self.render(
            WEKO_ITEM_ADMIN_IMPORT_TEMPLATE,
            workflows=workflows
            lang_code=session.get('selected_language', 'en')  # Set default
        )


itemtype_meta_data_adminview = {
    'view_class': ItemTypeMetaDataView,
    'kwargs': {
        'category': _('Item Types'),
        'name': _('Meta'),
        'url': '/admin/itemtypes',
        'endpoint': 'itemtypesregister'
    }
}

itemtype_properties_adminview = {
    'view_class': ItemTypePropertiesView,
    'kwargs': {
        'category': _('Item Types'),
        'name': _('Properties'),
        'url': '/admin/itemtypes/properties',
        'endpoint': 'itemtypesproperties'
    }
}

itemtype_mapping_adminview = {
    'view_class': ItemTypeMappingView,
    'kwargs': {
        'category': _('Item Types'),
        'name': _('Mapping'),
        'url': '/admin/itemtypes/mapping',
        'endpoint': 'itemtypesmapping'
    }
}

item_import_adminview = {
    'view_class': ItemImportView,
    'kwargs': {
        'category': _('Items'),
        'name': _('Import'),
        'url': '/admin/items/import',
        'endpoint': 'items/import'
    }
}

__all__ = (
    'itemtype_meta_data_adminview',
    'itemtype_properties_adminview',
    'itemtype_mapping_adminview',
    'item_import_adminview'
)
