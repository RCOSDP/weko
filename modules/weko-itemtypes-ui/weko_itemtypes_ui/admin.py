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
import io
import traceback

from flask import abort, current_app, flash, json, jsonify, redirect, \
    request, session, url_for, make_response, send_file
from sqlalchemy.sql.expression import null
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_db import db
from invenio_i18n.ext import current_i18n
from weko_admin.models import AdminSettings, BillingPermission, AdminLangSettings
from weko_logging.activity_logger import UserActivityLogger
from weko_logging.models import UserActivityLog
from weko_records.api import ItemsMetadata, ItemTypeEditHistory, \
    ItemTypeNames, ItemTypeProps, ItemTypes, Mapping
from weko_records.serializers.utils import get_mapping_inactive_show_list
from weko_records_ui.models import RocrateMapping
from weko_records.api import JsonldMapping
from weko_schema_ui.api import WekoSchema
from weko_search_ui.utils import get_key_by_property
from weko_search_ui.tasks import is_import_running
from weko_workflow.api import WorkFlow

from .config import WEKO_BILLING_FILE_ACCESS, WEKO_BILLING_FILE_PROP_ATT, \
    WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES_ATT
from .permissions import item_type_permission
from .utils import check_duplicate_mapping, fix_json_schema, \
    has_system_admin_access, remove_xsd_prefix, \
    update_required_schema_not_exist_in_form, update_text_and_textarea
from zipfile import ZipFile, ZIP_DEFLATED
from marshmallow import fields, missing, post_dump, Schema
from weko_records.models import ItemType, ItemTypeName, ItemTypeMapping, ItemTypeProperty
from flask_marshmallow import Marshmallow, sqla
from marshmallow_sqlalchemy import ModelSchema, SQLAlchemyAutoSchema
from invenio_files_rest.models import FileInstance

