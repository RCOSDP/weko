# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016, 2017 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio module that adds support for communities."""

from __future__ import absolute_import, print_function

import copy
import os
from functools import wraps

import bleach
from flask import Blueprint, abort, current_app, flash, jsonify, redirect, \
    render_template, request, url_for
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.resolver import Resolver
from invenio_records.api import Record
from weko_admin.utils import get_search_setting
from weko_index_tree.models import IndexStyle
from weko_search_ui.api import SearchSetting, get_search_detail_keyword

from invenio_communities.forms import CommunityForm, DeleteCommunityForm, \
    EditCommunityForm, SearchForm
from invenio_communities.models import Community, FeaturedCommunity
from invenio_communities.proxies import current_permission_factory
from invenio_communities.utils import Pagination, get_user_role_ids, \
    render_template_to_string

blueprint = Blueprint(
    'invenio_communities',
    __name__,
    url_prefix='/c',
    template_folder='../templates',
    static_folder='../static',
)


@blueprint.app_template_filter('sanitize_html')
def sanitize_html(value):
    """Sanitizes HTML using the bleach library."""
    return bleach.clean(
        value,
        tags=current_app.config['COMMUNITIES_ALLOWED_TAGS'],
        attributes=current_app.config['COMMUNITIES_ALLOWED_ATTRS'],
        styles=current_app.config['COMMUNITIES_ALLOWED_STYLES'],
        strip=True,
    ).strip()


def pass_community(f):
    """Decorator to pass community."""
    @wraps(f)
    def inner(community_id, *args, **kwargs):
        c = Community.get(community_id)
        if c is None:
            abort(404)
        return f(c, *args, **kwargs)
    return inner


def permission_required(action):
    """Decorator to require permission."""
    def decorator(f):
        @wraps(f)
        def inner(community, *args, **kwargs):
            permission = current_permission_factory(community, action=action)
            if not permission.can():
                abort(403)
            return f(community, *args, **kwargs)
        return inner
    return decorator


@blueprint.app_template_filter('format_item')
def format_item(item, template, name='item'):
    """Render a template to a string with the provided item in context."""
    ctx = {name: item}
    return render_template_to_string(template, **ctx)


@blueprint.app_template_filter('mycommunities_ctx')
def mycommunities_ctx():
    """Helper method for return ctx used by many views."""
    role_ids = get_user_role_ids()
    return {
        'mycommunities': Community.get_by_user(role_ids).all()
    }


# @blueprint.route('/', methods=['GET', ])
# def index():
#     """Index page with uploader and list of existing depositions."""
#     ctx = mycommunities_ctx()

#     p = request.args.get('p', type=str)
#     so = request.args.get('so', type=str)
#     page = request.args.get('page', type=int, default=1)

#     so = so or current_app.config.get('COMMUNITIES_DEFAULT_SORTING_OPTION')

#     communities = Community.filter_communities(p, so)
#     featured_community = FeaturedCommunity.get_featured_or_none()
#     form = SearchForm(p=p)
#     per_page = 10
#     page = max(page, 1)
#     p = Pagination(page, per_page, communities.count())

#     ctx.update({
#         'r_from': max(p.per_page * (p.page - 1), 0),
#         'r_to': min(p.per_page * p.page, p.total_count),
#         'r_total': p.total_count,
#         'pagination': p,
#         'form': form,
#         'title': _('Communities'),
#         'communities': communities.slice(
#             per_page * (page - 1), per_page * page).all(),
#         'featured_community': featured_community,
#     })

#     return render_template(
#         current_app.config['COMMUNITIES_INDEX_TEMPLATE'], **ctx)


@blueprint.route('/<string:community_id>/', methods=['GET'])
@pass_community
def view(community):
    """Index page with uploader and list of existing depositions.

    :param community_id: ID of the community to view.
    """
    key_val = request.args
    if key_val and 'view' in key_val:
        view_val = request.args.get("view")
    else:
        view_val = None
