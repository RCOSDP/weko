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

"""Blueprint for weko-search-ui."""

import time
import traceback
from xml.etree import ElementTree

from blinker import Namespace
from flask import Blueprint, current_app, flash, jsonify, render_template, request
from flask_babelex import gettext as _
from flask_login import login_required
from flask_security import current_user
from flask_wtf import FlaskForm
from invenio_db import db
from invenio_pidstore.models import PIDStatus, PersistentIdentifier
from invenio_i18n.ext import current_i18n
from sqlalchemy.sql.expression import func
from weko_admin.models import AdminSettings
from weko_admin.utils import get_search_setting
from weko_index_tree.api import Indexes
from weko_index_tree.models import IndexStyle
from weko_index_tree.utils import get_index_link_list
from weko_records.api import ItemLink, FeedbackMailList
from weko_records_ui.ipaddr import check_site_license_permission
from weko_workflow.utils import (
    get_allow_multi_thumbnail,
    get_record_by_root_ver,
    get_thumbnails,
)

from weko_search_ui.api import get_search_detail_keyword

from .api import SearchSetting
from .config import WEKO_SEARCH_TYPE_DICT
from .utils import (
    check_index_access_permissions,
    check_permission,
    get_journal_info,
)

_signals = Namespace()
searched = _signals.signal("searched")

blueprint = Blueprint(
    "weko_search_ui",
    __name__,
    template_folder="templates",
    static_folder="static",
)

blueprint_api = Blueprint(
    "weko_search_api",
    __name__,
    template_folder="templates",
    static_folder="static",
)


