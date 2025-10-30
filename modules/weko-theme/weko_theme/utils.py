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

"""Utils for weko-theme."""

import time
from datetime import date, timedelta

from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl.query import QueryString, Range
from flask import current_app, request
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_communities.forms import SearchForm
from invenio_communities.models import Community, FeaturedCommunity
from invenio_communities.utils import Pagination
from invenio_i18n.ext import current_i18n
from invenio_search import RecordsSearch
from weko_admin.models import AdminSettings, RankingSettings, SearchManagement
from weko_admin.utils import get_search_setting
from weko_gridlayout.services import WidgetDesignServices
from weko_gridlayout.utils import get_widget_design_page_with_main, \
    main_design_has_main_widget
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index, IndexStyle
from weko_index_tree.utils import get_index_link_list, filter_index_list_by_role
from weko_items_ui.utils import get_ranking
from weko_records_ui.ipaddr import check_site_license_permission
from weko_search_ui.api import SearchSetting, get_search_detail_keyword
from weko_search_ui.utils import check_permission, get_journal_info
from weko_schema_ui.models import PublishStatus


def get_weko_contents(getargs):
    """Get all contents needed for rendering WEKO frontpage."""
    community_id, ctx = get_community_id(getargs)

    # Index style
    style = IndexStyle.get(
        current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    if not style:
        IndexStyle.create(
            current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'],
            width=3,
            height=None)
        style = IndexStyle.get(
            current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    width = style.width
    height = style.height
    index_link_enabled = style.index_link_enabled

    index_link_list = []
    if index_link_enabled:
        index_link_list = get_index_link_list()

    detail_condition = get_search_detail_keyword('')
    check_site_license_permission()

    # Get Facet search setting.
    display_facet_search = get_search_setting().get("display_control", {}).get(
        'display_facet_search', {}).get('status', False)
    ctx.update({
        "display_facet_search": display_facet_search
    })

    # Get display_index_tree setting.
    display_index_tree = get_search_setting().get("display_control", {}).get(
        'display_index_tree', {}).get('status', False)
    ctx.update({
        "display_index_tree": display_index_tree
    })

    # Get display_community setting.
    display_community = get_search_setting().get("display_control", {}).get(
        'display_community', {}).get('status', False)
    ctx.update({
        "display_community": display_community
    })

    return dict(
        community_id=community_id,
        detail_condition=detail_condition,
        width=width, height=height,
        index_link_list=index_link_list,
        index_link_enabled=index_link_enabled,
        **ctx
    )


def get_community_id(getargs):  # TODO: Use this to refactor
    """Get the community data for specific args."""
    ctx = {'community': None}
    community_id = ""
    if 'c' in getargs:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(getargs.get('c'))
        ctx = {'community': comm}
        if comm is not None:
            community_id = comm.id
    return community_id, ctx


def get_design_layout(repository_id):
    """Get the design layout either from the page or from the main settings.

    There will only be one page or main layout per repository which has the
    main contents widget. This returns the page, or if the main layout contains
    the main contents widget, render_widgets remains True.

    Args:
        repository_id (_type_): _description_

    Returns:
        _type_: page, render_widgets
    """
    if not repository_id:
        return None, False

    main_has_main = main_design_has_main_widget(repository_id)
    page_with_main = get_widget_design_page_with_main(repository_id)

    # Main layout has main contents widget, so render widgets as normal
    if main_has_main:
        return None, True

    # Page has main contents widget
    # OR
    # No page has main contents widget, disable widgets
    return page_with_main, False


def has_widget_design(repository_id, current_language):
    """Check repository as widget design.

    :param repository_id: Repository Id
    :param current_language: Current language
    :return:
    """
    widget_design_setting = WidgetDesignServices.get_widget_design_setting(
        repository_id, current_language)
    if widget_design_setting and widget_design_setting.get('widget-settings'):
        return True
    else:
        return False


class MainScreenInitDisplaySetting:
    """Main screen initial display setting."""

    __INDEX_SEARCH_RESULT_VAL = "0"
    __RANKING_VAL = "1"
    __COMMUNITIES_VAL = "2"
    __INDEX_OF_NEWEST_ITEM_REGISTERED = "0"
    __SPECIFIC_INDEX = "1"

    @classmethod
    def get_init_display_setting(cls) -> dict:
        """Get main screen initial display setting.

        :return:initial display setting
        """
        search_setting = SearchManagement.get()
        if search_setting and search_setting.init_disp_setting:
            init_display_setting_data = search_setting.init_disp_setting
        else:
            init_display_setting_data = current_app.config[
                'WEKO_ADMIN_MANAGEMENT_OPTIONS']['init_disp_setting']

        # Get setting data.
        init_display_setting = init_display_setting_data[
            'init_disp_screen_setting']
        init_disp_index_disp_method = init_display_setting_data[
            'init_disp_index_disp_method']
        init_disp_index = init_display_setting_data['init_disp_index']

        main_screen_display_setting = {
            "init_display_setting": init_display_setting
        }

        if init_display_setting == cls.__INDEX_SEARCH_RESULT_VAL:
            cls.__index_search_result(init_disp_index,
                                      init_disp_index_disp_method,
                                      main_screen_display_setting)
        elif init_display_setting == cls.__RANKING_VAL:
            cls.__ranking(main_screen_display_setting)

        elif init_display_setting == cls.__COMMUNITIES_VAL:
            cls.__communities(main_screen_display_setting)

        return main_screen_display_setting

    @classmethod
    def __communities(cls, main_screen_display_setting):
        from invenio_communities.views.ui import mycommunities_ctx
        ctx = mycommunities_ctx()
        p = request.args.get('p', type=str)
        so = request.args.get('so', type=str)
        page = request.args.get('page', type=int, default=1)
        so = so or current_app.config.get(
            'COMMUNITIES_DEFAULT_SORTING_OPTION')
        communities = Community.filter_communities(p, so)
        featured_community = FeaturedCommunity.get_featured_or_none()
        form = SearchForm(p=p)
        per_page = 10
        page = max(page, 1)
        p = Pagination(page, per_page, communities.count())
        main_screen_display_setting.update({
            'r_from': max(p.per_page * (p.page - 1), 0),
            'r_to': min(p.per_page * p.page, p.total_count),
            'r_total': p.total_count,
            'pagination': p,
            'form': form,
            'title': _('Communities'),
            'communities': communities.slice(
                per_page * (page - 1), per_page * page).all(),
            'featured_community': featured_community,
        })
        main_screen_display_setting.update(ctx)

    @classmethod
    def __ranking(cls, main_screen_display_setting):
        from weko_items_ui.utils import get_ranking

        ranking_settings = RankingSettings.get()
        # get statistical period
        end_date = date.today()
        start_date = date.today()
        is_show = False
        if ranking_settings:
            start_date = end_date - timedelta(
                days=int(ranking_settings.statistical_period))
            main_screen_display_setting['rankings'] = get_ranking(
                ranking_settings)
            is_show = ranking_settings.is_show
        main_screen_display_setting['is_show'] = is_show
        main_screen_display_setting['start_date'] = start_date
        main_screen_display_setting['end_date'] = end_date

    @classmethod
    def __index_search_result(cls, init_disp_index, init_disp_index_disp_method,
                              main_screen_display_setting):
        export_settings = (
            AdminSettings.get('item_export_settings')
            or AdminSettings.Dict2Obj(
                current_app.config[
                    'WEKO_ADMIN_DEFAULT_ITEM_EXPORT_SETTINGS']
            )
        )
        sort_options, display_number = SearchSetting.get_results_setting()
        # Default index display format
        display_format = '1'
        if init_disp_index_disp_method == cls.__INDEX_OF_NEWEST_ITEM_REGISTERED:
            init_disp_index, display_format = cls.__get_last_publish_index()
        elif init_disp_index_disp_method == cls.__SPECIFIC_INDEX:
            current_index = Indexes.get_index(index_id=init_disp_index)
            if current_index:
                display_format = current_index.display_format
        if display_format == '2':
            display_number = 100

        if not init_disp_index:
            # In case is not found the index
            # set main screen initial display to the default
            main_screen_display_setting['init_display_setting'] = "-1"
        else:
            main_screen_display_setting.update({
                "sort_option": sort_options,
                "index_id": init_disp_index,
                "index_display_format": display_format,
                "disply_setting": {},
                "search_hidden_params": {
                    "search_type": current_app.config['WEKO_SEARCH_TYPE_DICT'][
                        'INDEX'],
                    "q": init_disp_index,
                    "size": display_number,
                    "timestamp": time.time(),
                    "is_search": 1,
                },
                "journal_info": get_journal_info(init_disp_index),
                "allow_item_exporting": export_settings.allow_item_exporting,
                "is_permission": check_permission(),
                "is_login": bool(current_user.get_id()),
            })

    @classmethod
    def __get_last_publish_record(cls):
        query_string = "relation_version_is_last:true AND publish_status: {}".format(PublishStatus.PUBLIC.value)
        query_range = {'publish_date': {'lte': 'now'}}
        result = []
        try:
            search = RecordsSearch(
                index=current_app.config['SEARCH_UI_SEARCH_INDEX'])
            search = search.query(QueryString(query=query_string))
            search = search.filter(Range(**query_range))
            search = search.sort('-publish_date', '-_updated')
            search_result = search.execute().to_dict()
            result = search_result.get('hits', {}).get('hits', [])
        except NotFoundError as e:
            current_app.logger.debug("Indexes do not exist yet: ", str(e))
        return result

    @classmethod
    def __get_last_publish_index(cls):
        def __last_index(_path: list):
            _last_index = None
            last_update = None
            for index in _path:
                tmp_index = index.split("/")[-1]
                if tmp_index in public_indexes:
                    _public_index = public_indexes.get(tmp_index, {})
                    if (last_update is None
                            or last_update < _public_index.get('updated')):
                        _last_index = tmp_index
                        last_update = _public_index.get('updated')
            return _last_index

        records = cls.__get_last_publish_record()
        public_indexes = {}
        index_list = filter_index_list_by_role(Indexes.get_public_indexes())
        cls.__get_public_indexes(index_list, public_indexes)
        last_index = ""
        for record in records:
            path = record.get('_source').get('path')
            last_index = __last_index(path)
            if last_index is not None:
                break
        display_format = public_indexes.get(last_index, {}).get(
            'display_format',
            '1')
        return last_index, display_format

    @classmethod
    def __get_public_indexes(cls, indexes: list, index_dict: dict):
        public_index_list = {}
        for i in indexes:
            public_index_list[i.id] = {
                'parent': i.parent,
                'public_state': i.public_state
            }
        for _index in indexes:
            pub_flag = _check_parent_permission(_index.id, public_index_list)
            if pub_flag and _index.id and _index.public_state:
                index_dict[str(_index.id)] = {
                    'updated': _index.updated,
                    'display_format': _index.display_format,
                }

def _check_parent_permission(index_id, public_index_list: dict):
    parent_id = public_index_list.get(index_id, {}).get('parent')
    if parent_id == 0:
        pub_flag = public_index_list.get(index_id, {}).get('public_state')
        public_index_list[index_id]['pub_flag'] = pub_flag
        return pub_flag
    else:
        if 'pub_flag' in public_index_list.get(index_id, {}):
            return public_index_list[index_id]['pub_flag']
        elif index_id not in public_index_list.keys():
            return False
        elif parent_id not in public_index_list.keys():
            public_index_list[index_id]['pub_flag'] = False
            return False
        else:
            pub_flag = _check_parent_permission(parent_id, public_index_list)
            public_index_list[index_id]['pub_flag'] = pub_flag
            return pub_flag
