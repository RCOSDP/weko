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

from flask import Blueprint, current_app, render_template, request, \
    redirect, url_for, make_response, jsonify
from xml.etree import ElementTree as ET
from weko_index_tree.models import Index, IndexStyle
from weko_index_tree.api import Indexes
from invenio_indexer.api import RecordIndexer
from .api import SearchSetting
from weko_search_ui.api import get_search_detail_keyword
from invenio_i18n.ext import current_i18n

blueprint = Blueprint(
    'weko_search_ui',
    __name__,
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
    'weko_search_ui',
    __name__,
    # url_prefix='/',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route("/search/index")
def search():
    """ Index Search page ui."""
    search_type = request.args.get('search_type', '0')
    getArgs= request.args
    community_id = ""
    ctx = {'community': None}
    cur_index_id = search_type if search_type not in ('0', '1', ) else None
    if 'community' in getArgs:
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id

    # Get index style
    style = IndexStyle.get(current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    width = style.width if style else '3'

    # add at 1206 for search management
    sort_options, display_number = SearchSetting.get_results_setting()
    disply_setting =dict(size=display_number)

    detail_condition = get_search_detail_keyword('')

    height = style.height if style else None

    index_link_list = []
    for index in Index.query.all():
        if index.index_link_enabled == True and index.public_state == True:
            if hasattr(current_i18n, 'language'):
                if current_i18n.language == 'ja' and index.index_link_name:
                    index_link_list.append((index.id, index.index_link_name))
                else:
                    index_link_list.append((index.id, index.index_link_name_english))
            else:
                index_link_list.append((index.id, index.index_link_name_english))

    if 'management' in getArgs:
        return render_template(current_app.config['WEKO_ITEM_MANAGEMENT_TEMPLATE'],
                               index_id=cur_index_id, community_id=community_id,
                               width=width, height=height, **ctx)
    else:
        return render_template(current_app.config['SEARCH_UI_SEARCH_TEMPLATE'],
                               index_id=cur_index_id, community_id=community_id,
                               sort_option=sort_options, disply_setting=disply_setting,
                               detail_condition=detail_condition, width=width, height=height,
                               index_link_enabled=style.index_link_enabled,
                               index_link_list=index_link_list, **ctx)



@blueprint_api.route('/opensearch/description.xml', methods=['GET'])
def opensearch_description():
    """
    Returns WEKO3 opensearch description document.
    :return:
    """

    # create a response
    response = current_app.response_class()

    # set the returned data, which will just contain the title
    ns_opensearch = "http://a9.com/-/spec/opensearch/1.1/"
    # ns_jairo = "jairo.nii.ac.jp/opensearch/1.0/"

    ET.register_namespace('', ns_opensearch)
    # ET.register_namespace('jairo', ns_jairo)

    root = ET.Element('OpenSearchDescription')

    sname = ET.SubElement(root, '{'+ ns_opensearch + '}ShortName')
    sname.text = current_app.config['WEKO_OPENSEARCH_SYSTEM_SHORTNAME']

    des = ET.SubElement(root, '{'+ ns_opensearch + '}Description')
    des.text = current_app.config['WEKO_OPENSEARCH_SYSTEM_DESCRIPTION']

    img = ET.SubElement(root, '{'+ ns_opensearch + '}Image')
    img.set('height', '16')
    img.set('width', '16')
    img.set('type', 'image/x-icon')
    img.text = request.host_url + \
               current_app.config['WEKO_OPENSEARCH_IMAGE_URL']

    url = ET.SubElement(root, '{'+ ns_opensearch + '}Url')
    url.set('type', 'application/atom+xml')
    url.set('template', request.host_url +
            'api/opensearch/search?q={searchTerms}')

    url = ET.SubElement(root, '{'+ ns_opensearch + '}Url')
    url.set('type', 'application/atom+xml')
    url.set('template', request.host_url +
            'api/opensearch/search?q={searchTerms}&amp;format=atom')

    response.data = ET.tostring(root)

    # update headers
    response.headers['Content-Type'] = 'application/xml'
    return response


@blueprint.route("/item_management/save", methods=['POST'])
def save_sort():
    """ Save custom sort"""
    try:
        data = request.get_json()
        index_id = data.get("q_id")
        sort_data = data.get("sort")

        # save data to DB
        item_sort={}
        for sort in sort_data:
            item_sort[sort.get('id')]=sort.get('custom_sort').get(index_id)

        Indexes.set_item_sort_custom(index_id, item_sort)

        # update es
        fp = Indexes.get_self_path(index_id)
        Indexes.update_item_sort_custom_es(fp.path, sort_data)

        jfy = {}
        jfy['status'] = 200
        jfy['message'] = 'Data is successfully updated.'
        return make_response(jsonify(jfy), jfy['status'])
    except Exception as ex:
        jfy['status'] = 405
        jfy['message'] = 'Error'
        return make_response(jsonify(jfy), jfy['status'])