#    if view_val is not None and 'basic' in view_val:
#        # return redirect(url_for('.detail', community_id=community.id))
#        return generic_item(
#            community, current_app.config['COMMUNITIES_DETAIL_TEMPLATE'])

    ctx = {'community': community}
    community_id = community.id
    # Get index style
    style = IndexStyle.get(
        current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
    width = style.width if style else '3'

    height = style.height if style else None

    sort_options, display_number = SearchSetting.get_results_setting()

    detail_condition = get_search_detail_keyword('')

    # Get Facet search setting.
    display_facet_search = get_search_setting().get("display_control", {})\
        .get('display_facet_search', {}).get('status', False)
    ctx.update({
        "display_facet_search": display_facet_search,
    })

    # Get index tree setting.
    display_index_tree = get_search_setting().get("display_control", {})\
        .get('display_index_tree', {}).get('status', False)
    ctx.update({
        "display_index_tree": display_index_tree,
    })

    return render_template(
        current_app.config['THEME_FRONTPAGE_TEMPLATE'],
        sort_option=sort_options, detail_condition=detail_condition, community_id=community_id, width=width, height=height, ** ctx
    )


@blueprint.route('/<string:community_id>/content_policy/', methods=['GET'])
@pass_community
def content_policy(community):
    """Display the content policy of a community."""
    ctx = {'community': community}
    community_id = community.id
    return render_template(
        'invenio_communities/content_policy.html',
        community_id=community_id, ** ctx
    )


# @blueprint.route('/<string:community_id>/detail/', methods=['GET'])
# @pass_community
# def detail(community):
#    """Index page with uploader and list of existing depositions."""
#    return generic_item(
#        community, current_app.config['COMMUNITIES_DETAIL_TEMPLATE'])


# @blueprint.route('/<string:community_id>/search', methods=['GET'])
# @pass_community
# def search(community):
#    """Index page with uploader and list of existing depositions."""
#    return generic_item(
#        community,
#        current_app.config['COMMUNITIES_SEARCH_TEMPLATE'],
#        detail=False)


# @blueprint.route('/<string:community_id>/about/', methods=['GET'])
# @pass_community
# def about(community):
#    """Index page with uploader and list of existing depositions."""
#    return generic_item(
#        community, current_app.config['COMMUNITIES_ABOUT_TEMPLATE'])


def generic_item(community, template, **extra_ctx):
    """Index page with uploader and list of existing depositions."""
    # Check existence of community
    ctx = mycommunities_ctx()
    role_id = min(get_user_role_ids())

    ctx.update({
        'is_owner': community.id_role == role_id,
        'community': community,
        'detail': True,
    })
    ctx.update(extra_ctx)

    return render_template(template, **ctx)


# @blueprint.route('/new/', methods=['GET', 'POST'])
# @login_required
# def new():
#    """Create a new community."""
#    form = CommunityForm(formdata=request.values)
#
#    ctx = mycommunities_ctx()
#    ctx.update({
#        'form': form,
#        'is_new': True,
#        'community': None,
#    })
#
#    if form.validate_on_submit():
#
#        data = copy.deepcopy(form.data)
#
#        community_id = data.pop('identifier')
#
#        root_index_id = data.pop('index_checked_nodeId')
#
#        del data['logo']
#
#        community = Community.create(
#            community_id, current_user.get_id(), root_index_id, **data)
#
#        # Default color
#        community.color_bg1 = request.form.get('color_bg1', '#ffffff')
#        community.color_bg2 = request.form.get('color_bg2', '#ffffff')
#        community.color_frame = request.form.get('color_frame', '#dddddd')
#        community.color_header = request.form.get('color_header', '#0d5f89')
#        community.color_footer = request.form.get('color_footer', '#0d5f89')
#
#        # Create scss
#        fn = community_id + '.scss'
#        scss_file = os.path.join(current_app.static_folder,
#                                 'scss/invenio_communities/communities/' + fn)
#        # Write scss
#        lines = []
#        lines.append(
#            '$'
#            + community_id
#            + '-community-body-bg: '
#            + community.color_bg1
#            + ';')
#        lines.append(
#            '$'
#            + community_id
#            + '-community-panel-bg: '
#            + community.color_bg2
#            + ';')
#        lines.append(
#            '$'
#            + community_id
#            + '-community-panel-border: '
#            + community.color_frame
#            + ';')
#        lines.append(
#            '$'
#            + community_id
#            + '-community-header-bg: '
#            + community.color_header
#            + ';')
#        lines.append(
#            '$'
#            + community_id
#            + '-community-footer-bg: '
#            + community.color_footer
#            + ';')
#
#        lines.append('.communities {.' + community.id
#                     + '-body {background-color: $' + community_id + '-community-body-bg;}}')
#        lines.append('.communities {.' + community.id
#                     + '-panel {background-color: $' + community_id + '-community-panel-bg;}}')
#        lines.append('.communities {.' + community.id
#                     + '-panel {border-color: $' + community_id + '-community-panel-border;}}')
#        lines.append('.communities {.' + community.id
#                     + '-header {background-color: $' + community_id + '-community-header-bg;}}')
#        lines.append('.communities {.' + community.id
#                     + '-footer {background-color: $' + community_id + '-community-footer-bg;}}')
#
#        with open(scss_file, 'w', encoding='utf-8') as fp:
#            fp.writelines('\n'.join(lines))
#
#        # Add to variables
#        var_file = os.path.join(current_app.static_folder,
#                                'scss/invenio_communities/variables.scss')
#        with open(var_file, 'a', encoding='utf-8') as fp:
#            str = '@import "communities/' + community_id + '";'
#            fp.writelines(str + '\n')
#
#        file = request.files.get('logo', None)
#        if file:
#            if not community.save_logo(file.stream, file.filename):
#                form.logo.errors.append(_(
#                    'Cannot add this file as a logo. Supported formats: '
#                    'PNG, JPG and SVG. Max file size: 1.5 MB.'))
#                db.session.rollback()
#                community = None
#
#        if community:
#            db.session.commit()
#            flash("Community was successfully created.", category='success')
#            return redirect(url_for('.edit', community_id=community.id))
#
#    return render_template(
#        current_app.config['COMMUNITIES_NEW_TEMPLATE'],
#        community_form=form,
#        **ctx
#    )


# @blueprint.route('/<string:community_id>/edit/', methods=['GET', 'POST'])
# @login_required
# @pass_community
# @permission_required('community-edit')
# def edit(community):
#    """Create or edit a community."""
#    def read_color(scss_file, community):
#        # Read
#        if os.path.exists(scss_file):
#            with open(scss_file, 'r', encoding='utf-8') as fp:
#                for line in fp.readlines():
#                    line = line.strip() if line else ''
#                    if line.startswith(
#                            '$' + community.id + '-community-body-bg:'):
#                        community.color_bg1 = line[line.find('#'):-1]
#                    if line.startswith(
#                            '$' + community.id + '-community-panel-bg:'):
#                        community.color_bg2 = line[line.find('#'):-1]
#                    if line.startswith(
#                            '$' + community.id + '-community-panel-border:'):
#                        community.color_frame = line[line.find('#'):-1]
#                    if line.startswith(
#                            '$' + community.id + '-community-header-bg:'):
#                        community.color_header = line[line.find('#'):-1]
#                    if line.startswith(
#                            '$' + community.id + '-community-footer-bg:'):
#                        community.color_footer = line[line.find('#'):-1]
#        # Create
#        else:
#            community.color_bg1 = '#ffffff'
#            community.color_bg2 = '#ffffff'
#            community.color_frame = '#dddddd'
#            community.color_header = '#0d5f89'
#            community.color_footer = '#0d5f89'
#
#            # Write scss
#            lines = []
#            lines.append(
#                '$'
#                + community.id
#                + '-community-body-bg: '
#                + community.color_bg1
#                + ';')
#            lines.append(
#                '$'
#                + community.id
#                + '-community-panel-bg: '
#                + community.color_bg2
#                + ';')
#            lines.append(
#                '$'
#                + community.id
#                + '-community-panel-border: '
#                + community.color_frame
#                + ';')
#            lines.append(
#                '$'
#                + community.id
#                + '-community-header-bg: '
#                + community.color_header
#                + ';')
#            lines.append(
#                '$'
#                + community.id
#                + '-community-footer-bg: '
#                + community.color_footer
#                + ';')
#
#            lines.append('.communities {.'
#                         + community.id
#                         + '-body {background-color: $'
#                         + community.id
#                         + '-community-body-bg;}}')
#            lines.append('.communities {.'
#                         + community.id
#                         + '-panel {background-color: $'
#                         + community.id
#                         + '-community-panel-bg;}}')
#            lines.append('.communities {.'
#                         + community.id
#                         + '-panel {border-color: $'
#                         + community.id
#                         + '-community-panel-border;}}')
#            lines.append('.communities {.'
#                         + community.id
#                         + '-header {background-color: $'
#                         + community.id
#                         + '-community-header-bg;}}')
#            lines.append('.communities {.'
#                         + community.id
#                         + '-footer {background-color: $'
#                         + community.id
#                         + '-community-footer-bg;}}')
#
#            with open(scss_file, 'w', encoding='utf-8') as fp:
#                fp.writelines('\n'.join(lines))
#
#            # Add to variables
#            var_file = os.path.join(current_app.static_folder,
#                                    'scss/invenio_communities/variables.scss')
#            with open(var_file, 'a', encoding='utf-8') as fp:
#                str = '@import "communities/' + community.id + '";'
#                fp.writelines(str + '\n')
#
#        return community
#
#    fn = community.id + '.scss'
#    scss_file = os.path.join(current_app.static_folder,
#                             'scss/invenio_communities/communities/' + fn)
#    read_color(scss_file, community)
#
#    form = EditCommunityForm(formdata=request.values, obj=community)
#    deleteform = DeleteCommunityForm()
#    ctx = mycommunities_ctx()
#    ctx.update({
#        'form': form,
#        'is_new': False,
#        'community': community,
#        'deleteform': deleteform,
#    })
#
#    if form.validate_on_submit():
#        for field, val in form.data.items():
#            setattr(community, field, val)
#
#        # Get color
#        color_bg1 = request.form.get('color_bg1', '#ffffff')
#        color_bg2 = request.form.get('color_bg2', '#ffffff')
#        color_frame = request.form.get('color_frame', '#dddddd')
#        color_header = request.form.get('color_header', community.color_header)
#        color_footer = request.form.get('color_footer', community.color_footer)
#
#        # Write scss
#        lines = []
#        lines.append(
#            '$'
#            + community.id
#            + '-community-body-bg: '
#            + color_bg1
#            + ';')
#        lines.append(
#            '$'
#            + community.id
#            + '-community-panel-bg: '
#            + color_bg2
#            + ';')
#        lines.append(
#            '$'
#            + community.id
#            + '-community-panel-border: '
#            + color_frame
#            + ';')
#        lines.append(
#            '$'
#            + community.id
#            + '-community-header-bg: '
#            + color_header
#            + ';')
#        lines.append(
#            '$'
#            + community.id
#            + '-community-footer-bg: '
#            + color_footer
#            + ';')
#        lines.append('.communities {.'
#                     + community.id
#                     + '-body {background-color: $'
#                     + community.id
#                     + '-community-body-bg;}}')
#        lines.append('.communities {.'
#                     + community.id
#                     + '-panel {background-color: $'
#                     + community.id
#                     + '-community-panel-bg;}}')
#        lines.append('.communities {.'
#                     + community.id
#                     + '-panel {border-color: $'
#                     + community.id
#                     + '-community-panel-border;}}')
#        lines.append('.communities {.'
#                     + community.id
#                     + '-header {background-color: $'
#                     + community.id
#                     + '-community-header-bg;}}')
#        lines.append('.communities {.'
#                     + community.id
#                     + '-footer {background-color: $'
#                     + community.id
#                     + '-community-footer-bg;}}')
#
#        with open(scss_file, 'w', encoding='utf-8') as fp:
#            fp.writelines('\n'.join(lines))
#
#        file = request.files.get('logo', None)
#        if file:
#            if not community.save_logo(file.stream, file.filename):
#                form.logo.errors.append(_(
#                    'Cannot add this file as a logo. Supported formats: '
#                    'PNG, JPG and SVG. Max file size: 1.5 MB.'))
#
#        if not form.logo.errors:
#            db.session.commit()
#            flash("Community successfully edited.", category='success')
#            return redirect(url_for('.edit', community_id=community.id))
#
#    return render_template(
#        current_app.config['COMMUNITIES_EDIT_TEMPLATE'],
#        **ctx
#    )
#

# @blueprint.route('/<string:community_id>/delete/', methods=['POST'])
# @login_required
# @pass_community
# @permission_required('community-delete')
# def delete(community):
#    """Delete a community."""
#    deleteform = DeleteCommunityForm(formdata=request.values)
#    ctx = mycommunities_ctx()
#    ctx.update({
#        'deleteform': deleteform,
#        'is_new': False,
#        'community': community,
#    })
#
#    if deleteform.validate_on_submit():
#        fn = community.id + '.scss'
#        scss_file = os.path.join(current_app.static_folder,
#                                 'scss/invenio_communities/communities/' + fn)
#        os.remove(scss_file)
#
#        var_file = os.path.join(current_app.static_folder,
#                                'scss/invenio_communities/variables.scss')
#
#        # Delete from variables
#        key = '@import "communities/' + community.id + '";'
#        with open(var_file, "r") as vf:
#            lines = vf.readlines()
#            lines.remove(key + '\n')
#            with open(var_file, "w") as new_vf:
#                for line in lines:
#                    new_vf.write(line)
#
#        community.delete()
#        db.session.commit()
#        flash("Community was deleted.", category='success')
#        return redirect(url_for('.index'))
#    else:
#        flash("Community could not be deleted.", category='warning')
#        return redirect(url_for('.edit', community_id=community.id))
#

# @blueprint.route('/<string:community_id>/curate/', methods=['GET', 'POST'])
# @login_required
# @pass_community
# @permission_required('community-curate')
# def curate(community):
#    """Index page with uploader and list of existing depositions.
#
#    :param community_id: ID of the community to curate.
#    """
#    if request.method == 'POST':
#        action = request.json.get('action')
#        recid = request.json.get('recid')
#
#        # 'recid' is mandatory
#        if not recid:
#            abort(400)
#        if action not in ['accept', 'reject', 'remove']:
#            abort(400)
#
#        # Resolve recid to a Record
#        resolver = Resolver(
#            pid_type='recid', object_type='rec', getter=Record.get_record)
#        pid, record = resolver.resolve(recid)
#
#        # Perform actions
#        if action == "accept":
#            community.accept_record(record)
#        elif action == "reject":
#            community.reject_record(record)
#        elif action == "remove":
#            community.remove_record(record)
#
#        record.commit()
#        db.session.commit()
#        RecordIndexer().index_by_id(record.id)
#        return jsonify({'status': 'success'})
#
#    ctx = {'community': community}
#    community_id = community.id
#    community_flg = "0"
#
#    # Get index style
#    style = IndexStyle.get(
#        current_app.config['WEKO_INDEX_TREE_STYLE_OPTIONS']['id'])
#    width = style.width if style else '3'
#    height = style.height if style else None
#
#    sort_options, display_number = SearchSetting.get_results_setting()
#
#    return render_template(
#        current_app.config['COMMUNITIES_CURATE_TEMPLATE'],
#        community_id=community_id, sort_option=sort_options, width=width, height=height, **ctx)


@blueprint.route('/list/', methods=['GET', ])
def community_list():
    """Index page with uploader and list of existing depositions."""
    ctx = mycommunities_ctx()
    from weko_theme.utils import get_design_layout

    # Get the design for widget rendering
    render_page, render_widgets = get_design_layout(
        current_app.config['WEKO_THEME_DEFAULT_COMMUNITY'])
    p = request.args.get('p', type=str)
    so = request.args.get('so', type=str)
    page = request.args.get('page', type=int, default=1)

    so = so or current_app.config.get('COMMUNITIES_DEFAULT_SORTING_OPTION')

    communities = Community.filter_communities(p, so)
    featured_community = FeaturedCommunity.get_featured_or_none()
    form = SearchForm(p=p)
    per_page = 10
    page = max(page, 1)
    p = Pagination(page, per_page, communities.count())

    ctx.update({
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

    # Get display_community setting.
    display_community = get_search_setting().get("display_control", {}).get(
        'display_community', {}).get('status', False)
    ctx.update({
        "display_community": display_community
    })

    return render_template(
        'invenio_communities/communities_list.html',
        page=render_page,
        render_widgets=render_widgets,
        communityModel = Community,
        **ctx)

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("invenio_communities dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()
