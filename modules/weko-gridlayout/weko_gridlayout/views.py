# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 National Institute of Informatics.
#
# weko-gridlayout is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module of weko-gridlayout."""
from __future__ import absolute_import, print_function

import six

from datetime import date, timedelta

from flask import Blueprint, abort, current_app, jsonify, render_template, \
    request
from flask_babelex import gettext as _
from flask_login import login_required
from werkzeug.exceptions import NotFound
from sqlalchemy.orm.exc import NoResultFound

from .api import WidgetItems
from .models import WidgetDesignPage, WidgetDesignSetting
from .services import WidgetDataLoaderServices, \
    WidgetDesignPageServices, WidgetDesignServices, \
    WidgetItemServices
from .utils import get_default_language, get_elasticsearch_result_by_date, \
    get_system_language, get_widget_type_list

blueprint = Blueprint(
    'weko_gridlayout',
    __name__,
    template_folder='templates',
    static_folder='static',
)

blueprint_rss = Blueprint(
    'weko_gridlayout_rss',
    __name__,
    url_prefix='/rss',
    template_folder='templates',
    static_folder='static',
)

blueprint_api = Blueprint(
    'weko_gridlayout',
    __name__,
    url_prefix='/admin',
    template_folder='templates',
    static_folder='static',
)

blueprint_pages = Blueprint(
    'weko_gridlayout_pages',
    # 'weko_gridlayout',
    __name__,
    template_folder='templates',
    static_folder='static',
    url_prefix='/',
)


@blueprint_pages.before_app_first_request
def preload_pages():
    """Register all widget pages before the first application request."""
    try:
        _add_url_rule([page.url for page in WidgetDesignPage.get_all()])
    except Exception:
        current_app.logger.warn('Pages were not loaded.')
        raise


@blueprint.route("/")
@login_required
def index():
    """Render a basic view."""
    return render_template(
        "weko_gridlayout/index.html",
        module_name=_('weko-gridlayout'))


@blueprint_api.route('/load_repository', methods=['GET'])
@login_required
def load_repository():
    """Get Repository list, to display on the combobox on UI.

    :return: Example
        {
           'repositories': [
            {
                'id': 'repository id',
                'title': 'repository title'
            }
           ],
            'error': ''
        }
    """
    result = WidgetDesignServices.get_repository_list()
    return jsonify(result)


@blueprint_api.route(
    '/load_widget_design_setting/<string:repository_id>', methods=['GET'])
@blueprint_api.route('/load_widget_design_setting/<string:repository_id>/'
                     '<string:current_language>', methods=['GET'])
def load_widget_design_setting(repository_id: str, current_language='',
                               page_id=''):
    """Load  Widget design setting from DB by repository id.

    :param repository_id: Identifier of the repository.
    :param current_language: The language default
    :return:
    """
    return jsonify(WidgetDesignServices.get_widget_design_setting(
        repository_id, current_language or get_default_language()))


@blueprint_api.route(
    '/load_widget_design_page_setting/<string:page_id>', methods=['GET'])
@blueprint_api.route('/load_widget_design_page_setting/<string:page_id>/'
                     '<string:current_language>',
                     methods=['GET'])  # TODO: Temporary, must eventually make widgetdeisngPage have its own class
def load_widget_design_page_setting(page_id: str, current_language=''):
    """Load  Widget design page setting from DB by page id.

    :param page_id: Identifier of the page.
    :param current_language: The language default
    :return:
    """
    return jsonify(WidgetDesignPageServices.get_widget_design_setting(
        page_id, current_language or get_default_language()))


@blueprint_api.route('/load_widget_list_design_setting/<string:repository_id>',
                     methods=['GET'])
