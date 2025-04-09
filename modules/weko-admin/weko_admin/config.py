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

"""Configuration for weko-admin."""

from flask_babelex import gettext as _

WEKO_ADMIN_DEFAULT_AGGREGATION_MONTH = 2
"""default aggregation month for site license mail."""

WEKO_ADMIN_DEFAULT_LIFETIME = 60
""" Session time out setting, default 60 minutes """

WEKO_ADMIN_IMPORT_PAGE_LIFETIME = 43200
""" Session time out setting in import page, default 43200 seconds (12 hours) """

WEKO_ADMIN_BASE_TEMPLATE = 'weko_admin/base.html'
"""Base template for weko-admin module."""

WEKO_ADMIN_SETTINGS_TEMPLATE = None
"""Settings base template for weko-admin module."""

WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS = 'elastic_reindex_settings'
"""admin_settings record name"""
WEKO_ADMIN_SETTINGS_ELASTIC_REINDEX_SETTINGS_HAS_ERRORED = 'has_errored'
"""a json property name of admin_settings record 'lastic_reindex_settings'"""

WEKO_ADMIN_LIFETIME_TEMPLATE = 'weko_admin/settings/lifetime.html'
"""Settings base template for weko-admin module."""

WEKO_ADMIN_SITE_LICENSE_TEMPLATE = 'weko_admin/admin/site_license_settings.html'
"""Site-license template."""

WEKO_ADMIN_SITE_LICENSE_SEND_MAIL_TEMPLATE = 'weko_admin/admin/site_license_send_mail_settings.html'
"""Site-license send mail settings templates."""

WEKO_ADMIN_SWORD_API_TEMPLATE = 'weko_admin/admin/sword_api_settings.html'
"""SWORD API template."""

WEKO_ADMIN_SWORD_API_JSONLD_TEMPLATE = 'weko_admin/admin/sword_api_jsonld_settings.html'
"""SWORD API JSONLD template."""

WEKO_ADMIN_SWORD_API_JSONLD_MAPPING_TEMPLATE = 'weko_admin/admin/jsonld_mapping_settings.html'
"""SWORD API JSONLD template."""

WEKO_ADMIN_BlOCK_STYLE_TEMPLATE = 'weko_admin/admin/block_style.html'
"""Block-style template."""

WEKO_ADMIN_REPORT_TEMPLATE = 'weko_admin/admin/report.html'
"""Report template."""

WEKO_ADMIN_STATS_SETTINGS_TEMPLATE = 'weko_admin/admin/stats_settings.html'
"""Stats Settings template."""

WEKO_ADMIN_LOG_ANALYSIS_SETTINGS_TEMPLATE = \
    'weko_admin/admin/log_analysis_settings.html'
"""Stats Settings template."""

WEKO_ADMIN_LANG_SETTINGS = 'weko_admin/admin/lang_settings.html'
"""Language template."""

WEKO_ADMIN_FEEDBACK_MAIL = 'weko_admin/admin/feedback_mail.html'
"""Language template."""

WEKO_ADMIN_REINDEX_ELASTICSEARCH_TEMPLATE = 'weko_admin/admin/reindex_elasticsearch.html'
"""reindex elasticSearch template."""

WEKO_ADMIN_WEB_API_ACCOUNT = 'weko_admin/admin/web_api_account.html'
"""Web Api Account template."""

WEKO_ADMIN_SEARCH_MANAGEMENT_TEMPLATE = \
    'weko_admin/admin/search_management_settings.html'
"""Site-license template."""

WEKO_ADMIN_RANKING_SETTINGS_TEMPLATE = 'weko_admin/admin/ranking_settings.html'
"""Ranking Settings template."""

WEKO_ADMIN_FILE_PREVIEW_SETTINGS_TEMPLATE = \
    'weko_admin/admin/file_preview_settings.html'
"""File Preview Settings template."""

WEKO_ADMIN_ITEM_EXPORT_SETTINGS_TEMPLATE = \
    'weko_admin/admin/item_export_settings.html'
"""Item Export Settings template."""

WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS_TEMPLATE = 'weko_admin/admin/restricted_access_settings.html'
"""Restricted Access Settings template."""

LOGO_ALLOWED_EXTENSIONS = set(['png', 'jpeg', 'jpg'])

WEKO_ADMIN_CROSSREF_API_URL = 'https://doi.crossref.org/'
"""URL of CrossRef API."""

WEKO_ADMIN_FEEDBACK_MAIL_NUM_OF_PAGE = 10
"""Numbers result per page in weko admin feedback mail"""

WEKO_ADMIN_ENDPOINT = 'openurl'
"""Endpoint to concate URL of CrossRef API."""

WEKO_ADMIN_TEST_DOI = '&id=doi:10.1047/0003-066X.59.1.29'
"""DOI for check Certificate valid or not."""

WEKO_ADMIN_FORMAT = '&format=json'
"""Format of CrossRef Certificate."""

WEKO_ADMIN_VALIDATION_MESSAGE = 'The login you supplied is not recognized'
"""Validate message of certificate."""

WEKO_ADMIN_DISPLAY_FILE_STATS = True  # TODO: Delete if not used
"""Display record stats or not."""

WEKO_ADMIN_SITE_INFO = 'weko_admin/admin/site_info.html'
"""Site info template."""

WEKO_ADMIN_DEFAULT_CRAWLER_LISTS = [
    'https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_ip_blacklist.txt',
    'https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_useragent.txt']
"""Default crawler files for restricting IP addresses and user agents."""

