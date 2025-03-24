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
        "label": "リソースタイプ",
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
        "label": "査読",
        "options": ["あり", "なし"],
        "default": [],  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "related_to_paper": {
        "label": "論文への関連",
        "options": ["あり", "なし"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "related_to_data": {
        "label": "根拠データへの関連",
        "options": ["あり", "なし"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "funder_name": {
        "label": "資金別情報 - 助成機関名",
        "options": [],  # 動的フィールド、初期は空、後でリストデータに基づいて填充される
        "default": [],  # 複数選択フィールド、空配列を保持
    },
    "award_title": {
        "label": "資金別情報 - 研究課題名",
        "options": [],  # 動的フィールド、初期は空、後でリストデータに基づいて填充される
        "default": [],  # 複数選択フィールド、空配列を保持
    },
    "file_present": {
        "label": "本文ファイル",
        "options": ["あり", "なし"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
    "favorite": {
        "label": "お気に入り",
        "options": ["あり", "なし"],
        "default": None,  # 単一選択フィールド、デフォルトは未選択で null を使用
    },
}
"""Default filter options for the workspace item list page."""

WEKO_WORKSPACE_OA_STATUS_MAPPING = {
    "Unprocessed": "Unlinked",
    "Unprocessed Pending": "Unlinked",
    "Processing Metadata Registered": "Metadata Registered",
    "Processing Metadata Registered (Fulltext Requested)": "Fulltext Requested",
    "Processing Metadata Registered (Fulltext Obtained)": "Fulltext Provided",
    "Processing Metadata Not Registered (Fulltext Requested)": "Unlinked (Fulltext Requested)",
    "Processing Metadata Not Registered (Fulltext Obtained)": "Unlinked (Fulltext Provided)",
    "Processed Fulltext Opened (OA)": "OA",
    "Processed Fulltext Registered (Embargo)": "Embargo OA",
    "Processed (Not OA) Metadata Opened (Fulltext Not Opened)": "Not OA",
    "Processed (Not OA) Metadata Opened (Fulltext Opened Limitedly)": "Opened Limitedly",
    "Unregistrable No Contact Information/Undeliverable": "Unlinked",
    "Unregistrable No Reply": "Unlinked",
    "Unregistrable No Permission": "Unlinked",
    "Unregistrable No Fulltext": "Unlinked",
    "Unregistrable Other Reasons": "Unlinked",
    "Excluded Already Opened Elsewhere": "Opened Elsewhere",
    "Excluded Not Funded by Designated FA": "Unlinked",
    "Excluded Not Affiliated First Author": "Unlinked",
    "Excluded Overlapped Content": "Unlinked",
    "Excluded Other Reasons": "Unlinked"
}
"""Mapping of OA status to the OA status in WEKO."""

# Error message variable definition

# Others