@login_required
def load_widget_list_design_setting(repository_id):
    """Get Widget list, to display on the Widget List panel on UI.

    :return: Example
            "widget-list": [
                {
                    "widgetId": "widget id",
                    "widgetLabel": "Widget label"
                }
            ],
            "error": ""
    """
    result = dict()
    lang_default = get_default_language()
    result["widget-list"] = WidgetDesignServices.get_widget_list(
        repository_id, lang_default)
    result["widget-preview"] = WidgetDesignServices.get_widget_preview(
        repository_id, lang_default)
    # result["page-list"] = WidgetDesignPageServices.get_page_list(
    #     repository_id, lang_default)

    result["error"] = result["widget-list"].get("error") or \
        result["widget-preview"].get("error")
        #result["page-list"].get("error")

    return jsonify(result)


@blueprint_api.route('/save_widget_layout_setting', methods=['POST'])
@login_required
def save_widget_layout_setting():  # TODO: Allow this to be used for both or make a different path
    """Save Widget design setting into DB.

    :return:
    """
    result = dict()

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    result = WidgetDesignServices.update_widget_design_setting(data)
    return jsonify(result)


@blueprint_api.route(
    '/load_widget_design_pages/<string:repository_id>', methods=['GET'])
@blueprint_api.route(
    '/load_widget_design_pages/<string:repository_id>/<string:lang>',
    methods=['GET']
)
@login_required
def load_widget_design_pages(repository_id, lang=''):
    """Get widget page list for repository.

    :return: Example
            "page-list": [
                {
                    "id": "id",
                    "title": "Page title",
                }
            ],
            "error": ""
    """
    result = dict()

    lang_default = get_default_language()
    lang_default = lang_default.get('lang_code') if lang_default else None

    result["page-list"] = WidgetDesignPageServices.get_page_list(
        repository_id, lang or lang_default)
    result["error"] = result["page-list"].get("error")

    return jsonify(result)


@blueprint_api.route('/load_widget_design_page/<string:page_id>',
                     methods=['GET'])
@login_required
def load_widget_design_page(page_id):
    """Get widget page list for repository.

    :return: Example
            "data": {}
            "error": ""
    """
    return jsonify(WidgetDesignPageServices.get_page(page_id))


@blueprint_api.route('/save_widget_design_page', methods=['POST'])
@login_required
def save_widget_design_page():
    """Save Widget design page into DB.

    :return: result JSON
    """
    result = dict()

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    result = WidgetDesignPageServices.add_or_update_page(data)
    return jsonify(result)


@blueprint_api.route('/delete_widget_design_page', methods=['POST'])
@login_required
def delete_widget_design_page():
    """Delete Widget design page into DB.

    :return: result JSON
    """
    result = dict()

    if request.headers['Content-Type'] != 'application/json':
        result['error'] = _('Header Error')
        return jsonify(result)

    data = request.get_json()
    result = WidgetDesignPageServices.delete_page(data.get('page_id'))
    return jsonify(result)


@blueprint_api.route('/load_widget_type', methods=['GET'])
@login_required
def load_widget_type():
    """Get Widget Type List."""
    results = get_widget_type_list()
    return jsonify(results)


