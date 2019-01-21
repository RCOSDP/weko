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

"""Configuration for weko-records-ui."""

WEKO_RECORDS_UI_DETAIL_TEMPLATE = 'weko_records_ui/detail.html'
WEKO_RECORDS_UI_BASE_TEMPLATE = 'weko_theme/page.html'

WEKO_PERMISSION_ROLE_USER = ('System Administrator',
                             'Repository Administrator',
                             'Contributor',
                             'General')

ADMIN_SET_ITEM_TEMPLATE = 'weko_records_ui/admin/item_setting.html'
# author setting page template

ITEM_SEARCH_FLG = 'name'
# setting author name search type: name or id

EMAIL_DISPLAY_FLG = True
# setting the email of author if display

RECORDS_UI_ENDPOINTS = dict(
    recid=dict(
        pid_type='recid',
        route='/records/<pid_value>',
        view_imp='weko_records_ui.views.default_view_method',
        template='weko_records_ui/detail.html',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
    ),
    recid_export=dict(
        pid_type='recid',
        route='/records/<pid_value>/export/<format>',
        view_imp='weko_records_ui.views.export',
        template='weko_records_ui/export.html',
        record_class='weko_deposit.api:WekoRecord',
    ),
    recid_files=dict(
        pid_type='recid',
        route='/record/<pid_value>/files/<path:filename>',
        view_imp='weko_records_ui.fd.file_download_ui',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
    ),
    recid_file_preview=dict(
        pid_type='recid',
        route='/record/<pid_value>/file_preview/<path:filename>',
        view_imp='weko_records_ui.fd.file_preview_ui',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
    ),
    recid_preview=dict(
        pid_type='recid',
        route='/record/<pid_value>/preview/<path:filename>',
        view_imp='weko_records_ui.preview.preview',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_records_ui.permissions'
                               ':page_permission_factory',
    ),
    recid_publish=dict(
        pid_type='recid',
        route='/record/<pid_value>/publish',
        view_imp='weko_records_ui.views.publish',
        template='weko_records_ui/detail.html',
        record_class='weko_deposit.api:WekoRecord',
        permission_factory_imp='weko_items_ui.permissions'
                               ':edit_permission_factory',
        methods=['POST'],
    ),
)

RECORDS_UI_EXPORT_FORMATS = {
    'recid': {
        'junii2': dict(
            title='junii2',
            serializer='weko_schema_ui.serializers.WekoCommonSchema',
            order=1,
        ),
        'jpcoar': dict(
            title='JPCOAR',
            serializer='weko_schema_ui.serializers.WekoCommonSchema',
            order=2,
        ),
        'oai_dc': dict(
            title='DublinCore',
            serializer='weko_schema_ui.serializers.WekoCommonSchema',
            order=3,
        ),
        'json': dict(
            title='JSON',
            serializer='invenio_records_rest.serializers.json_v1',
            order=4,
        ),
        'bibtex': dict(
            title='BIBTEX',
            serializer='weko_schema_ui.serializers.BibTexSerializer',
            order=5,
        ),
    }
}

OAISERVER_METADATA_FORMATS = {
    'junii2': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'junii2',
            }
        ),
        'schema': 'http://irdb.nii.ac.jp/oai/junii2-3-1.xsd',
        'namespace': 'http://irdb.nii.ac.jp/oai',
    },
    'jpcoar': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'jpcoar',
            }
        ),
        'namespace': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/',
        'schema': 'https://irdb.nii.ac.jp/schema/jpcoar/1.0/jpcoar_scm.xsd',
    },
    'oai_dc': {
        'serializer': (
            'weko_schema_ui.utils:dumps_oai_etree', {
                'schema_type': 'oai_dc',
            }
        ),
        'namespace': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'schema': 'http://www.openarchives.org/OAI/2.0/oai_dc.xsd',
    }
}
