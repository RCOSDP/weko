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

WEKO_ADMIN_DEFAULT_LIFETIME = 60
""" Session time out setting, default 60 minutes """

WEKO_ADMIN_BASE_TEMPLATE = 'weko_admin/base.html'
"""Base templates for weko-admin module."""

WEKO_ADMIN_SETTINGS_TEMPLATE = None
"""Settings base templates for weko-admin module."""

WEKO_ADMIN_LIFETIME_TEMPLATE = 'weko_admin/settings/lifetime.html'
"""Settings base templates for weko-admin module."""

WEKO_ADMIN_SITE_LICENSE_TEMPLATE = 'weko_admin/admin/site_license_settings.html'
"""Site-license templates."""

WEKO_ADMIN_BlOCK_STYLE_TEMPLATE = 'weko_admin/admin/block_style.html'
"""Block-style templates."""

WEKO_ADMIN_REPORT_TEMPLATE = 'weko_admin/admin/report.html'
"""Report template."""

WEKO_ADMIN_STATS_SETTINGS_TEMPLATE = 'weko_admin/admin/stats_settings.html'
"""Stats Settings template."""

WEKO_ADMIN_LOG_ANALYSIS_SETTINGS_TEMPLATE = \
    'weko_admin/admin/log_analysis_settings.html'
"""Stats Settings template."""

WEKO_ADMIN_LANG_SETTINGS = 'weko_admin/admin/lang_settings.html'
"""Language templates."""

WEKO_ADMIN_FEEDBACK_MAIL = 'weko_admin/admin/feedback_mail.html'
"""Language templates."""

WEKO_ADMIN_WEB_API_ACCOUNT = 'weko_admin/admin/web_api_account.html'
"""Web Api Account templates."""

WEKO_ADMIN_SEARCH_MANAGEMENT_TEMPLATE = \
    'weko_admin/admin/search_management_settings.html'
"""Site-license templates."""

WEKO_ADMIN_RANKING_SETTINGS_TEMPLATE = 'weko_admin/admin/ranking_settings.html'
"""Ranking Settings template."""

LOGO_ALLOWED_EXTENSIONS = set(['png', 'jpeg', 'jpg'])

WEKO_ADMIN_CROSSREF_API_URL = 'https://doi.crossref.org/'
"""URL of CrossRef API."""

WEKO_ADMIN_ENDPOINT = 'openurl'
"""Endpoint to concate URL of CrossRef API."""

WEKO_ADMIN_TEST_DOI = '&id=doi:10.1047/0003-066X.59.1.29'
"""DOI for check Certificate valid or not."""

WEKO_ADMIN_FORMAT = '&format=json'
"""Format of CrossRef Certificate."""

WEKO_ADMIN_VALIDATION_MESSAGE = 'The login you supplied is not recognized'
"""Validate message of certificate."""

WEKO_ADMIN_DISPLAY_FILE_STATS = True
"""Display record stats or not."""

WEKO_ADMIN_DEFAULT_CRAWLER_LISTS = [
    'https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_ip_blacklist.txt',
    'https://bitbucket.org/niijp/jairo-crawler-list/raw/master/JAIRO_Crawler-List_useragent.txt'
]
"""Default crawler files for restricting IP addresses and user agents."""

WEKO_ADMIN_REPORT_FREQUENCIES = ['daily', 'weekly', 'monthly']
"""Email schedule frequency options."""

WEKO_ADMIN_REPORT_DELIVERY_SCHED = {
    'frequency': 'daily', 'details': '', 'enabled': False
}
"""Default report email delivery schedule."""

WEKO_ADMIN_CACHE_PREFIX = 'admin_cache_{name}'
"""Redis cache."""