@blueprint_api.route('/save_widget_item', methods=['POST'])
@login_required
def save_widget_item():
    """Save Language List."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg='Header Error')
    data = request.get_json()
    return jsonify(WidgetItemServices.save_command(data))


@blueprint_api.route('/delete_widget_item', methods=['POST'])
@login_required
def delete_widget_item():
    """Delete Language List."""
    if request.headers['Content-Type'] != 'application/json':
        current_app.logger.debug(request.headers['Content-Type'])
        return jsonify(msg='Header Error')
    data = request.get_json()
    return jsonify(WidgetItemServices.delete_by_id(data.get('data_id')))


@blueprint_api.route('/get_account_role', methods=['GET'])
@login_required
def get_account_role():
    """Get Account role.

    :return:
    """
    role = WidgetItems().get_account_role()
    return jsonify(role)


@blueprint_api.route('/get_system_lang', methods=['GET'])
def get_system_lang():
    """Get system language.

    Returns:
        language -- list

    """
    result = get_system_language()
    return jsonify(result)


@blueprint_api.route('/get_new_arrivals/<int:widget_id>', methods=['GET'])
def get_new_arrivals_data(widget_id):
    """Get new arrivals data.

    Returns:
        json -- new arrivals data

    """
    return jsonify(WidgetDataLoaderServices.get_new_arrivals_data(widget_id))


@blueprint_rss.route('/records', methods=['GET'])
def get_rss_data():
    """Get rss data based on term.

    Returns:
        xml -- RSS data

    """
    try:
        data = request.args
        term = int(data.get('term'))
        count = int(data.get('count'))
    except Exception:
        count = -1
        term = -1
    if term < 0 or count < 0:
        return WidgetDataLoaderServices.get_arrivals_rss(None, 0, 0)
    current_date = date.today()
    end_date = current_date.strftime("%Y-%m-%d")
    start_date = (current_date - timedelta(days=term)).strftime("%Y-%m-%d")
    rd = get_elasticsearch_result_by_date(start_date, end_date)
    return WidgetDataLoaderServices.get_arrivals_rss(rd, term, count)


@blueprint_api.route('/get_page_endpoints/<int:widget_id>', methods=['GET'])
@blueprint_api.route('/get_page_endpoints/<int:widget_id>/<string:lang>', methods=['GET'])
def get_widget_page_endpoints(widget_id, lang=''):
    """Get menu pages urls and data."""
    if request.headers['Content-Type'] == 'application/json':
        lang_default = get_default_language()
        lang_default = lang_default.get('lang_code') if lang_default else None
        return \
            jsonify(WidgetDataLoaderServices.get_widget_page_endpoints(
                widget_id, lang or lang_default)
            )
    else:
        return abort(403)


# Based on invenio_pages.views
def view_widget_page():
    """View user-created WidgetDesignPages."""
    community_id, ctx = _get_community_id(request.args)
    try:
        page = WidgetDesignPage.get_by_url(request.path)
        return render_template(
            page.template_name or \
                current_app.config['WEKO_GRIDLAYOUT_DEFAULT_PAGES_TEMPLATE'],
            page=page,
            community_id=community_id,
            **ctx,
        )
    except Exception as e:
        current_app.logger.error(e)
        abort(404)


# Based on invenio_pages.views
def handle_not_found(exception, **extra):
    """Custom blueprint exception handler."""
    assert isinstance(exception, NotFound)  # Only handle 404 errors

    community_id, ctx = _get_community_id(request.args)
    try:  # Check if the page exists
        page = WidgetDesignPage.get_by_url(request.path)
    except NoResultFound:
        page = None

    if page:
        _add_url_rule(page.url)
        return render_template(
            page.template_name or \
                current_app.config['WEKO_GRIDLAYOUT_DEFAULT_PAGES_TEMPLATE'],
            page=page,
            community_id=community_id,
            **ctx,
        )
    elif extra['current_handler']:
        return extra['current_handler'](exception)
    else:
        return exception


# Based on invenio_pages.views
def _add_url_rule(url_or_urls):
    """Register URL rule to application URL map."""
    old = current_app._got_first_request
    # This is bit of cheating to overcome @flask.app.setupmethod decorator.
    current_app._got_first_request = False
    if isinstance(url_or_urls, six.string_types):
        url_or_urls = [url_or_urls]
    map(lambda url: \
        current_app.add_url_rule(url, 'weko_gridlayout.view_widget_page',
        view_widget_page), url_or_urls)
    current_app._got_first_request = old


def _get_community_id(getargs):
    """Get the community data for specific args."""
    ctx = {'community': None}
    community_id = ""
    if 'community' in getargs:  # TODO: Put into a function and use it EVERYWHERE
        from weko_workflow.api import GetCommunity
        comm = GetCommunity.get_community_by_id(request.args.get('community'))
        ctx = {'community': comm}
        community_id = comm.id
    return community_id, ctx
