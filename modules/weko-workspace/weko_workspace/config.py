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

"""Configuration for weko-workspace."""

from flask_babelex import lazy_gettext as _
from invenio_stats.config import SEARCH_INDEX_PREFIX as index_prefix

# Front-end variable definition
WEKO_WORKSPACE_BASE_TEMPLATE = 'weko_workspace/workspace_base.html'
"""Default base template for the demo page."""

# Back-end variable definition
WEKO_WORKSPACE_PID_TYPE = 'recid'
"""Get object_uuid."""

WEKO_WORKSPACE_ITEM = {
    "recid": None,
    "title": None,
    "favoriteSts": None,
    "readSts": None,
    "peerReviewSts": None,
    "doi": None,
    "resourceType": None,
    "authorlist": None,
    "accessCnt": None,
    "downloadCnt": None,
    "itemStatus": None,
    "publicationDate": None,
    "magazineName": None,
    "conferenceName": None,
    "volume": None,
    "issue": None,
    "funderName": None,
    "awardTitle": None,
    "fbEmailSts": None,
    "relation": None,
    "relationType": None,
    "relationTitle": None,
    "relationUrl": None,
    "connectionToPaperSts": None,
    "connectionToDatasetSts": None,
    "fileSts": None,
    "fileCnt": None,
    "publicSts": None,
    "publicCnt": None,
    "embargoedSts": None,
    "embargoedCnt": None,
    "restrictedPublicationSts": None,
    "restrictedPublicationCnt": None,
}
"""Default item template for the workspace item list page."""

WEKO_WORKSPACE_AUTOFILL_API_UPDATED = True
"""Flag to indicate if the autofill API is updated."""

WEKO_WORKSPACE_AUTOFILL_JAMAS_XML_DATA_KEYS = {
    "identifier": False,
    "title": False,
    "creator": True,
    "type": True,
    "language": False,
    "publisher": False,
    "description": True,
    "organization": True,
    "publicationName": False,
    "issn": False,
    "eIssn": False,
    "isbn": True,
    "volume": False,
    "number": False,
    "startingPage": False,
    "pageRange": False,
    "publicationDate": True,
    "keyword": True,
    "doi": False,
    "postDate": True,
}
"""Jamas XML data keys and multiple flags."""

WEKO_WORKSPACE_AUTOFILL_JAMAS_REQUIRED_ITEM = [
    "title",
    "creator",
    "sourceTitle",
    "sourceIdentifier",
    "volume",
    "issue",
    "pageStart",
    "numPages",
    "date",
    "relation",
    "publisher",
    "description",
]
"""Jamas required item"""

WEKO_WORKSPACE_ARTICLE_TYPES = [
    "conference paper",
    "data paper",
    "departmental bulletin paper",
    "editorial",
    "journal",
    "journal article",
    "newspaper",
    "review article",
    "other periodical",
    "software paper",
    "article"
]
"""Definition of Article categories"""

WEKO_WORKSPACE_DATASET_TYPES = [
    "aggregated data",
    "clinical trial data",
    "compiled data",
    "dataset",
    "encoded data",
    "experimental data",
    "genomic data",
    "geospatial data",
    "laboratory notebook",
    "measurement and test data",
    "observational data",
    "recorded data",
    "simulation data",
    "survey data"
]
"""Definition of Dataset categories"""