WEKO_ADMIN_REPORT_FREQUENCIES = ['daily', 'weekly', 'monthly']
"""Email schedule frequency options."""

WEKO_ADMIN_REPORT_DELIVERY_SCHED = {
    'frequency': 'daily', 'details': '', 'enabled': False
}
"""Default report email delivery schedule."""

WEKO_ADMIN_CACHE_PREFIX = 'admin_cache_{name}_{user_id}'
"""Redis cache."""

WEKO_ADMIN_OUTPUT_FORMAT = 'tsv'
"""Output file format."""

WEKO_ADMIN_REPORT_HEADERS = {
    'file_download': _('No. Of File Downloads'),
    'file_preview': _('No. Of File Previews'),
    'billing_file_download': _('No. Of Paid File Downloads'),
    'billing_file_preview': _('No. Of Paid File Previews'),
    'index_access': _('Detail Views Per Index'),
    'detail_view': _('Detail Views Count'),
    'file_using_per_user': _('Usage Count By User'),
    'search_count': _('Search Keyword Ranking'),
    'top_page_access': _('Number Of Access By Host'),
    'user_roles': _('User Affiliation Information'),
    'site_access': _('Access Count By Site License')
}
"""Headers for the report .csv files"""

WEKO_ADMIN_REPORT_SUB_HEADERS = {
    'file_download': _('Open-Access No. Of File Downloads'),
    'file_preview': _('Open-Access No. Of File Previews'),
    'site_access': _('Access Number Breakdown By Site License')
}
"""Sub-Headers for the report .csv files"""

WEKO_ADMIN_REPORT_COLS = {
    'file_download': [
        _('File Name'), _('Registered Index Name'),
        _('No. Of Times Downloaded'), _('Non-Logged In User'),
        _('Logged In User'), _('Site License'), _('Admin'),
        _('Registrar')],
    'file_preview': [
        _('File Name'), _('Registered Index Name'),
        _('No. Of Times Viewed'), _('Non-Logged In User'),
        _('Logged In User'), _('Site License'), _('Admin'),
        _('Registrar')],
    'index_access': [_('Index'), _('No. Of Views')],
    'detail_view': [
        _('Title'), _('Registered Index Name'), _('View Count'),
        _('Non-logged-in User')],
    'file_using_per_user': [_('Mail address'),
                            _('Username'),
                            _('File download count'),
                            _('File playing count')],
    'search_count': [_('Search Keyword'), _('Number Of Searches')],
    'top_page_access': [_('Host'), _('IP Address'),
                        _('WEKO Top Page Access Count')],
    'user_roles': [_('Role'), _('Number Of Users')],
    'site_access': [_('WEKO Top Page Access Count'),
                    _('Number Of Searches'), _('Number Of Views'),
                    _('Number Of File download'),
                    _('Number Of File Regeneration')]
}
"""Columns for the report .csv files"""

WEKO_ADMIN_REPORT_FILE_NAMES = {
    'file_download': _('FileDownload_'),
    'file_preview': _('FilePreview_'),
    'billing_file_download': _('PayFileDownload_'),
    'billing_file_preview': _('PayFilePreview_'),
    'index_access': _('IndexAccess_'),
    'detail_view': _('DetailView_'),
    'file_using_per_user': _('FileUsingPerUser_'),
    'search_count': _('SearchCount_'),
    'user_roles': _('UserAffiliate_'),
    'site_access': _('SiteAccess_'),
    'top_page_access': _('TopPageAccess_'),
}
"""File names for the report .csv files"""

WEKO_ADMIN_REPORT_EMAIL_TEMPLATE = 'weko_admin/email_templates/report.html'
"""Template for sending report email."""

# Search management json

