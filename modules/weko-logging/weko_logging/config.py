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


"""Configuration for WEKO-Logging.

Sentry can, in addition to the configuration variables listed, be further
configured with the folllowing configuration variables (see
`Raven <https://docs.sentry.io/clients/python/integrations/flask/#settings>`_
for further details):

- ``SENTRY_AUTO_LOG_STACKS``
- ``SENTRY_EXCLUDE_PATHS``
- ``SENTRY_INCLUDE_PATHS``
- ``SENTRY_MAX_LENGTH_LIST``
- ``SENTRY_MAX_LENGTH_STRING``
- ``SENTRY_NAME``
- ``SENTRY_PROCESSORS``
- ``SENTRY_RELEASE``
- ``SENTRY_SITE_NAME``
- ``SENTRY_TAGS``
- ``SENTRY_TRANSPORT``


.. note::

   Celery does not deal well with the threaded Sentry transport, so you should
   make sure that your **Celery workers** are configured with:

   .. code-block:: python

      SENTRY_TRANSPORT = 'raven.transport.http.HTTPTransport'
"""

# ----------
# FILESYSTEM
# ----------
WEKO_LOGGING_FS_LOGFILE = "{instance_path}/weko-logging.log"
"""Enable logging to the filesystem."""

WEKO_LOGGING_FS_PYWARNINGS = None
"""Enable logging of Python warnings to filesystem logging."""

WEKO_LOGGING_FS_WHEN = "D"
"""Number of rotated log files to keep.

Set to a valid Python level: ``H``, ``D``.
H - Hours
D - Days
"""

WEKO_LOGGING_FS_INTERVAL = 1
"""Number of rotated log files to keep."""

WEKO_LOGGING_FS_BACKUPCOUNT = 31
"""Number of rotated log files to keep."""

WEKO_LOGGING_FS_LEVEL = "ERROR"
"""Filesystem logging level.

Set to a valid Python logging level: ``CRITICAL``, ``ERROR``, ``WARNING``,
``INFO``, ``DEBUG``, or ``NOTSET``.
"""

WEKO_LOGGING_USER_ACTIVITY_DB_SETTING = {
   "log_level": "ERROR",
   "delete": {
      "when": "months",
      "interval": 3
   }
}
"""User activity logging to the database."""

WEKO_LOGGING_USER_ACTIVITY_STREAM_SETTING = {
   "log_level": "ERROR"
}
"""User activity logging to the stream."""