class ItemTypeMetaDataView(BaseView):
    """ItemTypeMetaDataView."""

    @expose('/', methods=['GET'])
    @expose('/<int:item_type_id>', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def index(self, item_type_id=0):
        """Renders an item type register view.

        :param item_type_id: Item type i. Default 0.
        """
        item_type_list = ItemTypes.get_latest_with_item_type(True)
        is_sys_admin = has_system_admin_access()

        return self.render(
            current_app.config['WEKO_ITEMTYPES_UI_ADMIN_REGISTER_TEMPLATE'],
            item_type_list=item_type_list,
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
            # Get sub-property has language
            languageVsValue = []
            item_type_mapping = Mapping.get_record(item_type_id)
            item_map = get_mapping_inactive_show_list(item_type_mapping,
                                                      'jpcoar_mapping')
            suffixes = '.@attributes.xml:lang'
            for key in item_map:
                # Get sub-property by format "parrent.sub
                # Property.@attributes.xml:lang" and key.count(".") > 1
                if key.find(suffixes) != -1:
                    # get language
                    _title_key = get_key_by_property(result, item_map, key)
                    languageVsValue.append(_title_key)
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
        result['key_subproperty_languague'] = languageVsValue
        return jsonify(result)

    @expose('/delete', methods=['POST'])
    @expose('/delete/', methods=['POST'])
    @expose('/delete/<int:item_type_id>', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def delete_itemtype(self, item_type_id=0):
        """Soft-delete an item type."""
        check = is_import_running()
        if check == "is_import_running":
            flash(_('Item type cannot be deleted becase import is in progress.'), 'error')
            return jsonify(code=-1)

        if not item_type_id > 0:
            flash(_('An error has occurred.'), 'error')
            return jsonify(code=-1)

        record = ItemTypes.get_record(id_=item_type_id)
        if record is not None:
            # Check harvesting_type
            if record.model.harvesting_type:
                flash(_('Cannot delete Item type for Harvesting.'), 'error')
                return jsonify(code=-1)
            # Get all versions
            all_records = ItemTypes.get_records_by_name_id(
                name_id=record.model.name_id
            )
            # Check that item type is already registered to an item or not
            for item in all_records:
                items = ItemsMetadata.get_registered_item_metadata(
                    item_type_id=item.id)
                if len(items) > 0:
                    flash(
                        _('Cannot delete due to child existing item types.'),
                        'error'
                    )
                    return jsonify(code=-1)
            # Check that item type is used SWORD API
            jsonld_mappings = JsonldMapping.get_by_itemtype_id(item_type_id)
            for jsonld_mapping in jsonld_mappings:
                sword_clients = jsonld_mapping.sword_clients.all()
                if sword_clients:
                    current_app.logger.info("Item type is used SWORD API.")
                    flash(
                        _('Cannot delete due to SWORD API is using this item types.'),
                        'error'
                    )
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
                    current_app.logger.info(
                        f"Item type deleted: {item_type_name.name}"
                    )
                except Exception:
                    db.session.rollback()
                    exec_info = sys.exc_info()
                    tb_info = traceback.format_tb(exec_info[2])
                    current_app.logger.error(
                        "Unexpected error: {}".format(exec_info))
                    UserActivityLogger.error(
                        operation="ITEM_TYPE_DELETE",
                        target_key=item_type_id,
                        remarks=tb_info[0]
                    )
                    traceback.print_exc()
                    flash(_('Failed to delete Item type.'), 'error')
                    return jsonify(code=-1)

                for jsonld_mapping in jsonld_mappings:
                    try:
                        # Delete itemtype JOSN-LD mapping
                        JsonldMapping.delete(jsonld_mapping.id)
                        db.session.commit()
                        current_app.logger.info(
                            f"JSON-LD mapping deleted: {jsonld_mapping.name}"
                        )
                    except Exception:
                        db.session.rollback()
                        current_app.logger.error(
                            "Failed to delete Item type JSON-LD mapping: {}"
                            .format(jsonld_mapping.name)
                        )
                        traceback.print_exc()

                current_app.logger.debug(
                    'Itemtype delete: {}'.format(item_type_id))
                UserActivityLogger.info(
                    operation="ITEM_TYPE_DELETE",
                    target_key=item_type_id
                )
                flash(_('Deleted Item type successfully.'))
                return jsonify(code=0)


    @expose('/register', methods=['POST'])
    @expose('/<int:item_type_id>/register', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def register(self, item_type_id=0):
        """Register an item type."""
        if request.headers['Content-Type'] != 'application/json':
            current_app.logger.debug(request.headers['Content-Type'])
            return jsonify(msg=_('Header Error'))

        check = is_import_running()
        if check == "is_import_running":
            response = jsonify(msg=_('Item type cannot be updated becase '
                                     'import is in progress.'))
            response.status_code = 400
            return response

        data = request.get_json()
        # current_app.logger.eqrror("data:{}".format(data))
        try:
            table_row_map = data.get('table_row_map')
            json_schema = fix_json_schema(table_row_map.get('schema'))
            json_form = table_row_map.get('form')
            json_schema = update_required_schema_not_exist_in_form(
                json_schema, json_form)

            if item_type_id != 0:
                json_schema, json_form = update_text_and_textarea(
                    item_type_id, json_schema, json_form)

            if not json_schema:
                raise ValueError('Schema is in wrong format.')

            record = ItemTypes.update(id_=item_type_id,
                                      name=table_row_map.get('name'),
                                      schema=json_schema,
                                      form=table_row_map.get('form'),
                                      render=data)
            upgrade_version = current_app.config[
                'WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED'
            ]

            if not upgrade_version:
                Mapping.create(item_type_id=record.model.id,
                               mapping=table_row_map.get('mapping'))
            # Just update Mapping when create new record
            elif record.model.id != item_type_id:
                Mapping.create(item_type_id=record.model.id,
                               mapping=table_row_map.get('mapping'))
                workflow = WorkFlow()
                workflow_list = workflow.get_workflow_by_itemtype_id(
                    item_type_id)
                for wf in workflow_list:
                    workflow.update_itemtype_id(wf, record.model.id)

            ItemTypeEditHistory.create_or_update(
                item_type_id=record.model.id,
                user_id=current_user.get_id(),
                notes=data.get('edit_notes', {})
            )

            db.session.commit()
            if item_type_id == 0:
                UserActivityLogger.info(
                    operation="ITEM_TYPE_CREATE",
                    target_key=record.model.id
                )
            else:
                UserActivityLogger.info(
                    operation="ITEM_TYPE_UPDATE",
                    target_key=item_type_id
                )
            # log item type mapping and workflow
            if not upgrade_version or item_type_id != record.model.id:
                UserActivityLogger.info(
                    operation="ITEM_TYPE_MAPPING_CREATE",
                    target_key=record.model.id
                )
            else:
                UserActivityLogger.info(
                    operation="ITEM_TYPE_MAPPING_UPDATE",
                    target_key=item_type_id
                )
                workflow_list = WorkFlow().get_workflow_by_itemtype_id(item_type_id)
                for wf in workflow_list:
                    UserActivityLogger.info(
                        operation="WORKFLOW_UPDATE",
                        target_key=wf.id
                    )
        except Exception as ex:
            db.session.rollback()
            current_app.logger.error(
                f"Failed to register item type: {item_type_id}"
            )
            traceback.print_exc()
            exec_info = sys.exc_info()
            tb_info = traceback.format_tb(exec_info[2])
            if item_type_id != 0:
                UserActivityLogger.error(
                    operation="ITEM_TYPE_UPDATE",
                    target_key=item_type_id,
                    remarks=tb_info[0]
                )
            else:
                UserActivityLogger.error(
                    operation="ITEM_TYPE_CREATE",
                    remarks=tb_info[0]
                )
            default_msg = _('Failed to register Item type.')
            response = jsonify(msg='{} {}'.format(default_msg, str(ex)))
            response.status_code = 400
            return response
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
                        current_app.logger.error(
                            "Unexpected error: {}".format(sys.exc_info()))
                        traceback.print_exc()
                        return jsonify(code=-1,
                                       msg=_('Failed to restore Item type.'))

                    current_app.logger.debug(
                        'Itemtype restore: {}'.format(item_type_id))
                    return jsonify(code=0,
                                   msg=_('Restored Item type successfully.'))

        return jsonify(code=-1, msg=_('An error has occurred.'))

    @expose('/get-all-properties', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def get_property_list(self, property_id=0):
        """Renders an primitive property view."""
        lang = request.values.get('lang')

        props = ItemTypeProps.get_records([])

        billing_perm = BillingPermission.get_billing_information_by_id(
            WEKO_BILLING_FILE_ACCESS)
        if not billing_perm or not billing_perm.is_active:
            for prop in props:
                if prop.schema.get(WEKO_BILLING_FILE_PROP_ATT, None):
                    props.remove(prop)

        lists = {'system': {}}
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
            if name and name[:2] == 'S_':
                lists['system'][k.id] = tmp
            else:
                lists[k.id] = tmp

        settings = AdminSettings.get('default_properties_settings')
        default_properties = current_app.config[
            'WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES']
        if settings:
            if settings.show_flag:
                lists['defaults'] = default_properties
            else:
                lists['defaults'] = {
                    '0': {
                        'name': _('Date (Type-less）'),
                        'value': 'datetime'}}
        else:
            if current_app.config['WEKO_ITEMTYPES_UI_SHOW_DEFAULT_PROPERTIES']:
                lists['defaults'] = default_properties
            else:
                lists['defaults'] = {
                    '0': {
                        'name': _('Date (Type-less）'),
                        'value': 'datetime'}}

        return jsonify(lists)

    @expose('/<int:item_type_id>/export', methods=['GET'])
    def export(self,item_type_id):
        item_types = ItemTypes.get_by_id(id_=item_type_id)

        # 存在しないアイテムタイプ、削除済みアイテムタイプ、ハーベスト用アイテムタイプの場合はエクスポート不可。エラー画面を表示する。
        if item_types is None or item_types.harvesting_type is True :
            current_app.logger.error('item_type_id={} is cannot export.'.format(item_type_id))
            return self.render(
                    current_app.config['WEKO_ITEMTYPE'
                                       'S_UI_ADMIN_ERROR_TEMPLATE']
                )

        item_type_properties = ItemTypeProps.get_records([])
        item_type_names = ItemTypeNames.get_record(id_=item_types.name_id)
        item_type_mappings = Mapping.get_record(item_type_id)
        fp = io.BytesIO()
        with ZipFile(fp, 'w', compression=ZIP_DEFLATED) as new_zip:
            # zipファイルにJSON文字列を追加
            new_zip.writestr("ItemType.json", ItemTypeSchema().dumps(item_types).data.encode().decode('unicode-escape').encode())
            new_zip.writestr("ItemTypeName.json", ItemTypeNameSchema().dumps(item_type_names).data.encode().decode('unicode-escape').encode())
            new_zip.writestr("ItemTypeMapping.json", ItemTypeMappingSchema().dumps(item_type_mappings.model).data.encode().decode('unicode-escape').encode())
            json_str = ""
            for item_type_property in item_type_properties :
                prop_str = ItemTypePropertySchema().dumps(item_type_property).data
                if len(json_str) > 0:
                    json_str += ","
                json_str += prop_str
            json_str = "[" + json_str + "]"
            new_zip.writestr("ItemTypeProperty.json", json_str.encode().decode('unicode-escape').encode())
        fp.seek(0)
        return send_file(
            fp ,
            mimetype = 'application/zip' ,
            attachment_filename ='ItemType_export.zip' ,
            as_attachment = True
        )

    @expose('/import', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def item_type_import(self):
        """Import item type."""
        item_type_id = 0

        # Get request data
        item_type_name = request.form['item_type_name']
        input_file = request.files['file']
        if len(item_type_name) == 0:
            return jsonify(msg=_('No item type name Error'))
        if input_file is None:
            return jsonify(msg=_('No file Error'))
        if input_file.mimetype is None:
            current_app.logger.debug(input_file.mimetype)
            return jsonify(msg=_('Illegal mimetype Error'))

        # Issue log group ID
        if not UserActivityLogger.issue_log_group_id(db.session):
            current_app.logger.error('Failed to issue log group ID.')
            return jsonify(msg=_('Failed to issue log group ID.'))

        try:
            readable_files = ["ItemType.json", "ItemTypeName.json", "ItemTypeMapping.json", "ItemTypeProperty.json"]
            import_data = {
                "ItemType":null,
                "ItemTypeName":null,
                "ItemTypeMapping":null,
                "ItemTypeProperty":null,
            }
            with ZipFile(input_file, 'r') as import_zip:
                # Check JSON files in ZipFile
                current_app.logger.debug("Unzip requested file...")
                for file_name in import_zip.namelist():
                    current_app.logger.debug("Read file:" + file_name)
                    if file_name not in readable_files:
                        current_app.logger.debug(file_name + " is ignored.")
                    else:
                        with import_zip.open(file_name, 'r') as json_file:
                            json_obj = json.load(json_file)
                            if file_name == "ItemType.json":
                                import_data["ItemType"] = json_obj
                                #print(json_obj)
                            elif file_name == "ItemTypeName.json":
                                import_data["ItemTypeName"] = json_obj
                                #print(json_obj)
                            elif file_name == "ItemTypeMapping.json":
                                import_data["ItemTypeMapping"] = json_obj
                                #print(json_obj)
                            elif file_name == "ItemTypeProperty.json":
                                import_data["ItemTypeProperty"] = json_obj
                                #print(json_obj)

            # ZIPファイル内に規定のアイテムタイプデータが無ければエラー
            if import_data["ItemType"] is null or import_data["ItemTypeName"] is null or import_data["ItemTypeMapping"] is null or import_data["ItemTypeProperty"] is null :
                raise ValueError('Zip file contents invalid.')


            json_schema = fix_json_schema(import_data["ItemType"].get('schema'))
            json_form = import_data["ItemType"].get('form')
            json_schema = update_required_schema_not_exist_in_form(
                json_schema, json_form)

            if not json_schema:
                raise ValueError('Schema is in wrong format.')

            record = ItemTypes.update(id_=0,
                                      name=item_type_name,
                                      schema=json_schema,
                                      form=json_form,
                                      render=import_data["ItemType"].get('render'))
            upgrade_version = current_app.config[
                'WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED'
            ]
            item_type_id=record.model.id
            Mapping.create(item_type_id=item_type_id,
                               mapping=import_data["ItemTypeMapping"].get('mapping'))

            ItemTypeEditHistory.create_or_update(
                item_type_id=item_type_id,
                user_id=current_user.get_id(),
                notes={}
            )

            db.session.commit()
            UserActivityLogger.info(
                operation="ITEM_TYPE_CREATE",
                target_key=item_type_id
            )
            # log item type mapping and workflow
            UserActivityLogger.info(
                operation="ITEM_TYPE_MAPPING_CREATE",
                target_key=item_type_id
            )
        except Exception as ex:
            db.session.rollback()
            traceback.print_exc()
            default_msg = _('Failed to import Item type.')
            response = jsonify(msg='{} {}'.format(default_msg, str(ex)))
            response.status_code = 400
            return response
        current_app.logger.debug('itemtype import: {}'.format(item_type_id))
        flash(_('Successfuly import Item type.'))
        redirect_url = url_for('.index', item_type_id=item_type_id)
        return jsonify(msg=_('Successfuly import Item type.'),
                       redirect_url=redirect_url)

class ItemTypeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ItemType

class ItemTypeNameSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ItemTypeName

class ItemTypeMappingSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ItemTypeMapping

class ItemTypePropertySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ItemTypeProperty


class ItemTypePropertiesView(BaseView):
    """ItemTypePropertiesView."""

    @expose('/', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def index(self, property_id=0):
        """Renders an primitive property view."""
        lists = ItemTypeProps.get_records([])

        # remove default properties
        properties = lists.copy()
        defaults_property_ids = [prop.id for prop in lists if
                                 prop.schema.get(
                                     WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES_ATT,
                                     None)]
        for item in lists:
            if item.id in defaults_property_ids:
                properties.remove(item)

        billing_perm = BillingPermission.get_billing_information_by_id(
            WEKO_BILLING_FILE_ACCESS)
        if not billing_perm or not billing_perm.is_active:
            for prop in properties:
                if prop.schema.get(WEKO_BILLING_FILE_PROP_ATT, None):
                    properties.remove(prop)

        return self.render(
            current_app.config['WEKO_ITEMTYPES_UI_ADMIN_CREATE_PROPERTY'],
            lists=properties,
            lang_code=session.get('selected_language', 'en')  # Set default
        )

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
        current_app.logger.error("ItemTypeID:{}".format(ItemTypeID))
        try:
            lists = ItemTypes.get_latest()  # ItemTypes.get_all()
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

            meta_system_items = ['system_identifier_doi',
                                 'system_identifier_hdl',
                                 'system_identifier_uri',
                                 'system_file',
                                 'updated_date', 'created_date',
                                 'persistent_identifier_doi',
                                 'persistent_identifier_h',
                                 'ranking_page_url', 'belonging_index_info']

            for key in meta_system_items:
                if isinstance(meta_system, dict) and meta_system.get(key) \
                        and isinstance(meta_system[key], dict):
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
                                    elem_str = elem.get('title', '')
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
            if item_type_mapping is None:
                current_app.logger.error("item_type_mapping is None.")
                item_type_mapping = {}

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
        except BaseException:
            current_app.logger.error(traceback.format_exc())
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
        return abort(400)

    @expose('', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def mapping_register(self):
        """Register an item type mapping."""
        if request.headers['Content-Type'] != 'application/json':
            current_app.logger.debug(request.headers['Content-Type'])
            return jsonify(msg=_('Header Error'))

        data = request.get_json()
        # current_app.logger.debug("data:{}".format(data))
        item_type = ItemTypes.get_by_id(data.get('item_type_id'))
        meta_system = item_type.render.get('meta_system')
        mapping_type = data.get('mapping_type')
        data_mapping = data.get('mapping')
        lst_duplicate = check_duplicate_mapping(
            data_mapping, meta_system, item_type, mapping_type)
        if len(lst_duplicate) > 0:
            return jsonify(duplicate=True, err_items=lst_duplicate,
                           msg=_('Duplicate mapping as below:'))
        try:
            Mapping.create(item_type_id=data.get('item_type_id'),
                           mapping=data_mapping)
            db.session.commit()
            UserActivityLogger.info(
                operation="ITEM_TYPE_MAPPING_UPDATE",
                target_key=data.get('item_type_id')
            )
        except BaseException:
            db.session.rollback()
            current_app.logger.error(
                "Unexpected error: {}".format(sys.exc_info()))
            exec_info = sys.exc_info()
            tb_info = traceback.format_tb(exec_info[2])
            UserActivityLogger.error(
                operation="ITEM_TYPE_MAPPING_UPDATE",
                target_key=data.get('item_type_id'),
                remarks=tb_info[0]
            )
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


class ItemTypeRocrateMappingView(BaseView):
    @expose('/', methods=['GET'])
    @expose('/<int:item_type_id>', methods=['GET'])
    @item_type_permission.require(http_exception=403)
    def index(self, item_type_id=0):
        """Renders an item type mapping view.

        :param item_type_id: Item type ID. (Default: 0)
        :return: The rendered template.
        """
        current_app.logger.info('ItemTypeID:{}'.format(item_type_id))
        try:
            item_type_names = ItemTypes.get_latest()  # ItemTypes.get_all()
            if item_type_names is None or len(item_type_names) == 0:
                return self.render(
                    current_app.config['WEKO_ITEMTYPES_UI_ADMIN_ERROR_TEMPLATE']
                )
            item_type = ItemTypes.get_by_id(item_type_id)
            if item_type is None:
                current_app.logger.info(item_type_names[0].item_type[0])
                return redirect(url_for('itemtypesrocratemapping.index', item_type_id=item_type_names[0].item_type[0].id))

            item_properties = self._get_item_properties(item_type)
            record = RocrateMapping.query.filter_by(item_type_id=item_type_id).one_or_none()
            rocrate_mapping = record.mapping if record is not None else ''

            registered_languages = AdminLangSettings.get_registered_language()

        except BaseException:
            current_app.logger.error('Unexpected error: {}'.format(sys.exc_info()))
            abort(500)

        return self.render(
            current_app.config['WEKO_ITEMTYPES_UI_ADMIN_ROCRATE_MAPPING_TEMPLATE'],
            item_type_id=item_type_id,
            item_type_names=item_type_names,
            item_properties=item_properties,
            rocrate_mapping=rocrate_mapping,
            rocrate_dataset_properties=current_app.config['WEKO_ITEMTYPES_UI_DATASET_PROPERTIES'],
            rocrate_file_properties=current_app.config['WEKO_ITEMTYPES_UI_FILE_PROPERTIES'],
            registered_languages=registered_languages,
        )

    @expose('', methods=['POST'])
    @item_type_permission.require(http_exception=403)
    def register(self):
        """Register an item type mapping."""
        if request.headers['Content-Type'] != 'application/json':
            current_app.logger.debug(request.headers['Content-Type'])
            abort(400)

        try:
            data = request.get_json()
            item_type_id = data.get('item_type_id')
            mapping = data.get('mapping')

            with db.session.begin_nested():
                record = RocrateMapping.query.filter_by(item_type_id=item_type_id).one_or_none()
                if record is None:
                    # Create data
                    record = RocrateMapping(item_type_id, mapping)
                    db.session.add(record)
                else:
                    # Update data
                    record.mapping = mapping
            db.session.commit()

        except BaseException:
            db.session.rollback()
            current_app.logger.error('Unexpected error: {}'.format(sys.exc_info()))
            abort(500)

        return jsonify(msg=_('Successfully saved new mapping.'))

    def _get_item_properties(self, item_type):
        schema_props = item_type.schema.get('properties')
        cur_lang = current_i18n.language

        keys = ['pubdate']
        render_table_row = item_type.render.get('table_row')
        if isinstance(render_table_row, list):
            keys.extend(render_table_row)

        item_properties = {}
        for key in keys:
            schema_prop = schema_props.get(key)
            form_key = [key]
            form_prop = self._get_child_form_prop(item_type.form, form_key)

            item_properties[key] = self._get_item_property(schema_prop, form_key, form_prop, cur_lang)

        return item_properties

    def _get_item_property(self, schema_prop, form_key, form_prop, cur_lang):
        item_property = {}
        title = self._get_title(schema_prop, form_prop, cur_lang)
        item_property['title'] = title
        type = schema_prop.get('type')
        if type == 'string' or type == ["null", "string"]:
            item_property['type'] = 'string'

        elif type == 'object':
            item_property['type'] = 'object'
            item_property['properties'] = {}

            for child_key, child_schema_prop in schema_prop.get('properties').items():
                child_form_key = form_key + [child_key]
                child_form_prop = self._get_child_form_prop(form_prop.get('items', []), child_form_key)

                item_property['properties'][child_key] = self._get_item_property(child_schema_prop, child_form_key, child_form_prop, cur_lang)

        elif type == 'array':
            item_property['type'] = 'array'
            item_property['properties'] = {}

            for child_key, child_schema_prop in schema_prop.get('items').get('properties').items():
                child_form_key = form_key + [child_key]
                child_form_prop = self._get_child_form_prop(form_prop.get('items', []), child_form_key)

                item_property['properties'][child_key] = self._get_item_property(child_schema_prop, child_form_key, child_form_prop, cur_lang)

        return item_property

    def _get_title(self, schema_prop, form_prop, cur_lang):
        title = ''
        if 'default' != cur_lang:
            if 'title_i18n' in schema_prop:
                if cur_lang in schema_prop['title_i18n']:
                    title = schema_prop['title_i18n'][cur_lang]
            else:
                if form_prop:
                    if 'title_i18n' in form_prop:
                        if cur_lang in form_prop['title_i18n']:
                            title = form_prop['title_i18n'][cur_lang]

        if title == '':
            title = schema_prop.get('title')

        return title

    def _get_child_form_prop(self, forms, form_key):
        target = {}
        for form in forms:
            if 'key' not in form:
                continue
            if self._check_form_key(form['key'], form_key):
                target = form
                break
        return target

    def _check_form_key(self, form_key, schema_keys):
        form_keys = form_key.split('.')
        if len(form_keys) != len(schema_keys):
            return False
        for index, key_name in enumerate(form_keys):
            key_name = key_name.split('[')[0]
            if schema_keys[index] != key_name:
                return False
        return True


itemtype_meta_data_adminview = {
    'view_class': ItemTypeMetaDataView,
    'kwargs': {
        'category': _('Item Types'),
        'name': _('Metadata'),
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

itemtype_rocrate_mapping_adminview = {
    'view_class': ItemTypeRocrateMappingView,
    'kwargs': {
        'category': _('Item Types'),
        'name': _('RO-Crate Mapping'),
        'url': '/admin/itemtypes/rocrate_mapping',
        'endpoint': 'itemtypesrocratemapping'
    }
}

__all__ = (
    'itemtype_meta_data_adminview',
    'itemtype_properties_adminview',
    'itemtype_mapping_adminview',
    'itemtype_rocrate_mapping_adminview',
)