WEKO_ADMIN_MANAGEMENT_OPTIONS = {
    'dlt_dis_num_options': [
        {'id': '20', 'contents': '20'},
        {'id': '50', 'contents': '50'},
        {'id': '75', 'contents': '75'},
        {'id': '100', 'contents': '100'}
    ],
    'dlt_dis_num_selected': '20',
    'dlt_index_sort_options': [
        {'id': 'wtl_asc', 'contents': 'Title(asc)', 'disableFlg': False},
        {'id': 'wtl_desc', 'contents': 'Title(desc)', 'disableFlg': False},
        {'id': 'creator_asc', 'contents': 'Creator(asc)', 'disableFlg': False},
        {'id': 'creator_desc',
         'contents': 'Creator(desc)',
         'disableFlg': False},
        {'id': 'itemType_asc',
         'contents': 'Item Type(asc)',
         'disableFlg': False},
        {'id': 'itemType_desc',
         'contents': 'Item Type(desc)',
         'disableFlg': False},
        {'id': 'controlnumber_asc',
         'contents': 'ID(asc)',
         'disableFlg': False},
        {'id': 'controlnumber_desc',
         'contents': 'ID(desc)',
         'disableFlg': False},
        {'id': 'upd_asc', 'contents': 'Update(asc)', 'disableFlg': False},
        {'id': 'upd_desc', 'contents': 'Update(desc)', 'disableFlg': False},
        {'id': 'createdate_asc',
         'contents': 'Create(asc)',
         'disableFlg': False},
        {'id': 'createdate_desc',
         'contents': 'Create(desc)',
         'disableFlg': False},
        {'id': 'pyear_asc',
         'contents': 'Date Of Issued(asc)',
         'disableFlg': False},
        {'id': 'pyear_desc',
         'contents': 'Date Of Issued(desc)',
         'disableFlg': False},
        {'id': 'custom_sort_asc',
         'contents': 'Custom(asc)',
         'disableFlg': False},
        {'id': 'custom_sort_desc',
         'contents': 'Custom(desc)',
         'disableFlg': False},
        {'id': 'relevance_asc',
         'contents': 'Relevance(asc)',
         'disableFlg': False},
        {'id': 'relevance_desc',
         'contents': 'Relevance(desc)',
         'disableFlg': False},
        {'id': 'temporal_asc',
         'contents': 'Temporal(asc)',
         'disableFlg': False},
        {'id': 'temporal_desc',
         'contents': 'Temporal(desc)',
         'disableFlg': False},
    ],
    'dlt_index_sort_selected': 'controlnumber_asc',
    'dlt_keyword_sort_options': [
        {'id': 'wtl_asc', 'contents': 'Title(asc)', 'disableFlg': False},
        {'id': 'wtl_desc', 'contents': 'Title(desc)', 'disableFlg': False},
        {'id': 'creator_asc', 'contents': 'Creator(asc)', 'disableFlg': False},
        {'id': 'creator_desc',
         'contents': 'Creator(desc)',
         'disableFlg': False},
        {'id': 'itemType_asc',
         'contents': 'Item Type(asc)',
         'disableFlg': False},
        {'id': 'itemType_desc',
         'contents': 'Item Type(desc)',
         'disableFlg': False},
        {'id': 'controlnumber_asc',
         'contents': 'ID(asc)',
         'disableFlg': False},
        {'id': 'controlnumber_desc',
         'contents': 'ID(desc)',
         'disableFlg': False},
        {'id': 'upd_asc', 'contents': 'Update(asc)', 'disableFlg': False},
        {'id': 'upd_desc', 'contents': 'Update(desc)', 'disableFlg': False},
        {'id': 'createdate_asc',
         'contents': 'Create(asc)',
         'disableFlg': False},
        {'id': 'createdate_desc',
         'contents': 'Create(desc)',
         'disableFlg': False},
        {'id': 'pyear_asc',
         'contents': 'Date Of Issued(asc)',
         'disableFlg': False},
        {'id': 'pyear_desc',
         'contents': 'Date Of Issued(desc)',
         'disableFlg': False},
        {'id': 'custom_sort_asc',
         'contents': 'Custom(asc)',
         'disableFlg': False},
        {'id': 'custom_sort_desc',
         'contents': 'Custom(desc)',
         'disableFlg': False},
        {'id': 'relevance_asc',
         'contents': 'Relevance(asc)',
         'disableFlg': False},
        {'id': 'relevance_desc',
         'contents': 'Relevance(desc)',
         'disableFlg': False},
        {'id': 'temporal_asc',
         'contents': 'Temporal(asc)',
         'disableFlg': False},
        {'id': 'temporal_desc',
         'contents': 'Temporal(desc)',
         'disableFlg': False},
    ],
    'dlt_keyword_sort_selected': 'createdate_desc',
    'sort_options': {
        'deny': [],
        'allow': [
            {'id': 'wtl_asc', 'contents': 'Title(asc/desc)'},
            {'id': 'creator_asc', 'contents': 'Creator(asc/desc)'},
            {'id': 'itemType_asc', 'contents': 'ItemType(asc/desc)'},
            {'id': 'controlnumber_asc', 'contents': 'ID(asc/desc)'},
            {'id': 'upd_asc', 'contents': 'Update(asc/desc)'},
            {'id': 'createdate_asc', 'contents': 'Create(asc/desc)'},
            {'id': 'pyear_asc', 'contents': 'Date Of Issued(asc/desc)'},
            {'id': 'custom_sort_asc', 'contents': 'Custom(asc/desc)'},
            {'id': 'relevance_asc', 'contents': 'Relevance(asc/desc)'},
            {'id': 'temporal_asc', 'contents': 'Temporal(asc/desc)'},
        ]
    },
    'display_control': {
        'display_index_tree': {
            'id': 'display_index_tree',
            'status': True
        },
        'display_facet_search': {
            'id': 'display_facet_search',
            'status': False
        },
        'display_community': {
            'id': 'display_community',
            'status': False
        }
    },
    'init_disp_setting': {
        'init_disp_screen_setting': '0',
        'init_disp_index_disp_method': '0',
        'init_disp_index': ''
    },

    'detail_condition': [
        {'id': 'title',
         'contents': '',
         'contents_value': {'en': 'Title', 'ja': 'タイトル'},
         'useable_status': True,
         'mapping': ['title'],
         'sche_or_attr':[{'id': 'title',
                          'contents': 'title',
                          'checkStus': False}],
         'default_display': True,
         'inputType': 'text',
         'inputVal': '',
         'mappingFlg': False,
         'mappingName': ''},
        {'id': 'creator',
         'contents': '',
         'contents_value': {'en': 'Author Name', 'ja': '著者名'},
         'useable_status': True,
         'mapping': ['creator'],
         'sche_or_attr':[{'id': 'creator',
                          'contents': 'creator',
                          'checkStus': False}],
         'default_display': True,
         'inputType': 'text',
         'inputVal': '',
         'mappingFlg': False,
         'mappingName': ''},
        {'id': 'subject', 'contents': '', 'contents_value': {'en': 'Subject', 'ja': '件名'}, 'useable_status': True, 'mapping': ['BSH', 'DDC', 'LCC', 'LCSH', 'MeSH', 'NDC', 'NDLC', 'NDLSH', 'UDC', 'Other', 'Scival'],
         'sche_or_attr':[{'id': '0', 'contents': 'BSH', 'checkStus': False},
                         {'id': '1', 'contents': 'DDC', 'checkStus': False},
                         {'id': '2', 'contents': 'LCC', 'checkStus': False},
                         {'id': '3', 'contents': 'LCSH', 'checkStus': False},
                         {'id': '4', 'contents': 'MeSH', 'checkStus': False},
                         {'id': '5', 'contents': 'NDC', 'checkStus': False},
                         {'id': '6', 'contents': 'NDLC', 'checkStus': False},
                         {'id': '7', 'contents': 'NDLSH', 'checkStus': False},
                         {'id': '8', 'contents': 'UDC', 'checkStus': False},
                         {'id': '9', 'contents': 'Other', 'checkStus': False},
                         {'id': '10', 'contents': 'Scival', 'checkStus': False}],
         'default_display': True, 'inputType': 'text', 'inputVal': '', 'mappingFlg': True, 'mappingName': 'sbjscheme'},

        {'id': 'spatial',
         'contents': '',
         'contents_value': {'en': 'Region', 'ja': '地域'},
         'useable_status': True,
         'mapping': ['spatial'],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},
        {'id': 'des',
         'contents': '',
         'contents_value': {'en': 'Description', 'ja': '内容記述'},
         'useable_status': True,
         'mapping': ['description'],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},
        {'id': 'publisher',
         'contents': '',
         'contents_value': {'en': 'Publisher', 'ja': '出版者'},
         'useable_status': True,
         'mapping': ['publisher'],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},
        {'id': 'cname',
         'contents': '',
         'contents_value': {'en': 'Contributors', 'ja': '寄与者'},
         'useable_status': True,
         'mapping': ['contributor'],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},


        {'id': 'filedate', 'contents': '', 'contents_value': {'en': 'Contents Created Date', 'ja': 'コンテンツ作成日'}, 'useable_status': True, 'mapping': ['date'],
         'sche_or_attr':[{'id': 'Accepted', 'contents': 'Accepted', 'checkStus': False},
                         {'id': 'Available',
                          'contents': 'Available',
                          'checkStus': False},
                         {'id': 'Collected',
                          'contents': 'Collected',
                          'checkStus': False},
                         {'id': 'Copyrighted',
                          'contents': 'Copyrighted',
                          'checkStus': False},
                         {'id': 'Created', 'contents': 'Created', 'checkStus': False},
                         {'id': 'Issued', 'contents': 'Issued', 'checkStus': False},
                         {'id': 'Submitted',
                          'contents': 'Submitted',
                          'checkStus': False},
                         {'id': 'Updated', 'contents': 'Updated', 'checkStus': False},
                         {'id': 'Valid', 'contents': 'Valid', 'checkStus': False}],
         'default_display': True, 'inputType': 'dateRange', 'inputVal_from': '', 'inputVal_to': '', 'mappingFlg': True, 'mappingName': 'fd_attr'},

        {'id': 'mimetype',
         'contents': '',
         'contents_value': {'en': 'Format', 'ja': 'フォーマット'},
         'useable_status': True,
         'mapping': ['format'],
         'sche_or_attr':[{'id': 'format',
                          'contents': 'format',
                          'checkStus': False}],
         'default_display': True,
         'inputType': 'text',
         'inputVal': '',
         'mappingFlg': False,
         'mappingName': ''},

        {'id': 'id', 'contents': '', 'contents_value': {'en': 'ID', 'ja': 'ID'}, 'useable_status': True, 'mapping': ['identifier', 'URI', 'fullTextURL', 'selfDOI', 'ISBN', 'ISSN', 'NCID', 'pmid', 'doi', 'NAID', 'ichushi'],
         'sche_or_attr':[{'id': 'identifier', 'contents': 'identifier', 'checkStus': False},
                         {'id': 'URI', 'contents': 'URI', 'checkStus': False},
                         {'id': 'fullTextURL',
                          'contents': 'fullTextURL',
                          'checkStus': False},
                         {'id': 'selfDOI', 'contents': 'selfDOI', 'checkStus': False},
                         {'id': 'ISBN', 'contents': 'ISBN', 'checkStus': False},
                         {'id': 'ISSN', 'contents': 'ISSN', 'checkStus': False},
                         {'id': 'NCID', 'contents': 'NCID', 'checkStus': False},
                         {'id': 'pmid', 'contents': 'pmid', 'checkStus': False},
                         {'id': 'doi', 'contents': 'doi', 'checkStus': False},
                         {'id': 'NAID', 'contents': 'NAID', 'checkStus': False},
                         {'id': 'ichushi', 'contents': 'ichushi', 'checkStus': False},
                         ],
         'default_display': True, 'inputType': 'text', 'inputVal': '', 'mappingFlg': True, 'mappingName': 'id_attr'},

        {'id': 'srctitle',
         'contents': '',
         'contents_value': {'en': 'Journal Title', 'ja': '雑誌名'},
         'useable_status': True,
         'mapping': ['srctitle'],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},
        {'id': 'type', 'contents': '', 'contents_value': {'en': 'Resource Type', 'ja': '資源タイプ'}, 'useable_status': True, 'mapping': ['Conference', 'Paper', 'Departmental', 'Bulletin',
                                                                                                                                     'Paper', 'Journal', 'Article', 'Article', 'Book', 'Presentation',
                                                                                                                                     'Data', 'or', 'Dataset', 'Research', 'Paper', 'Technical', 'Report',
                                                                                                                                     'Thesis', 'or', 'Dissertation', 'Learning', 'Material', 'Software'],
         'check_val':[
             {'id': '0', 'contents': 'conference paper', 'checkStus': False},
             {'id': '1', 'contents': 'data paper', 'checkStus': False},
             {'id': '2', 'contents': 'departmental bulletin paper', 'checkStus': False},
             {'id': '3', 'contents': 'editorial', 'checkStus': False},
             {'id': '4', 'contents': 'journal article', 'checkStus': False},
             {'id': '5', 'contents': 'newspaper', 'checkStus': False},
             {'id': '6', 'contents': 'periodical', 'checkStus': False},
             {'id': '7', 'contents': 'review article', 'checkStus': False},
             {'id': '8', 'contents': 'software paper', 'checkStus': False},
             {'id': '9', 'contents': 'article', 'checkStus': False},
             {'id': '10', 'contents': 'book', 'checkStus': False},
             {'id': '11', 'contents': 'book part', 'checkStus': False},
             {'id': '12', 'contents': 'cartographic material', 'checkStus': False},
             {'id': '13', 'contents': 'map', 'checkStus': False},
             {'id': '14', 'contents': 'conference object', 'checkStus': False},
             {'id': '15', 'contents': 'conference proceedings', 'checkStus': False},
             {'id': '16', 'contents': 'conference poster', 'checkStus': False},
             {'id': '17', 'contents': 'dataset', 'checkStus': False},
             {'id': '18', 'contents': 'interview', 'checkStus': False},
             {'id': '19', 'contents': 'image', 'checkStus': False},
             {'id': '20', 'contents': 'still image', 'checkStus': False},
             {'id': '21', 'contents': 'moving image', 'checkStus': False},
             {'id': '22', 'contents': 'video', 'checkStus': False},
             {'id': '23', 'contents': 'lecture', 'checkStus': False},
             {'id': '24', 'contents': 'patent', 'checkStus': False},
             {'id': '25', 'contents': 'internal report', 'checkStus': False},
             {'id': '26', 'contents': 'report', 'checkStus': False},
             {'id': '27', 'contents': 'research report', 'checkStus': False},
             {'id': '28', 'contents': 'technical report', 'checkStus': False},
             {'id': '29', 'contents': 'policy report', 'checkStus': False},
             {'id': '30', 'contents': 'report part', 'checkStus': False},
             {'id': '31', 'contents': 'working paper', 'checkStus': False},
             {'id': '32', 'contents': 'data management plan', 'checkStus': False},
             {'id': '33', 'contents': 'sound', 'checkStus': False},
             {'id': '34', 'contents': 'thesis', 'checkStus': False},
             {'id': '35', 'contents': 'bachelor thesis', 'checkStus': False},
             {'id': '36', 'contents': 'master thesis', 'checkStus': False},
             {'id': '37', 'contents': 'doctoral thesis', 'checkStus': False},
             {'id': '38', 'contents': 'interactive resource', 'checkStus': False},
             {'id': '39', 'contents': 'learning object', 'checkStus': False},
             {'id': '40', 'contents': 'manuscript', 'checkStus': False},
             {'id': '41', 'contents': 'musical notation', 'checkStus': False},
             {'id': '42', 'contents': 'research proposal', 'checkStus': False},
             {'id': '43', 'contents': 'software', 'checkStus': False},
             {'id': '44', 'contents': 'technical documentation', 'checkStus': False},
             {'id': '45', 'contents': 'workflow', 'checkStus': False},
             {'id': '46', 'contents': 'other', 'checkStus': False}
        ],
            'default_display': True, 'inputType': 'checkbox_list', 'inputVal': '', 'mappingFlg': False, 'mappingName': ''},

        {'id': 'itemtype',
         'contents': '',
         'contents_value': {'en': 'Item Type', 'ja': 'アイテムタイプ'},
         'useable_status': True,
         'mapping': ['itemtype'],
         'check_val':[],
         'default_display':True,
         'inputType':'checkbox_list',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},


        {'id': 'lang', 'contents': '', 'contents_value': {'en': 'Language', 'ja': '言語'}, 'useable_status': True, 'mapping': ['Japanese', 'English', 'French', 'Italian', 'German', 'Spanish', 'Chinese', 'Russian', 'Latin', 'Malay', 'Esperanto', 'Arabic', 'Greek', 'Korean', 'Other'],
         'check_val':[{'id': 'jpn', 'contents': 'Japanese', 'checkStus': False},
                      {'id': 'eng', 'contents': 'English', 'checkStus': False},
                      {'id': 'fra', 'contents': 'French', 'checkStus': False},
                      {'id': 'ita', 'contents': 'Italian', 'checkStus': False},
                      {'id': 'deu', 'contents': 'German', 'checkStus': False},
                      {'id': 'spa', 'contents': 'Spanish', 'checkStus': False},
                      {'id': 'zho', 'contents': 'Chinese', 'checkStus': False},
                      {'id': 'rus', 'contents': 'Russian', 'checkStus': False},
                      {'id': 'lat', 'contents': 'Latin', 'checkStus': False},
                      {'id': 'msa', 'contents': 'Malay', 'checkStus': False},
                      {'id': 'epo', 'contents': 'Esperanto', 'checkStus': False},
                      {'id': 'ara', 'contents': 'Arabic', 'checkStus': False},
                      {'id': 'ell', 'contents': 'Greek', 'checkStus': False},
                      {'id': 'kor', 'contents': 'Korean', 'checkStus': False},
                      {'id': 'other', 'contents': 'Other', 'checkStus': False},
                      ], 'default_display': True, 'inputType': 'checkbox_list', 'inputVal': '', 'mappingFlg': False, 'mappingName': ''},
        {'id': 'temporal',
         'contents': '',
         'contents_value': {'en': 'Period', 'ja': '期間'},
         'useable_status': True,
         'mapping': ['temporal'],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},

        {'id': 'dategranted',
         'contents': '',
         'contents_value': {'en': 'Academic Degree Date', 'ja': '学位取得日'},
         'useable_status': True,
         'mapping': ['date'],
         'default_display':True,
         'inputType':'dateRange',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':''},


        {'id': 'version', 'contents': '', 'contents_value': {'en': 'Author Version Flag', 'ja': '著者版フラグ'}, 'useable_status': True, 'mapping': [],
         'options':[
             {'id': 'accepted', 'contents': 'accepted'},
             {'id': 'published', 'contents': 'published'},
             {'id': 'draft', 'contents': 'draft'},
             {'id': 'submitted', 'contents': 'submitted'},
             {'id': 'updated', 'contents': 'updated'}
        ], 'default_display': True, 'inputType': 'selectbox', 'inputVal': '', 'mappingFlg': False, 'mappingName': ''},
        {'id': 'dissno',
         'contents': '',
         'contents_value': {'en': 'Academic Degree Number', 'ja': '学位番号'},
         'useable_status': True,
         'mapping': [],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},

        {'id': 'degreename',
         'contents': '',
         'contents_value': {'en': 'Degree Name', 'ja': '学位名'},
         'useable_status': True,
         'mapping': [],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},
        {'id': 'dgname',
         'contents': '',
         'contents_value': {'en': 'Institution For Academic Degree', 'ja': '学位授与機関'},
         'useable_status': True,
         'mapping': [],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},
        {'id': 'wid',
         'contents': '',
         'contents_value': {'en': 'Author Id', 'ja': '著者ID'},
         'useable_status': True,
         'mapping': [],
         'default_display':True,
         'inputType':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':''},
        {'id': 'iid', 'contents': '', 'contents_value': {'en': 'Index', 'ja': 'インデックス'}, 'useable_status': True,
         'mapping': ['iid'],
         'check_val':[],
         'inputVal':'',
         'default_display': True, 'inputType': 'checkbox_list', 'inputVal': '', 'mappingFlg': False, 'mappingName': ''},
        {'id': 'license', 'contents': 'License', 'contents_value': {'en': 'License', 'ja': 'ライセンス'}, 'useable_status': True,
         'mapping': [],
         'check_val':[
             {'id': 'license_12', 'contents': 'CC0'},
             {'id': 'license_6', 'contents': 'CC BY 3.0'},
             {'id': 'license_7', 'contents': 'CC BY-SA 3.0'},
             {'id': 'license_8', 'contents': 'CC BY-ND 3.0'},
             {'id': 'license_9', 'contents': 'CC BY-NC 3.0'},
             {'id': 'license_10', 'contents': 'CC BY-NC-SA 3.0'},
             {'id': 'license_11', 'contents': 'CC BY-NC-ND 3.0'},
             {'id': 'license_0', 'contents': 'CC BY 4.0'},
             {'id': 'license_1', 'contents': 'CC BY-SA 4.0'},
             {'id': 'license_2', 'contents': 'CC BY-ND 4.0'},
             {'id': 'license_3', 'contents': 'CC BY-NC 4.0'},
             {'id': 'license_4', 'contents': 'CC BY-NC-SA 4.0'},
             {'id': 'license_5', 'contents': 'CC BY-NC-ND 4.0'},
             {'id': 'license_free', 'contents': 'Other'},
        ], 'default_display': True, 'inputType': 'checkbox_list', 'inputVal': '', 'mappingFlg': False, 'mappingName': ''},
        {'id': 'text1',
         'contents': '',
         'contents_value': {'en': 'text1', 'ja': 'テキスト1'},
         'useable_status': True,
         'mapping': [],
         'default_display':True,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },
        {'id': 'text2',
         'contents': '',
         'contents_value': {'en': 'text2', 'ja': 'テキスト2'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },
        {'id': 'text3',
         'contents': '',
         'contents_value': {'en': 'text3', 'ja': 'テキスト3'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },
        {'id': 'text4',
         'contents': '',
         'contents_value': {'en': 'text4', 'ja': 'テキスト4'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },
        {'id': 'text5',
         'contents': '',
         'contents_value': {'en': 'text5', 'ja': 'テキスト5'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },
        {'id': 'text6',
         'contents': '',
         'contents_value': {'en': 'text6', 'ja': 'テキスト6'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },
        {'id': 'text7',
         'contents': '',
         'contents_value': {'en': 'text7', 'ja': 'テキスト7'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },
        {'id': 'text8',
         'contents': '',
         'contents_value': {'en': 'text8', 'ja': 'テキスト8'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },
        {'id': 'text9',
         'contents': '',
         'contents_value': {'en': 'text9', 'ja': 'テキスト9'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },
        {'id': 'text10',
         'contents': '',
         'contents_value': {'en': 'text10', 'ja': 'テキスト10'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'text',
         'input_Type':'text',
         'inputVal':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': '', 'path_type': 'json'}
                       }
         },


        {'id': 'integer_range1',
         'contents': '',
         'contents_value': {'en': 'integer_EN_1', 'ja': 'integer_JA_1'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'integer_range2',
         'contents': '',
         'contents_value': {'en': 'integer_EN_2', 'ja': 'integer_JA_2'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'integer_range3',
         'contents': '',
         'contents_value': {'en': 'integer_EN_3', 'ja': 'integer_JA_3'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'integer_range4',
         'contents': '',
         'contents_value': {'en': 'integer_EN_4', 'ja': 'integer_JA_4'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'integer_range5',
         'contents': '',
         'contents_value': {'en': 'integer_EN_5', 'ja': 'integer_JA_5'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },

        {'id': 'float_range1',
         'contents': 'float_range1',
         'contents': '',
         'contents_value': {'en': 'float_EN_1', 'ja': 'float_JA_1'},
         'useable_status': True,
         'mapping': [],
         'default_display':True,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'float_range2',
         'contents': '',
         'contents_value': {'en': 'float_EN_2', 'ja': 'float_JA_2'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'float_range3',
         'contents': '',
         'contents_value': {'en': 'float_EN_3', 'ja': 'float_JA_3'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'float_range4',
         'contents': '',
         'contents_value': {'en': 'float_EN_4', 'ja': 'float_JA_4'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'float_range5',
         'contents': '',
         'contents_value': {'en': 'float_EN_5', 'ja': 'float_JA_5'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'range',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },

        {'id': 'date_range1',
         'contents': '',
         'contents_value': {'en': 'date_EN_1', 'ja': 'date_JA_1'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'dateRange',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'date_range2',
         'contents': '',
         'contents_value': {'en': 'date_EN_2', 'ja': 'date_JA_2'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'dateRange',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'date_range3',
         'contents': '',
         'contents_value': {'en': 'date_EN_3', 'ja': 'date_JA_3'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'dateRange',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'date_range4',
         'contents': '',
         'contents_value': {'en': 'date_EN_4', 'ja': 'date_JA_4'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'dateRange',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },
        {'id': 'date_range5',
         'contents': '',
         'contents_value': {'en': 'date_EN_5', 'ja': 'date_JA_5'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'dateRange',
         'input_Type':'range',
         'inputVal_from':'',
         'inputVal_to':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'gte': '', 'lte': ''}, 'path_type': {'gte': 'json', 'lte': 'json'}}
                       }
         },

        {'id': 'geo_point1',
         'contents': '',
         'contents_value': {'en': 'geopoint_EN_1', 'ja': 'geopoint_JA_1'},
         'useable_status': True,
         'mapping': [],
         'default_display':True,
         'inputType':'geo_distance',
         'input_Type':'geo_point',
         'inputVal_lat':'',
         'inputVal_lon':'',
         'inputVal_distance':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'lat': '', 'lon': ''}, 'path_type': {'lat': 'json', 'lon': 'json'}}
                       }
         },

        {'id': 'geo_shape1',
         'contents': '',
         'contents_value': {'en': 'geoshape_EN_1', 'ja': 'geoshape_JA_1'},
         'useable_status': True,
         'mapping': [],
         'default_display':False,
         'inputType':'geo_distance',
         'input_Type':'geo_shape',
         'inputVal_lat':'',
         'inputVal_lon':'',
         'inputVal_distance':'',
         'mappingFlg':False,
         'mappingName':'',
         'item_value':{'1': {'path': {'type': '', 'coordinates': ''}, 'path_type': {'type': 'json', 'coordinates': 'json'}}
                       }
         }
    ]
}

WEKO_ADMIN_PERMISSION_ROLE_SYSTEM = "System Administrator"

WEKO_ADMIN_PERMISSION_ROLE_REPO = "Repository Administrator"

WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY = "Community Administrator"

WEKO_ADMIN_COMMUNITY_ACCESS_LIST = [
    'admin',
    'harvestsettings',
    'identifier',
    'widgetitem',
    'widgetdesign',
    'items/custom_sort',
    'items/search',
    'indexedit',
    'indexjournal',
    'report',
    'itemexportsettings',
    'items/import',
    'logs/export'
    'items/bulk/update',
    'items/bulk/delete',
    'items/bulk-export',
    'authors',
    'authors/export',
    'authors/import',
    'feedbackmail',
    'sitelicensesendmail',
    'flowsetting',
    'workflowsetting',
    'community',
    'user',
    'resource_list',
    'change_list',
    'resync',
    'sitelicensesettings',
    'oaiset',
]
"""Classes Community Administrator can access."""

WEKO_ADMIN_REPOSITORY_ACCESS_LIST = [
    'authors',
    'authors/export',
    'authors/import',
    'flowsetting',
    'identify',
    'items/bulk/delete',
    'items/bulk/update',
    'items/search',
    'itemtypes',
    'language',
    'loganalysissetting',
    'others',
    'pdfcoverpage',
    'rankingsettings',
    'site-info',
    'site-license',
    'search-management',
    'sitemap',
    'indexlink',
    'itemsetting',
    'statssettings',
    'stylesetting',
    'user',
    'userprofile',
    'workflowsetting',
    'searchsettings',
    'sitelicensesettings',
    'itemtypesregister',
    'itemtypesmapping',
    'itemtypesrocratemapping',
    'itemtypes/mapping',
    'items/bulk-export',
    'feedbackmail',
    'sitelicensesendmail',
    'sessionactivity',
    'rankingsettings',
    'longanalysissetting',
    'site_info',
    'location',
    'facet-search',
    'community',
    'workspaceworkflowsetting',
    'swordapi',
    'swordapi/jsonld',
    'jsonld-mapping',
    'shibboleth',
    # 'restricted_access'
] + WEKO_ADMIN_COMMUNITY_ACCESS_LIST
"""Classes Repository Administrator can access."""

WEKO_ADMIN_ACCESS_TABLE = {
    "System Administrator": [],  # Can access all, not needed
    "Repository Administrator": WEKO_ADMIN_REPOSITORY_ACCESS_LIST,
    "Community Administrator": WEKO_ADMIN_COMMUNITY_ACCESS_LIST,
}
"""Access table for different admin roles."""

WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS = {
    'allow_item_exporting': True,
    'enable_contents_exporting': True
}
"""Access table for different admin roles."""

WEKO_ADMIN_NUMBER_OF_SEND_MAIL_HISTORY = 20
"""Number of history display per page."""

WEKO_ADMIN_NUMBER_OF_FAILED_MAIL = 10
"""Number of failed mail display per page."""

WEKO_PIDSTORE_IDENTIFIER_TEMPLATE_CREATOR = 'weko_records_ui/admin/pidstore_identifier_creator.html'
""" Pidstore identifier creator template. """

WEKO_PIDSTORE_IDENTIFIER_TEMPLATE_EDITOR = 'weko_records_ui/admin/pidstore_identifier_editor.html'
""" Pidstore identifier editor template. """

WEKO_ADMIN_ENABLE_LOGIN_INSTRUCTIONS = False
""" Enable Login Instructions """


WEKO_HEADER_NO_CACHE = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}
""" Header no cache property """

WEKO_ADMIN_SEARCH_OPTIONS = {
    "init_disp_setting_options": {
        "init_disp_screen_setting": [
            {'id': '0', 'contents': {
                'en': 'Index search result',
                'ja': 'インデックス検索結果を表示する'
            }},
            {'id': '1', 'contents': {
                'en': 'Ranking',
                'ja': 'ランキングを表示する'
            }},
            {'id': '2', 'contents': {
                'en': 'Communities',
                'ja': 'コミュニティ一覧を表示する'
            }},
        ],
        "init_disp_index_disp_method": [
            {'id': '0', 'contents': {
                'en': 'Index of the newest item registered',
                'ja': '最も新しい公開アイテムの属するインデックス'
            }},
            {'id': '1', 'contents': {
                'en': 'Specific index',
                'ja': 'インデックス指定'
            }},
        ]
    }
}
"""Admin Search Options """

WEKO_INDEX_TREE_STYLE_OPTIONS = {
    'id': 'weko',
    'widths': ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
}

WEKO_ADMIN_RESTRICTED_ACCESS_DISPLAY_FLAG = False
"""
Restricted access feature display flag.
True: display all feature
False: only display secret url download
"""

WEKO_ADMIN_RESTRICTED_ACCESS_SETTINGS = {
    "secret_URL_file_download": {
        "secret_expiration_date": 30,
        "secret_expiration_date_unlimited_chk": False,
        "secret_download_limit": 10,
        "secret_download_limit_unlimited_chk": False,
    },
    "content_file_download": {
        "expiration_date": 30,
        "expiration_date_unlimited_chk": False,
        "download_limit": 10,
        "download_limit_unlimited_chk": False,
    },
    "usage_report_workflow_access": {
        "expiration_date_access": 500,
        "expiration_date_access_unlimited_chk": False,
    },
    "terms_and_conditions": []
}
"""Default restricted access settings."""

WEKO_ADMIN_RESTRICTED_ACCESS_MAX_INTEGER = 9999999

WEKO_ADMIN_ITEMS_PER_PAGE_USAGE_REPORT_REMINDER = 25
"""Default number of usage report activities results that display in one page."""

WEKO_ADMIN_FEEDBACK_MAIL_DEFAULT_SUBJECT = "No Site Name"
"""Default subject of feedback email."""

WEKO_ADMIN_FACET_SEARCH_SETTING_TEMPLATE = 'weko_admin/admin/facet_search_setting.html'
"""Facet search setting template."""

WEKO_ADMIN_FACET_SEARCH_SETTING = {
    "name_en": "",
    "name_jp": "",
    "mapping": "",
    "active": True,
    "aggregations": [],
    "ui_type": "CheckboxList",
    "display_number": 5,
    "is_open": True,
    "search_condition": "OR"
}
"""Default Facet Search settings."""

WEKO_ADMIN_FACET_SEARCH_SETTING_QUERY_KEY_HAS_PERMISSION = 'facet_search_query_has_permission'
"""Default Facet Search query has permission settings."""

WEKO_ADMIN_FACET_SEARCH_SETTING_QUERY_KEY_NO_PERMISSION = 'facet_search_query_no_permission'
"""Default Facet Search query has no permission settings."""

WEKO_ADMIN_FACET_SEARCH_SETTING_BUCKET_SIZE = 1000
"""Default Facet Search bucket size."""

WEKO_ADMIN_SWORD_API_JSON_LD_FULL_AUTHORITY_ROLE = 1
"""Allowed Role id, full access to list JSON_LD."""

WEKO_ADMIN_CACHE_TEMP_DIR_INFO_KEY_DEFAULT = 'cache::temp_dir_info'
"""Default Cache Temporary Directory Information Key."""

WEKO_ADMIN_USE_REGEX_IN_CRAWLER_LIST = False
""" If True, enable regex function in crawler list processing. """
