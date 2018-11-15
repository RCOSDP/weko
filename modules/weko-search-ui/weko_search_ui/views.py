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

from flask import Blueprint, current_app, render_template, request
from xml.etree import ElementTree as ET
from weko_index_tree.models import IndexStyle

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

    return render_template(current_app.config['SEARCH_UI_SEARCH_TEMPLATE'],
                           index_id=cur_index_id, community_id=community_id,
                           width=width, **ctx)


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
