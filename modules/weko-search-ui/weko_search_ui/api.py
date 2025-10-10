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

"""WEKO3 module docstring."""

import unicodedata
import markupsafe
from operator import index

from flask import current_app, json
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_db import db
from invenio_i18n.ext import current_i18n
from weko_admin import config as ad_config
from weko_admin.models import SearchManagement as sm
from weko_index_tree.api import Indexes
from weko_records.utils import get_keywords_data_load


class SearchSetting(object):
    """About search setting."""

    @classmethod
    def get_results_setting(cls):
        """Get result setting."""
        res = sm.get()
        options = dict()
        sort_options = dict()
        display_number = 20
        if res:
            display_number = res.default_dis_num
            res = res.sort_setting.get("allow")
        else:
            return current_app.config["RECORDS_REST_SORT_OPTIONS"], display_number

        for x in res:
            if isinstance(x, dict):
                key_str = x.get("id")
                key = key_str[0 : key_str.rfind("_", 1)]
                val = (
                    current_app.config["RECORDS_REST_SORT_OPTIONS"]
                    .get(current_app.config["SEARCH_UI_SEARCH_INDEX"])
                    .get(key)
                )
                if key not in options.keys():
                    options[key] = val

        sort_options[current_app.config["SEARCH_UI_SEARCH_INDEX"]] = options

        return sort_options, display_number

    @classmethod
    def get_default_sort(cls, search_type, root_flag=False):
        """Get default sort."""
        res = sm.get()
        sort_str = None
        if res:
            if search_type == current_app.config["WEKO_SEARCH_TYPE_KEYWORD"]:
                sort_str = res.default_dis_sort_keyword
            else:
                sort_str = res.default_dis_sort_index
        else:
            if search_type == current_app.config["WEKO_SEARCH_TYPE_KEYWORD"]:
                sort_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS[
                    "dlt_keyword_sort_selected"
                ]
            else:
                sort_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS[
                    "dlt_index_sort_selected"
                ]

        sort_key = sort_str[0 : sort_str.rfind("_", 1)]
        sort = sort_str[sort_str.rfind("_", 1) + 1 :]

        if root_flag and "custom_sort" in sort_key:
            if search_type == current_app.config["WEKO_SEARCH_TYPE_KEYWORD"]:
                sort_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS[
                    "dlt_keyword_sort_selected"
                ]
            else:
                sort_str = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS[
                    "dlt_index_sort_selected"
                ]
            sort_key = sort_str[0 : sort_str.rfind("_", 1)]
            sort = sort_str[sort_str.rfind("_", 1) + 1 :]

        return sort_key, sort

    @classmethod
    def get_sort_key(cls, key_str):
        """Get sort key."""
        sort_key = (
            current_app.config["RECORDS_REST_SORT_OPTIONS"]
            .get(current_app.config["SEARCH_UI_SEARCH_INDEX"], {})
            .get(key_str, {})
            .get("fields")
        )
        if isinstance(sort_key, list) and len(sort_key) > 0:
            return sort_key[0]
        return None

    @classmethod
    def get_custom_sort(cls, index_id, sort_type):
        """Get custom sort."""
        if sort_type == "asc":
            factor_obj = Indexes.get_item_sort(index_id)
            script_str = {
                "_script": {
                    "script": {
                        "source": 'if(params.factor.get(doc["control_number"].value.toString())!=null){params.factor.get(doc["control_number"].value.toString())}else{Integer.MAX_VALUE}',
                        "lang": "painless",
                        "params": {"factor": factor_obj},
                    },
                    "type": "number",
                    "order": "asc",
                }
            }
            default_sort = {"_created": {"order": "asc", "unmapped_type": "long"}}
        else:
            factor_obj = Indexes.get_item_sort(index_id)
            script_str = {
                "_script": {
                    "script": {
                        "source": 'if(params.factor.get(doc["control_number"].value.toString())!=null){params.factor.get(doc["control_number"].value.toString())}else{Integer.MAX_VALUE}',
                        "lang": "painless",
                        "params": {"factor": factor_obj},
                    },
                    "type": "number",
                    "order": "desc",
                }
            }
            default_sort = {"_created": {"order": "desc", "unmapped_type": "long"}}

        return script_str, default_sort

    @classmethod
    def get_nested_sorting(cls, key_str):
        """Get nested sorting object."""
        nested_sorting = None
        sort_option = (
            current_app.config["RECORDS_REST_SORT_OPTIONS"]
            .get(current_app.config["SEARCH_UI_SEARCH_INDEX"])
            .get(key_str)
        )
        if sort_option:
            nested_sorting = sort_option.get("nested")
        return nested_sorting