WEKO_WORKSPACE_DEFAULT_FILTERS = {
    "resource_type": {
        "label": "Resource Type",
        "options": [
            "conference paper",
            "data paper",
            "departmental bulletin paper",
            "editorial",
            "journal",
            "journal article",
            "newspaper",
            "review article",
            "other periodical",
            "software paper",
            "article",
            "book",
            "book part",
            "cartographic material",
            "map",
            "conference output",
            "conference presentation",
            "conference proceedings",
            "conference poster",
            "aggregated data",
            "clinical trial data",
            "compiled data",
            "dataset",
            "encoded data",
            "experimental data",
            "genomic data",
            "geospatial data",
            "laboratory notebook",
            "measurement and test data",
            "observational data",
            "recorded data",
            "simulation data",
            "survey data",
            "image",
            "still image",
            "moving image",
            "video",
            "lecture",
            "design patent",
            "patent",
            "PCT application",
            "plant patent",
            "plant variety protection",
            "software patent",
            "trademark",
            "utility model",
            "report",
            "research report",
            "technical report",
            "policy report",
            "working paper",
            "data management plan",
            "sound",
            "thesis",
            "bachelor thesis",
            "master thesis",
            "doctoral thesis",
            "commentary",
            "design",
            "industrial design",
            "interactive resource",
            "layout design",
            "learning object",
            "manuscript",
            "musical notation",
            "peer review",
            "research proposal",
            "research protocol",
            "software",
            "source code",
            "technical documentation",
            "transcription",
            "workflow",
            "other",
        ],
        "default": [],  # 複数選択フィールド、文字列配列を保持
    },
    "peer_review": {
        "label": "Peer Review",
        "options": ["Yes", "No"],
        "default": [],  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "related_to_paper": {
        "label": "Related To Paper",
        "options": ["Yes", "No"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "related_to_data": {
        "label": "Related To Data",
        "options": ["Yes", "No"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "funder_name": {
        "label": "Funding Reference - Funder Name",
        "options": [],  # 動的フィールド、初期は空、後でリストデータに基づいて填充される
        "default": [],  # 複数選択フィールド、空配列を保持
    },
    "award_title": {
        "label": "Funding Reference - Award Title",
        "options": [],  # 動的フィールド、初期は空、後でリストデータに基づいて填充される
        "default": [],  # 複数選択フィールド、空配列を保持
    },
    "file_present": {
        "label": "File",
        "options": ["Yes", "No"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "favorite": {
        "label": "Favorite",
        "options": ["Yes", "No"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
}
"""Default filter options for the workspace item list page."""

WEKO_WORKSPACE_OA_STATUS_MAPPING = {
    "Unprocessed": _("Unlinked"),
    "Unprocessed Pending": _("Unlinked"),
    "Processing Metadata Registered": _("Metadata Registered"),
    "Processing Metadata Registered (Fulltext Requested)": _("Fulltext Requested"),
    "Processing Metadata Registered (Fulltext Obtained)": _("Fulltext Provided"),
    "Processing Metadata Not Registered (Fulltext Requested)": _("Unlinked (Fulltext Requested)"),
    "Processing Metadata Not Registered (Fulltext Obtained)": _("Unlinked (Fulltext Provided)"),
    "Processed Fulltext Opened (OA)": _("OA"),
    "Processed Fulltext Registered (Embargo)": _("Embargo OA"),
    "Processed (Not OA) Metadata Opened (Fulltext Not Opened)": _("Not OA"),
    "Processed (Not OA) Metadata Opened (Fulltext Opened Limitedly)": _("Opened Limitedly"),
    "Unregistrable No Contact Information/Undeliverable": _("Unlinked"),
    "Unregistrable No Reply": _("Unlinked"),
    "Unregistrable No Permission": _("Unlinked"),
    "Unregistrable No Fulltext": _("Unlinked"),
    "Unregistrable Other Reasons": _("Unlinked"),
    "Excluded Already Opened Elsewhere": _("Opened Elsewhere"),
    "Excluded Not Funded by Designated FA": _("Unlinked"),
    "Excluded Not Affiliated First Author": _("Unlinked"),
    "Excluded Overlapped Content": _("Unlinked"),
    "Excluded Other Reasons": _("Unlinked")
}
"""Mapping of OA status to the OA status in WEKO."""

WEKO_WORKSPACE_ITEM_SEARCH_INDEX = "{}-weko".format(index_prefix)
"""Search index for WEKO workspace item."""

WEKO_WORKSPACE_ITEM_SEARCH_TYPE = "item-v1.0.0"
"""Search type for WEKO workspace item."""

WEKO_WORKSPACE_SYS_HTTP_PROXY = ''
"""HTTP proxy"""

WEKO_WORKSPACE_SYS_HTTPS_PROXY = ''
"""HTTPS proxy"""

WEKO_WORKSPACE_REQUEST_TIMEOUT = 5
"""Request time out"""

WEKO_WORKSPACE_JAMAS_API_URL = 'https://search.jamas.or.jp/'
"""Jamas API URL"""

WEKO_WORKSPACE_CiNii_API_URL = 'https://cir.nii.ac.jp/opensearch/all'
"""CiNii API URL"""

WEKO_WORKSPACE_JALC_API_URL = 'https://api.japanlinkcenter.org/dois/'
"""JALC API URL"""

WEKO_WORKSPACE_DATACITE_API_URL = 'https://api.datacite.org/dois/'
"""DataCite API URL"""

WEKO_WORKSPACE_CINII_REQUIRED_ITEM = [
    'title',
    'creator',
    'description',
    'subject',
    'sourceTitle',
    'volume',
    'issue',
    'pageStart',
    'pageEnd',
    'numPages',
    'date',
    'publisher',
    'sourceIdentifier',
    'relation'
]
"""CiNii required item"""

WEKO_WORKSPACE_JALC_REQUIRED_ITEM = [
    'title',
    'creator',
    'sourceTitle',
    'volume',
    'issue',
    'pageStart',
    'pageEnd',
    'numPages',
    'date',
    'publisher',
    'sourceIdentifier',
    'relation'
]
"""JaLC required item"""

WEKO_WORKSPACE_DATACITE_REQUIRED_ITEM = [
    'title',
    'creator',
    'contributor',
    'description',
    'subject',
    'sourceTitle',
    'sourceIdentifier',
    'relation'
]
"""DataCite required item"""

WEKO_WORKSPACE_DATA_DEFAULT_LANGUAGE = 'en'
"""Default language for data"""
