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
from .utils import remove_xsd_prefix


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
        for list in lists:
            # Get all versions
            all_records = ItemTypes.get_records_by_name_id(name_id=list.id)
            list.belonging_item_flg = False
            for item in all_records:
                metaDataRecords = ItemsMetadata.get_by_item_type_id(
                    item_type_id=item.id)
                list.belonging_item_flg = len(metaDataRecords) > 0
                if list.belonging_item_flg:
                    break

        return self.render(
            current_app.config['WEKO_ITEMTYPES_UI_ADMIN_REGISTER_TEMPLATE'],
            lists=lists,
            id=item_type_id,
            lang_code=session.get('selected_language', 'en')  # Set default
        )

    @expose('/<int:item_type_id>/render', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def render_itemtype(self, item_type_id=0):
        """Renderer."""
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
                    flash(_('Cannot delete Item type for Harvesting.'), 'error')
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
                            _('Cannot delete due to child existing item types.'), 'error')
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
            record = ItemTypes.update(id_=item_type_id,
                                      name=data.get(
                                          'table_row_map').get('name'),
                                      schema=data.get('table_row_map').get(
                                          'schema'),
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
                    lang in k.form['title_i18n'] and k.form['title_i18n'][lang]:
                name = k.form['title_i18n'][lang]

            tmp = {'name': name, 'schema': k.schema, 'form': k.form,
                   'forms': k.forms, 'sort': k.sort}
            lists[k.id] = tmp

        lists['defaults'] = current_app.config['WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES']

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
                    current_app.config['WEKO_ITEMTYPES_UI_ADMIN_ERROR_TEMPLATE']
                )
            item_type = ItemTypes.get_by_id(ItemTypeID)
            if item_type is None:
                current_app.logger.info(lists[0].item_type[0])
                return redirect(url_for('itemtypesmapping.index',
                                        ItemTypeID=lists[0].item_type[0].id))
            itemtype_list = []
            itemtype_prop = item_type.schema.get('properties')
            table_rows = ['pubdate']
            render_table_row = item_type.render.get('table_row')
            if isinstance(render_table_row, list):
                table_rows.extend(render_table_row)
            for key in table_rows:
                prop = itemtype_prop.get(key)
                cur_lang = current_i18n.language
                schema_form = item_type.form
                elemStr = ''
                if 'default' != cur_lang:
                    for elem in schema_form:
                        if 'items' in elem:
                            for sub_elem in elem['items']:
                                if 'key' in sub_elem and sub_elem['key'] == key:
                                    if 'title_i18n' in sub_elem:
                                        if cur_lang in sub_elem['title_i18n']:
                                            if len(
                                                    sub_elem['title_i18n'][cur_lang]) > 0:
                                                elemStr = sub_elem['title_i18n'][
                                                    cur_lang]
                                    else:
                                        elemStr = sub_elem['title']
                                    break
                        else:
                            if elem['key'] == key:
                                if 'title_i18n' in elem:
                                    if cur_lang in elem['title_i18n']:
                                        if len(elem['title_i18n']
                                               [cur_lang]) > 0:
                                            elemStr = elem['title_i18n'][
                                                cur_lang]
                                else:
                                    elemStr = elem['title']

                        if elemStr != '':
                            break

                if elemStr == '':
                    elemStr = prop.get('title')

                itemtype_list.append((key, elemStr))

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
                itemtype_list=itemtype_list,
                id=ItemTypeID,
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

__all__ = (
    'itemtype_meta_data_adminview',
    'itemtype_properties_adminview',
    'itemtype_mapping_adminview',
)