def get_search_detail_keyword(str_):
    """Get search detail keyword."""
    res = sm.get()
    options = None
    key_options = dict()
    if res:
        options = res.search_conditions
    else:
        options = ad_config.WEKO_ADMIN_MANAGEMENT_OPTIONS["detail_condition"]

    item_type_list = get_keywords_data_load("")
    check_val = []
    for x in item_type_list:
        sub = dict(id=x[0], contents=x[0], checkStus=False)
        check_val.append(sub)

    check_val2 = []
    if current_user and current_user.is_authenticated:
        index_browsing_tree = Indexes.get_browsing_tree()
    else:
        index_browsing_tree = Indexes.get_browsing_reset_tree()
    for indextree in index_browsing_tree:
        index_parelist = []
        index_list = get_childinfo(indextree, index_parelist)

        for idx in index_list:
            sub2 = dict(id=idx["id"], contents=idx["parent_name"], checkStus=False)
            check_val2.append(sub2)

    for k_v in options:
        if k_v.get("id") == "itemtype":
            k_v["check_val"] = check_val
        # detail search for index
        elif k_v.get("id") == "iid":
            k_v["check_val"] = check_val2
        
        if k_v.get("contents") == "":
            contents_value = k_v.get("contents_value")
            k_v["contents"] = contents_value["en"]
            for key_lang in contents_value.keys():
                if key_lang == current_i18n.language:
                    k_v["contents"] = contents_value[key_lang]
        if k_v.get("check_val"):
            if k_v.get("id") != "iid":
                for val in k_v.get("check_val"):
                    if val.get("contents"):
                        val["contents"] = escape_str(_(val["contents"]))
                    if val.get("id") and isinstance(val.get("id"), str):
                        val["id"] = escape_str(_(val["id"]))
    key_options["condition_setting"] = options

    key_options_str = json.dumps(key_options)
    key_options_str.replace("False", "false")
    key_options_str.replace("True", "true")

    return key_options_str


def get_childinfo(index_tree, result_list=[], parename=""):
    """Get childinfo.

    Args:
        index_tree (type): description
        result_list (list, optional): description. Defaults to [].
        parename (str, optional): description. Defaults to "".

    Returns:
        [type]: [description]
    """
    # current_app.logger.debug("index_tree: {0}".format(index_tree))
    if isinstance(index_tree, dict):
        if "pid" in index_tree.keys():
            if index_tree["pid"] != 0:
                pname = parename + "/" + index_tree["name"]
                pid = index_tree["parent"] + "/" + str(index_tree["cid"])
            else:
                pname = index_tree["name"]
                pid = index_tree["cid"]

            data = {
                "id": index_tree["cid"],
                "index_name": index_tree["name"],
                "parent_id": pid,
                "parent_name": pname,
            }
            result_list.append(data)

        if "children" in index_tree.keys():
            for childlist in index_tree["children"]:
                if childlist:
                    get_childinfo(childlist, result_list, pname)

    return result_list

def escape_str(s):
    """remove escape character from string

    :argument
        s -- {str} A string removes the escape character.
    :return
        s -- {str} string removing escape character.
    """

    s = unicodedata.normalize("NFKD", s)
    s = repr(markupsafe.escape(s))[8:-2]

    #s = repr(s)
    #if 'Markup' == s[:6]:
    #    s = s[8:-2]
    #else:
    #    s = s[1:-1]

    return s