WEKO_LOGGING_OPERATION_MASTER = {
   "GENERAL": {
      "id": 1,
      "label": "一般",
      "operation": {
         "LOGIN": {
            "id": 1,
            "label": "ログイン",
            "target": "user",
         },
         "LOGOUT": {
            "id": 2,
            "label": "ログアウト",
            "target": "user"
         }
      }
   },
   "ITEM_TYPE": {
      "id": 10,
      "label": "アイテムタイプ操作",
      "operation": {
         "ITEM_TYPE_CREATE": {
            "id": 1,
            "label": "アイテムタイプ登録",
            "target": "itemtype",
         },
         "ITEM_TYPE_UPDATE": {
            "id": 2,
            "label": "アイテムタイプ編集",
            "target": "itemtype"
         },
         "ITEM_TYPE_DELETE": {
            "id": 3,
            "label": "アイテムタイプ削除",
            "target": "itemtype"
         },
         "ITEM_TYPE_MAPPING_CREATE": {
            "id": 4,
            "label": "マッピング登録",
            "target": "itemtype"
         },
         "ITEM_TYPE_MAPPING_UPDATE": {
            "id": 5,
            "label": "マッピング編集",
            "target": "itemtype"
         },
         "ITEM_TYPE_MAPPING_DELETE": {
            "id": 6,
            "label": "マッピング削除",
            "target": "itemtype"
         }
      }
   },
   "ITEM": {
      "id": 11,
      "label": "アイテム操作",
      "operation": {
         "ITEM_CREATE": {
            "id": 1,
            "label": "アイテム登録",
            "target": "item",
         },
         "ITEM_UPDATE": {
            "id": 2,
            "label": "アイテム更新",
            "target": "item"
         },
         "ITEM_DELETE": {
            "id": 3,
            "label": "アイテム削除",
            "target": "item",
         },
         "ITEM_DELETE_REQUEST": {
            "id": 4,
            "label": "アイテム削除申請",
            "target": "item",
         },
         "ITEM_IMPORT": {
            "id": 5,
            "label": "アイテムインポート",
            "target": None,
         },
         "ITEM_BULK_CREATE": {
            "id": 6,
            "label": "アイテム一括登録",
            "target": None,
         },
         "ITEM_BULK_DELETE": {
            "id": 7,
            "label": "アイテム一括削除",
            "target": None,
         },
         "ITEM_CREATE_LINK": {
            "id": 8,
            "label": "アイテム間連携登録",
            "target": "item",
         },
         "ITEM_UPDATE_LINK": {
            "id": 9,
            "label": "アイテム間連携変更",
            "target": "item",
         },
         "ITEM_DELETE_LINK": {
            "id": 10,
            "label": "アイテム間連携削除",
            "target": "item",
         },
         "ITEM_ASSIGN_DOI": {
            "id": 11,
            "label": "DOI付与",
            "target": "item",
         },
         "ITEM_WITHDRAW_DOI": {
            "id": 12,
            "label": "DOI取り下げ",
            "target": "item",
         },
         "ITEM_PUBLISH": {
            "id": 13,
            "label": "アイテム公開",
            "target": "item",
         },
         "ITEM_UNPUBLISH": {
            "id": 14,
            "label": "アイテム非公開",
            "target": "item",
         },
         "ITEM_EXTERNAL_LINK": {
            "id": 15,
            "label": "外部へのアイテム情報連携",
            "target": "item",
         }
      }
   },
   "FILE": {
      "id": 12,
      "label": "ファイル操作",
      "operation": {
         "FILE_CREATE": {
            "id": 1,
            "label": "ファイル登録",
            "target": "file",
         },
         "FILE_UPDATE": {
            "id": 2,
            "label": "ファイル変更",
            "target": "file",
         },
         "FILE_DELETE": {
            "id": 3,
            "label": "ファイル削除",
            "target": "file",
         },
         "FILE_REQUEST_MAIL": {
            "id": 4,
            "label": "リクエストメール",
            "target": "file",
         },
         "FILE_DOWNLOAD": {
            "id": 5,
            "label": "ファイルダウンロード",
            "target": "file",
         }
      }
   },
   "WORKFLOW": {
      "id": 20,
      "label": "ワークフロー操作",
      "operation": {
         "WORKFLOW_CREATE": {
            "id": 1,
            "label": "ワークフロー登録",
            "target": "workflow",
         },
         "WORKFLOW_UPDATE": {
            "id": 2,
            "label": "ワークフロー変更",
            "target": "workflow"
         },
         "WORKFLOW_DELETE": {
            "id": 3,
            "label": "ワークフロー削除",
            "target": "workflow"
         },
      }
   },
   "INDEX": {
      "id": 21,
      "label": "インデックス操作",
      "operation": {
         "INDEX_CREATE": {
            "id": 1,
            "label": "インデックス登録",
            "target": "index",
         },
         "INDEX_UPDATE": {
            "id": 2,
            "label": "インデックス変更",
            "target": "index",
         },
         "INDEX_DELETE": {
            "id": 3,
            "label": "インデックス削除",
            "target": "index",
         },
      }
   },
   "AUTHOR_DB": {
      "id": 22,
      "label": "著者DB",
      "operation": {
         "AUTHOR_CREATE": {
            "id": 1,
            "label": "著者情報登録",
            "target": "author",
         },
         "AUTHOR_UPDATE": {
            "id": 2,
            "label": "著者情報変更",
            "target": "author",
         },
         "AUTHOR_DELETE": {
            "id": 3,
            "label": "著者情報削除",
            "target": "author",
         },
      }
   }
}

WEKO_LOGGING_LOG_EXPORT_TEMPLATE = "weko_logging/admin/export_log.html"

WEKO_LOGGING_EXPORT_CACHE_STATUS_KEY = "weko_user_activity_log_export_status"