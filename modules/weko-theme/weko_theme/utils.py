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

from flask import current_app
from invenio_i18n.ext import current_i18n
from weko_admin.utils import set_default_language
from weko_gridlayout.utils import get_widget_design_page_with_main, \
    main_design_has_main_widget
from weko_index_tree.models import Index, IndexStyle
from weko_records_ui.ipaddr import check_site_license_permission
from weko_search_ui.api import get_search_detail_keyword


def get_weko_contents(getargs):
    """Get all contents needed for rendering WEKO frontpage."""
    community_id, ctx = get_community_id(getargs)

    # set default language base on Admin language setting
    set_default_language()

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
    for index in Index.query.all():
        if index.index_link_enabled and index.public_state:
            if hasattr(current_i18n, 'language'):
                if current_i18n.language == 'ja' and index.index_link_name:
                    index_link_list.append((index.id, index.index_link_name))
                else:
                    index_link_list.append(
                        (index.id, index.index_link_name_english))
            else:
                index_link_list.append(
                    (index.id, index.index_link_name_english))

    detail_condition = get_search_detail_keyword('')
    check_site_license_permission()

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
    if 'community' in getargs:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(getargs.get('community'))
        ctx = {'community': comm}
        community_id = comm.id
    return community_id, ctx


def get_design_layout(repository_id):
    """Get the design layout either from the page or from the main settings.

    There will only be one page or main layout per repository which has the
    main contents widget. This returns the page, or if the main layout contains
    the main contents widget, render_widgets remains True.
    :param repository_id
    :returns page, render_widgets
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