@blueprint.route("/search/index")
@check_index_access_permissions
def search():
    """Index Search page ui."""
    search_type = request.args.get("search_type", WEKO_SEARCH_TYPE_DICT["FULL_TEXT"])
    get_args = request.args
    community_id = ""
    ctx = {"community": None}
    cur_index_id = (
        search_type
        if search_type
        not in (
            WEKO_SEARCH_TYPE_DICT["FULL_TEXT"],
            WEKO_SEARCH_TYPE_DICT["KEYWORD"],
        )
        else None
    )
    if "community" in get_args:
        from weko_workflow.api import GetCommunity

        comm = GetCommunity.get_community_by_id(request.args.get("community"))
        ctx = {"community": comm}
        if comm is not None:
            community_id = comm.id

    # Get the design for widget rendering
    from weko_theme.utils import get_design_layout
    page, render_widgets = get_design_layout(
        community_id or current_app.config["WEKO_THEME_DEFAULT_COMMUNITY"]
    )

    # Get index style
    style = IndexStyle.get(current_app.config["WEKO_INDEX_TREE_STYLE_OPTIONS"]["id"])
    width = style.width if style else "3"

    # add at 1206 for search management
    sort_options, display_number = SearchSetting.get_results_setting()

    ts = time.time()
    # disply_setting = dict(size=display_number, timestamp=ts)
    disply_setting = dict(size=display_number)

    detail_condition = get_search_detail_keyword("")

    export_settings = AdminSettings.get(
        "item_export_settings"
    ) or AdminSettings.Dict2Obj(
        current_app.config["WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS"]
    )

    height = style.height if style else None
    if request.values.get("search_type") in (
        WEKO_SEARCH_TYPE_DICT["FULL_TEXT"],
        WEKO_SEARCH_TYPE_DICT["KEYWORD"],
    ):
        for _key in request.values:
            _val = request.values.get(_key)
            if "<" in _val or ">" in _val:
                flash(
                    _('"<" and ">" cannot be used for searching.'), category="warning"
                )
                break
    if "item_link" in get_args:
        from weko_workflow.api import WorkActivity
        from weko_workflow.views import get_main_record_detail

        activity_id = request.args.get("item_link")
        workflow_activity = WorkActivity()
        (
            activity_detail,
            item,
            steps,
            action_id,
            cur_step,
            temporary_comment,
            approval_record,
            step_item_login_url,
            histories,
            res_check,
            pid,
            community_id,
            ctx,
        ) = workflow_activity.get_activity_index_search(activity_id=activity_id)

        recid = approval_record.get("control_number", None)
        if recid:
            item_link = ItemLink.get_item_link_info(recid)
            ctx["item_link"] = item_link
        # Get files and thumbnail to set and show popup item link.
        item_link, files = get_record_by_root_ver(recid)
        is_multi_thumbnails = get_allow_multi_thumbnail(
            approval_record.get("item_type_id"), None
        )
        files_thumbnail = get_thumbnails(files, is_multi_thumbnails)

        # Get item link info.
        record_detail_alt = get_main_record_detail(activity_id, activity_detail)

        ctx.update(
            dict(
                record_org=record_detail_alt.get("record"),
                files_org=record_detail_alt.get("files"),
                thumbnails_org=record_detail_alt.get("files_thumbnail"),
            )
        )
        form = FlaskForm(request.form)
        return render_template(
            "weko_workflow/activity_detail.html",
            action_id=action_id,
            activity=activity_detail,
            allow_item_exporting=export_settings.allow_item_exporting,
            community_id=community_id,
            cur_step=cur_step,
            files_thumbnail=files_thumbnail,
            files=files,
            height=height,
            histories=histories,
            index_id=cur_index_id,
            is_enable_item_name_link=True,
            is_login=bool(current_user.get_id()),
            is_permission=check_permission(),
            item=item,
            page=page,
            pid=pid,
            form=form,
            record=approval_record,
            render_widgets=render_widgets,
            res_check=res_check,
            step_item_login_url=step_item_login_url,
            steps=steps,
            temporary_comment=temporary_comment,
            width=width,
            **ctx
        )
    else:
        journal_info = None
        index_display_format = "1"
        check_site_license_permission()
        send_info = dict()
        send_info["site_license_flag"] = (
            True if hasattr(current_user, "site_license_flag") else False
        )
        send_info["site_license_name"] = (
            current_user.site_license_name
            if hasattr(current_user, "site_license_name")
            else ""
        )
        if search_type in WEKO_SEARCH_TYPE_DICT.values():
            if (
                not search_type == WEKO_SEARCH_TYPE_DICT["INDEX"]
                and get_args.get("q", "").strip()
            ):
                searched.send(
                    current_app._get_current_object(),
                    search_args=get_args,
                    info=send_info,
                )
            if search_type == WEKO_SEARCH_TYPE_DICT["INDEX"]:
                cur_index_id = request.args.get("q", "")
                journal_info = get_journal_info(cur_index_id)
                index_info = Indexes.get_index(cur_index_id)
                if index_info:
                    index_display_format = index_info.display_format
                    if index_display_format == "2":
                        disply_setting = dict(size=100)
                        # disply_setting = dict(size=100, timestamp=ts)

        index_link_list = get_index_link_list()
        # Get Facet search setting.
        display_facet_search = (
            get_search_setting()
            .get("display_control", {})
            .get("display_facet_search", {})
            .get("status", False)
        )
        ctx.update(
            {
                "display_facet_search": display_facet_search,
            }
        )

        # Get index tree setting.
        display_index_tree = (
            get_search_setting()
            .get("display_control", {})
            .get("display_index_tree", {})
            .get("status", False)
        )
        ctx.update(
            {
                "display_index_tree": display_index_tree,
            }
        )

        # Get display_community setting.
        display_community = (
            get_search_setting()
            .get("display_control", {})
            .get("display_community", {})
            .get("status", False)
        )
        ctx.update({"display_community": display_community})

        return render_template(
            current_app.config["SEARCH_UI_SEARCH_TEMPLATE"],
            page=page,
            render_widgets=render_widgets,
            index_id=cur_index_id,
            community_id=community_id,
            sort_option=sort_options,
            disply_setting=disply_setting,
            detail_condition=detail_condition,
            width=width,
            height=height,
            index_link_enabled=style.index_link_enabled,
            index_link_list=index_link_list,
            journal_info=journal_info,
            index_display_format=index_display_format,
            allow_item_exporting=export_settings.allow_item_exporting,
            is_permission=check_permission(),
            is_login=bool(current_user.get_id()),
            **ctx
        )


@blueprint_api.route("/opensearch/description.xml", methods=["GET"])
def opensearch_description():
    """Returns WEKO3 opensearch description document.

    :return:
    """
    # create a response
    response = current_app.response_class()

    # set the returned data, which will just contain the title
    ns_opensearch = "http://a9.com/-/spec/opensearch/1.1/"

    ElementTree.register_namespace("", ns_opensearch)
    # ElementTree.register_namespace('jairo', ns_jairo)

    root = ElementTree.Element("OpenSearchDescription")

    sname = ElementTree.SubElement(root, "{" + ns_opensearch + "}ShortName")
    sname.text = current_app.config["WEKO_OPENSEARCH_SYSTEM_SHORTNAME"]

    des = ElementTree.SubElement(root, "{" + ns_opensearch + "}Description")
    des.text = current_app.config["WEKO_OPENSEARCH_SYSTEM_DESCRIPTION"]

    img = ElementTree.SubElement(root, "{" + ns_opensearch + "}Image")
    img.set("height", "16")
    img.set("width", "16")
    img.set("type", "image/x-icon")
    img.text = request.host_url + current_app.config["WEKO_OPENSEARCH_IMAGE_URL"]

    url = ElementTree.SubElement(root, "{" + ns_opensearch + "}Url")
    url.set("type", "application/atom+xml")
    url.set("template", request.host_url + "api/opensearch/search?q={searchTerms}")

    url = ElementTree.SubElement(root, "{" + ns_opensearch + "}Url")
    url.set("type", "application/atom+xml")
    url.set(
        "template",
        request.host_url + "api/opensearch/search?q={searchTerms}&amp;format=atom",
    )

    response.data = ElementTree.tostring(root)

    # update headers
    response.headers["Content-Type"] = "application/xml"
    return response