WEKO_ADMIN_REPORT_HEADERS = {
    'file_download': _('No. Of File Downloads'),
    'file_preview': _('No. Of File Previews'),
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
        _('No. Of Times Downloaded/Viewed'), _('Non-Logged In User'),
        _('Logged In User'), _('Site License'), _('Admin'),
        _('Registrar')],
    'file_preview': [
        _('File Name'), _('Registered Index Name'),
        _('No. Of Times Downloaded/Viewed'), _('Non-Logged In User'),
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
    'dlt_dis_num_options':[
        {'id': '20', 'contents': '20'},
        {'id': '50', 'contents': '50'},
        {'id': '75', 'contents': '75'},
        {'id': '100', 'contents': '100'}
    ],
    'dlt_dis_num_selected': '20',
    'dlt_index_sort_options':[
        {'id': 'wtl_asc', 'contents': 'Title(asc)', 'disableFlg':False},
        {'id': 'wtl_desc', 'contents': 'Title(desc)', 'disableFlg':False},
        {'id': 'creator_asc', 'contents': 'Creator(asc)', 'disableFlg':False},
        {'id': 'creator_desc', 'contents': 'Creator(desc)', 'disableFlg':False},
        {'id': 'itemType_asc', 'contents': 'Item Type(asc)', 'disableFlg':False},
        {'id': 'itemType_desc', 'contents': 'Item Type(desc)', 'disableFlg':False},
        {'id': 'controlnumber_asc', 'contents': 'ID(asc)', 'disableFlg':False},
        {'id': 'controlnumber_desc', 'contents': 'ID(desc)', 'disableFlg':False},
        {'id': 'upd_asc', 'contents': 'Update(asc)', 'disableFlg':False},
        {'id': 'upd_desc', 'contents': 'Update(desc)', 'disableFlg':False},
        {'id': 'createdate_asc', 'contents': 'Create(asc)', 'disableFlg':False},
        {'id': 'createdate_desc', 'contents': 'Create(desc)', 'disableFlg':False},
        {'id': 'pyear_asc', 'contents': 'Date Of Issued(asc)', 'disableFlg':False},
        {'id': 'pyear_desc', 'contents': 'Date Of Issued(desc)', 'disableFlg':False},
        {'id': 'custom_sort_asc', 'contents': 'Custom(asc)', 'disableFlg':False},
        {'id': 'custom_sort_desc', 'contents': 'Custom(desc)', 'disableFlg':False},
    ],
    'dlt_index_sort_selected': 'controlnumber_asc',
    'dlt_keyword_sort_options':[
        {'id': 'wtl_asc', 'contents': 'Title(asc)', 'disableFlg': False},
        {'id': 'wtl_desc', 'contents': 'Title(desc)', 'disableFlg': False},
        {'id': 'creator_asc', 'contents': 'Creator(asc)', 'disableFlg': False},
        {'id': 'creator_desc', 'contents': 'Creator(desc)', 'disableFlg': False},
        {'id': 'itemType_asc', 'contents': 'Item Type(asc)', 'disableFlg': False},
        {'id': 'itemType_desc', 'contents': 'Item Type(desc)', 'disableFlg': False},
        {'id': 'controlnumber_asc', 'contents': 'ID(asc)', 'disableFlg': False},
        {'id': 'controlnumber_desc', 'contents': 'ID(desc)', 'disableFlg': False},
        {'id': 'upd_asc', 'contents': 'Update(asc)', 'disableFlg': False},
        {'id': 'upd_desc', 'contents': 'Update(desc)', 'disableFlg': False},
        {'id': 'createdate_asc', 'contents': 'Create(asc)', 'disableFlg': False},
        {'id': 'createdate_desc', 'contents': 'Create(desc)', 'disableFlg': False},
        {'id': 'pyear_asc', 'contents': 'Date Of Issued(asc)', 'disableFlg': False},
        {'id': 'pyear_desc', 'contents': 'Date Of Issued(desc)', 'disableFlg': False},
        {'id': 'custom_sort_asc', 'contents': 'Custom(asc)', 'disableFlg': False},
        {'id': 'custom_sort_desc', 'contents': 'Custom(desc)', 'disableFlg': False},
    ],
    'dlt_keyword_sort_selected': 'createdate_desc',
    'sort_options':{
        'deny':[],
        'allow':[
            {'id': 'wtl_asc', 'contents': 'Title(asc/desc)'},
            {'id': 'creator_asc', 'contents': 'Creator(asc/desc)'},
            {'id': 'itemType_asc', 'contents': 'ItemType(asc/desc)'},
            {'id': 'controlnumber_asc', 'contents': 'ID(asc/desc)'},
            {'id': 'upd_asc', 'contents': 'Update(asc/desc)'},
            {'id': 'createdate_asc', 'contents': 'Create(asc/desc)'},
            {'id': 'pyear_asc', 'contents': 'Date Of Issued(asc/desc)'},
            {'id': 'custom_sort_asc', 'contents': 'Custom(asc/desc)'}
        ]
    },
    'detail_condition':[
        {'id':'title','contents':'Title','useable_status':True,'mapping':['title'], 'sche_or_attr':[{'id':'title','contents':'title', 'checkStus':False}], 'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'creator','contents':'Author Name','useable_status':True,'mapping':['creator'], 'sche_or_attr':[{'id':'creator','contents':'creator', 'checkStus':False}],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'subject','contents':'Subject','useable_status':True, 'mapping':['BSH','DDC','LCC','LCSH','MeSH','NDC','NDLC','NDLSH','UDC','Other', 'Scival'],
         'sche_or_attr':[{'id':'1','contents':'BSH', 'checkStus':False},
                            {'id':'2','contents':'DDC', 'checkStus':False},
                            {'id':'3','contents':'LCC', 'checkStus':False},
                            {'id':'4','contents':'LCSH', 'checkStus':False},
                            {'id':'5','contents':'MeSH', 'checkStus':False},
                            {'id':'6','contents':'NDC', 'checkStus':False},
                            {'id':'7','contents':'NDLC', 'checkStus':False},
                            {'id':'8','contents':'NDLSH', 'checkStus':False},
                            {'id':'9','contents':'UDC', 'checkStus':False},
                            {'id':'10','contents':'Other', 'checkStus':False},
                            {'id':'11','contents':'Scival', 'checkStus':False}],
         'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':True, 'mappingName':'sbjscheme'},

        {'id':'spatial','contents':'Region','useable_status':True,'mapping':['spatial'],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'des','contents':'Description','useable_status':True,'mapping':['description'],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'publisher','contents':'Publisher','useable_status':True,'mapping':['publisher'],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'cname','contents':'Contributors','useable_status':True,'mapping':['contributor'],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},


        {'id':'filedate', 'contents': 'Contents Created Date', 'useable_status': True, 'mapping': ['date'],
         'sche_or_attr':[{'id':'Accepted','contents':'Accepted', 'checkStus':False},
                            {'id':'Available','contents':'Available', 'checkStus':False},
                            {'id':'Collected','contents':'Collected', 'checkStus':False},
                            {'id':'Copyrighted','contents':'Copyrighted', 'checkStus':False},
                            {'id':'Created','contents':'Created', 'checkStus':False},
                            {'id':'Issued','contents':'Issued', 'checkStus':False},
                            {'id':'Submitted','contents':'Submitted', 'checkStus':False},
                            {'id':'Updated','contents':'Updated', 'checkStus':False},
                            {'id':'Valid','contents':'Valid', 'checkStus':False}],
         'default_display':True, 'inputType':'dateRange', 'inputVal_from':'', 'inputVal_to':'','mappingFlg':True, 'mappingName':'fd_attr'},

        {'id':'format','contents':'Format','useable_status':True,'mapping':['format'],'sche_or_attr':[{'id':'format','contents':'format', 'checkStus':False}],'default_display':True,'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},

        {'id':'id','contents':'ID','useable_status':True,'mapping':['identifier','URI','fullTextURL','selfDOI','ISBN','ISSN','NCID','pmid','doi','NAID','ichushi'],
        'sche_or_attr':[{'id':'identifier','contents':'identifier', 'checkStus':False},
                        {'id':'URI','contents':'URI', 'checkStus':False},
                        {'id':'fullTextURL','contents':'fullTextURL', 'checkStus':False},
                        {'id':'selfDOI','contents':'selfDOI', 'checkStus':False},
                        {'id':'ISBN','contents':'ISBN', 'checkStus':False},
                        {'id':'ISSN','contents':'ISSN', 'checkStus':False},
                        {'id':'NCID','contents':'NCID', 'checkStus':False},
                        {'id':'pmid','contents':'pmid', 'checkStus':False},
                        {'id':'doi','contents':'doi', 'checkStus':False},
                        {'id':'NAID','contents':'NAID', 'checkStus':False},
                        {'id':'ichushi','contents':'ichushi', 'checkStus':False},
                        ],
         'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':True, 'mappingName':'id_attr'},

        {'id':'srctitle','contents':'Journal Title','useable_status':True,'mapping':['srctitle'],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'type','contents':'Resource Type','useable_status':True,'mapping':['Conference','Paper','Departmental','Bulletin',
                                                                                           'Paper','Journal','Article','Article','Book','Presentation',
                                                                                           'Data','or','Dataset','Research','Paper','Technical','Report',
                                                                                           'Thesis','or','Dissertation','Learning','Material','Software'],
                                                                                'check_val':[{'id':'1','contents':'Conference Paper', 'checkStus':False},
                                                                                                {'id':'2','contents':'Departmental Bulletin Paper', 'checkStus':False},
                                                                                                {'id':'3','contents':'Journal Article', 'checkStus':False},
                                                                                                {'id':'4','contents':'Article', 'checkStus':False},
                                                                                                {'id':'5','contents':'Book', 'checkStus':False},
                                                                                                {'id':'6','contents':'Presentation', 'checkStus':False},
                                                                                                {'id':'7','contents':'Data or Dataset', 'checkStus':False},
                                                                                                {'id':'8','contents':'Research Paper', 'checkStus':False},
                                                                                                {'id':'9','contents':'Technical Report', 'checkStus':False},
                                                                                                {'id':'10','contents':'Thesis or Dissertation', 'checkStus':False},
                                                                                                {'id':'11','contents':'Learning Material', 'checkStus':False},
                                                                                                {'id':'12','contents':'Software', 'checkStus':False},
                                                                                                ],
                                                                                'default_display':True,'inputType':'checkbox_list', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},

        {'id':'itemtype','contents':'Item Type','useable_status':True,'mapping':['itemtype'],'check_val':[],'default_display':True, 'inputType':'checkbox_list', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},


        {'id':'lang','contents':'Language','useable_status':True,'mapping':['Japanese','English','French','Italian','German','Spanish','Chinese','Russian', 'Latin','Malay','Esperanto','Arabic','Greek','Korean','Other'],
                                                                            'check_val':[{'id':'jpn','contents':'Japanese', 'checkStus':False},
                                                                                        {'id':'eng','contents':'English', 'checkStus':False},
                                                                                        {'id':'fra','contents':'French', 'checkStus':False},
                                                                                        {'id':'ita','contents':'Italian', 'checkStus':False},
                                                                                        {'id':'deu','contents':'German', 'checkStus':False},
                                                                                        {'id':'spa','contents':'Spanish', 'checkStus':False},
                                                                                        {'id':'zho','contents':'Chinese', 'checkStus':False},
                                                                                        {'id':'rus','contents':'Russian', 'checkStus':False},
                                                                                        {'id':'lat','contents':'Latin', 'checkStus':False},
                                                                                        {'id':'msa','contents':'Malay', 'checkStus':False},
                                                                                        {'id':'epo','contents':'Esperanto', 'checkStus':False},
                                                                                        {'id':'ara','contents':'Arabic', 'checkStus':False},
                                                                                        {'id':'ell','contents':'Greek', 'checkStus':False},
                                                                                        {'id':'kor','contents':'Korean', 'checkStus':False},
                                                                                        {'id':'other','contents':'Other', 'checkStus':False},
                                                                                        ],'default_display':True, 'inputType':'checkbox_list', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'temporal','contents':'Period','useable_status':True,'mapping':['temporal'],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},

        {'id':'dategranted','contents':'Academic Degree Date','useable_status':True,'mapping':['date'], 'default_display':True,  'inputType':'dateRange', 'inputVal_from':'', 'inputVal_to':'','mappingFlg':False, 'mappingName':''},


        {'id':'version','contents':'Author Version Flag','useable_status':True,'mapping':[],
                                                                                            'options':[
                                                                                                {'id':'accepted','contents':'accepted'},
                                                                                                {'id':'published','contents':'published'},
                                                                                                {'id':'draft','contents':'draft'},
                                                                                                {'id':'submitted','contents':'submitted'},
                                                                                                {'id':'updated','contents':'updated'}
                                                                                            ],'default_display':True,  'inputType':'selectbox', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'dissno','contents':'Academic Degree Number','useable_status':True,'mapping':[],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},

        {'id':'degreename','contents':'Degree Name','useable_status':True,'mapping':[],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'dgname','contents':'Institution For Academic Degree','useable_status':True,'mapping':[],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'wid','contents':'Author Id','useable_status':True,'mapping':[],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'iid','contents':'Index','useable_status':True,'mapping':[],'default_display':True, 'inputType':'text', 'inputVal':'', 'mappingFlg':False, 'mappingName':''},
        {'id':'rights','contents':'Rights','useable_status':True,'mapping':['CC','BY','CC','BY-SA','CC','BY-ND','CC','BY-NC','CC','BY-NC-SA','ANY'],
                                                                          'radio_val':[
                                                                            {'id':'CC BY','contents':'CC BY'},
                                                                            {'id':'CC BY-SA','contents':'CC BY-SA'},
                                                                            {'id':'CC BY-ND','contents':'CC BY-ND'},
                                                                            {'id':'CC BY-NC','contents':'CC BY-NC'},
                                                                            {'id':'CC BY-NC-SA','contents':'CC BY-NC-SA'},
                                                                            {'id':'ANY','contents':'ANY'},
                                                                          ],'default_display':True,  'inputType':'radio_list', 'inputVal':'', 'mappingFlg':False, 'mappingName':''}
    ]
}

WEKO_ADMIN_PERMISSION_ROLE_SYSTEM = "System Administrator"

WEKO_PERMISSION_ROLE_REPO = "Repository Administrator"

WEKO_PERMISSION_ROLE_COMMUNITY = "Community Administrator"

WEKO_ADMIN_COMMUNITY_ACCESS_LIST = [
    'admin',
    'harvestsettings',
    'identifier',
    'widgetitem',
    'widgetdesign',
    'community',
]
"""Classes Community Administrator can access."""

WEKO_ADMIN_REPOSITORY_ACCESS_LIST = [
    'bucket',
    'flowsetting',
    'fileinstance',
    'identify',
    'items',
    'location',
    'item_management',
    'itemtypes',
    'language',
    'loganalysissetting',
    'mail',
    'others',
    'pdfcoverpage',
    'shibboleth',
    'site-license',
    'search-management',
    'sitemap',
    'indexlink',
    'indextree',
    'itemsetting',
    'statssettings',
    'stylesetting',
    'webapiaccount',
    'report',
    'user',
    'workflowsetting',
    'indexedit',
    'indexjournal',
    'searchsettings',
    'sitelicensesettings',
] + WEKO_ADMIN_COMMUNITY_ACCESS_LIST
"""Classes Repository Administrator can access."""

WEKO_ADMIN_ACCESS_TABLE = {
    "System Administrator": [], # Can access all, not needed
    "Repository Administrator": WEKO_ADMIN_REPOSITORY_ACCESS_LIST,
    "Community Administrator": WEKO_ADMIN_COMMUNITY_ACCESS_LIST,
}
"""Access table for different admin roles."""