@blueprint.route("/journal_info/<int:index_id>", methods=["GET"])
def journal_detail(index_id=0):
    """Render a check view."""
    result = get_journal_info(index_id)
    return jsonify(result)


@blueprint.route("/search/feedback_mail_list", methods=["GET"])
@login_required
def search_feedback_mail_list():
    """Render a check view."""
    result = FeedbackMailList.get_feedback_mail_list()
    return jsonify(result)


@blueprint.route("/get_child_list/<int:index_id>", methods=["GET"])
def get_child_list(index_id=0):
    """Get child id list to index list display."""
    return jsonify(Indexes.get_child_id_list(index_id))


@blueprint.route("/get_path_name_dict/<string:path_str>", methods=["GET"])
def get_path_name_dict(path_str=""):
    """Get path and name."""
    path_name_dict = {}
    path_arr = path_str.split("_")
    for path in path_arr:
        index = Indexes.get_index(index_id=path)
        idx_name = index.index_name
        idx_name_en = index.index_name_english
        if current_i18n.language == "ja" and idx_name:
            path_name_dict[path] = idx_name.replace("\n", r"<br\>").replace(
                "&EMPTY&", ""
            )
        else:
            path_name_dict[path] = idx_name_en.replace("\n", r"<br\>").replace(
                "&EMPTY&", ""
            )
    return jsonify(path_name_dict)


@blueprint.route("/facet-search/get-title-and-order", methods=["POST"])
def gettitlefacet():
    """Soft getname Facet Search."""
    from weko_admin.utils import get_title_facets
    titles, order, uiTypes, isOpens, displayNumbers, searchConditions = get_title_facets()
    result = {
        "status": True,
        "data": {
            "titles": titles,
            "order": order,
            "uiTypes": uiTypes,
            "isOpens": isOpens,
            "displayNumbers": displayNumbers,
            "searchConditions": searchConditions
        },
        "isFacetLangDisplay":
            current_app.config["WEKO_SEARCH_UI_FACET_LANG_DISP_FLG"]
    }
    return jsonify(result), 200


@blueprint_api.route('/get_last_item_id', methods=['GET'])
def get_last_item_id():
    """Get last item id."""
    result = {"last_id": ""}
    try:
        is_super = any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in current_user.roles)

        if is_super:
            data = db.session.query(
                func.max(
                    func.to_number(
                        PersistentIdentifier.pid_value,
                        current_app.config["WEKO_SEARCH_UI_TO_NUMBER_FORMAT"]
                    )
                )
            ).filter(
                PersistentIdentifier.status == PIDStatus.REGISTERED,
                PersistentIdentifier.pid_type == 'recid',
                PersistentIdentifier.pid_value.notlike("%.%")
            ).one_or_none()
            if data[0]:
                result["last_id"] = str(data[0])
        else:
            from invenio_indexer.api import RecordIndexer
            from invenio_communities.models import Community
            index_id_list = []
            repositories = Community.get_repositories_by_user(current_user)
            for repository in repositories:
                index = Indexes.get_child_list_recursive(repository.root_node_id)
                index_id_list.extend(index)

            index = current_app.config['SEARCH_UI_SEARCH_INDEX']
            query = {
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "bool": {
                                    "must_not": {
                                        "regexp": {
                                            "control_number": ".*\\..*"
                                        }
                                    }
                                }
                            },
                            {
                                "terms": {
                                    "path": index_id_list
                                }
                            }
                        ]
                    }
                },
                "size": 1,
                "_source": False,
                "sort": [
                    {
                        "control_number": {
                            "order": "desc"
                        }
                    }
                ]
            }
            results = RecordIndexer().client.search(index=index, body=query)
            if "hits" in results and "hits" in results["hits"] and results["hits"]["hits"]:
                result["last_id"] = results["hits"]["hits"][0].get("sort", [])
    except Exception as ex:
        current_app.logger.error(ex)
        traceback.print_exc()
    return jsonify(data=result), 200

@blueprint.teardown_request
@blueprint_api.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("weko_search_ui dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()
