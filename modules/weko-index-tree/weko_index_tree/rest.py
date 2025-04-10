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

"""Blueprint for Weko index tree rest."""

import inspect
import json
import os
import traceback
from functools import wraps
from datetime import datetime, timezone, timedelta

from flask import Blueprint, abort, current_app, jsonify, make_response, \
    request, Response
from flask_babelex import gettext as _
from flask_babelex import get_locale as get_current_locale
from flask_login import current_user
from werkzeug.http import generate_etag
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_records_rest.utils import obj_or_import_string
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.errors import SameContentException
from invenio_db import db
from sqlalchemy.exc import SQLAlchemyError
from weko_admin.models import AdminLangSettings
from weko_accounts.utils import roles_required
from werkzeug.exceptions import BadRequest
import time

from .api import Indexes
from .errors import IndexAddedRESTError, IndexNotFoundRESTError, \
    IndexUpdatedRESTError, InvalidDataRESTError, VersionNotFoundRESTError, InternalServerError, \
    PermissionError, IndexNotFound404Error
from .models import Index
from .scopes import create_index_scope,read_index_scope,update_index_scope,delete_index_scope
from .utils import check_doi_in_index, check_index_permissions, can_user_access_index,\
    is_index_locked, perform_delete_index, save_index_trees_to_redis, reset_tree
from weko_accounts.utils import limiter
WEKO_ADMIN_PERMISSION_ROLE_SYSTEM = "System Administrator"
WEKO_ADMIN_PERMISSION_ROLE_REPO = "Repository Administrator"
WEKO_ADMIN_PERMISSION_ROLE_COMMUNITY = "Community Administrator"

JST = timezone(timedelta(hours=+9), 'JST')

def need_record_permission(factory_name):
    """Decorator checking that the user has the required permissions on record.

    :param factory_name: name of the factory to retrieve.
    """
    def need_record_permission_builder(f):
        @wraps(f)
        def need_record_permission_decorator(self, *args,
                                             **kwargs):
            permission_factory = (getattr(self, factory_name))

            if permission_factory is not None:
                if not permission_factory.can():
                    index_id = kwargs.get('index_id')
                    if index_id and factory_name == 'read_permission_factory':
                        if not check_index_permissions(index_id=index_id):
                            abort(403)
                    else:
                        if not current_user.is_authenticated:
                            abort(401)
                        abort(403)

            return f(self, *args, **kwargs)
        return need_record_permission_decorator
    return need_record_permission_builder


def create_blueprint(app, endpoints):
    """Create Weko-Index-Tree-REST blueprint.

    See: :data:`weko_index_tree.config.WEKO_INDEX_TREE_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_index_tree_rest',
        __name__,
        url_prefix='',
    )

    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("weko_index_tree dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    for endpoint, options in (endpoints or {}).items():
        if 'record_serializers' in options:
            record_serializers = options.get('record_serializers')
            record_serializers = {mime: obj_or_import_string(func)
                                  for mime, func in record_serializers.items()}
        else:
            record_serializers = {}

        record_class = obj_or_import_string(
            options.get('record_class'), default=Indexes)

        ctx = dict(
            read_permission_factory=obj_or_import_string(
                options.get('read_permission_factory_imp')
            ),
            create_permission_factory=obj_or_import_string(
                options.get('create_permission_factory_imp')
            ),
            update_permission_factory=obj_or_import_string(
                options.get('update_permission_factory_imp')
            ),
            delete_permission_factory=obj_or_import_string(
                options.get('delete_permission_factory_imp')
            ),
            record_class=record_class,
            loaders={
                options.get('default_media_type'): lambda: request.get_json()},
        )

        iar = IndexActionResource.as_view(
            IndexActionResource.view_name.format(endpoint),
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )

        itg = GetIndex.as_view(
            GetIndex.view_name.format(endpoint),
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )

        itp = GetParentIndex.as_view(
            GetParentIndex.view_name.format(endpoint),
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )

        ita = IndexTreeActionResource.as_view(
            IndexTreeActionResource.view_name.format(endpoint),
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )
        
        ima = IndexManagementAPI.as_view(
            f"{IndexManagementAPI.view_name}_{endpoint}",
            ctx=ctx,
            record_serializers=record_serializers,
            default_media_type=options.get('default_media_type'),
        )


        blueprint.add_url_rule(
            options.get('index_route'),
            view_func=iar,
            methods=['GET', 'PUT', 'POST', 'DELETE'],
        )

        blueprint.add_url_rule(
            options.get('get_index_tree'),
            view_func=itg,
            methods=['GET'],
        )
        
        blueprint.add_url_rule(
            options.get('api_get_all_index_jp_en'),
            view_func=ima,
            methods=['GET'],
        )
        
        blueprint.add_url_rule(
            options.get('api_get_index_tree'),
            view_func=ima,
            methods=['GET'],
        )
        
        blueprint.add_url_rule(
            options.get('api_create_index'),
            view_func=ima,
            methods=['POST'],
        )
        
        blueprint.add_url_rule(
            options.get('api_update_index'),
            view_func=ima,
            methods=['PUT'],
        )
        
        blueprint.add_url_rule(
            options.get('api_delete_index'),
            view_func=ima,
            methods=['DELETE'],
        )

        blueprint.add_url_rule(
            options.get('get_index_root_tree'),
            view_func=itg,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('get_parent_index_tree'),
            view_func=itp,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('tree_route'),
            view_func=ita,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('item_tree_route'),
            view_func=ita,
            methods=['GET'],
        )

        blueprint.add_url_rule(
            options.get('index_move_route'),
            view_func=ita,
            methods=['PUT'],
        )
    return blueprint


class IndexActionResource(ContentNegotiatedMethodView):
    """Index create update delete view."""

    view_name = '{0}_index_action'

    def __init__(self, ctx, record_serializers=None,
                 default_media_type=None, **kwargs):
        """Constructor."""
        super(IndexActionResource, self).__init__(
            method_serializers={
                'GET': record_serializers,
                'PUT': record_serializers,
                'POST': record_serializers,
                'DELETE': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
                'PUT': default_media_type,
                'POST': default_media_type,
                'DELETE': record_serializers,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @need_record_permission('read_permission_factory')
    def get(self, index_id):
        """Get a tree index record."""
        try:
            if str(index_id) != '0':
                index = self.record_class.get_index_with_role(index_id)
                have_children = Index.have_children(index_id)
                index['have_children'] = have_children
                if not have_children:
                    index['more_check'] = False
            else:
                index = {}

            can_edit = False
            role_ids = []
            if current_user and current_user.is_authenticated:
                for role in current_user.roles:
                    if role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']:
                        role_ids = []
                        can_edit = True
                        break
                    else:
                        role_ids.append(role.id)
            if not can_edit and role_ids and str(index_id) != '0':
                from invenio_communities.models import Community
                indexes = [i.id for i in Indexes.get_all_parent_indexes(index_id)]
                comm_data = Community.query.filter(
                    Community.root_node_id.in_(indexes),
                    Community.id_role.in_(role_ids)
                ).all()
                if comm_data:
                    can_edit = True
            index["can_edit"] = can_edit

            return make_response(jsonify(index), 200)
        except Exception:
            raise InvalidDataRESTError()

    # @pass_record
    @need_record_permission('create_permission_factory')
    def post(self, index_id, **kwargs):
        """Create a index."""
        data = self.loaders[request.mimetype]()
        if not data:
            raise InvalidDataRESTError()
        errors = []
        msg = ''
        status = 200
        if is_index_locked(index_id):
            errors.append(_('Index Delete is in progress on another device.'))
        else:
            if not self.record_class.create(index_id, data):
                raise IndexAddedRESTError()
            status = 201
            msg = 'Index created successfully.'

            langs = AdminLangSettings.get_registered_language()
            if "ja" in [lang["lang_code"] for lang in langs]:
                tree_ja = self.record_class.get_index_tree(lang="ja")
            tree = self.record_class.get_index_tree(lang="other_lang")

            for lang in langs:
                lang_code = lang["lang_code"]
                if lang_code == "ja":
                    save_index_trees_to_redis(tree_ja, lang=lang_code)
                else:
                    save_index_trees_to_redis(tree, lang=lang_code)

        return make_response(
            jsonify({'status': status, 'message': msg, 'errors': errors}),
            status)

    @need_record_permission('update_permission_factory')
    def put(self, index_id, **kwargs):
        """Update a new index."""
        from weko_search_ui.tasks import is_import_running

        data = self.loaders[request.mimetype]()
        if not data:
            raise InvalidDataRESTError()
        msg = ''
        delete_flag = False
        errors = []
        status = 200
        check = is_import_running()

        if check == "is_import_running":
            errors.append(_('The index cannot be updated becase '
                            'import is in progress.'))
        else:
            public_state = data.get('public_state') and data.get(
                'harvest_public_state')

            if is_index_locked(index_id):
                errors.append(_('Index Delete is in progress on another device.'))
            elif not public_state and check_doi_in_index(index_id):
                if not data.get('public_state'):
                    errors.append(_('The index cannot be kept private because '
                                    'there are links from items that have a DOI.'))
                elif not data.get('harvest_public_state'):
                    errors.append(_('Index harvests cannot be kept private because'
                                    ' there are links from items that have a DOI.'
                                    ))
            else:
                if data.get('thumbnail_delete_flag'):
                    delete_flag = True
                    filename = os.path.join(
                        current_app.instance_path,
                        current_app.config['WEKO_THEME_INSTANCE_DATA_DIR'],
                        'indextree',
                        data.get('image_name').split('/')[-1])
                    if os.path.isfile(filename):
                        os.remove(filename)
                    data['image_name'] = ""

                if data.get('thumbnail_delete_flag') is not None:
                    del data['thumbnail_delete_flag']
                if not self.record_class.update(index_id, **data):
                    raise IndexUpdatedRESTError()
                msg = 'Index updated successfully.'


            #roles = get_account_role()
            #for role in roles:
            langs = AdminLangSettings.get_registered_language()
            if "ja" in [lang["lang_code"] for lang in langs]:
                tree_ja = self.record_class.get_index_tree(lang="ja")
            tree = self.record_class.get_index_tree(lang="other_lang")
            for lang in langs:
                lang_code = lang["lang_code"]
                if lang_code == "ja":
                    save_index_trees_to_redis(tree_ja, lang=lang_code)
                else:
                    save_index_trees_to_redis(tree, lang=lang_code)

        return make_response(jsonify(
            {'status': status, 'message': msg, 'errors': errors,
             'delete_flag': delete_flag}), status)

    @need_record_permission('delete_permission_factory')
    def delete(self, index_id, **kwargs):
        """Delete a index."""
        from weko_search_ui.tasks import is_import_running

        errors = []
        msg = ''
        if not index_id or index_id <= 0:
            raise IndexNotFoundRESTError()

        check = is_import_running()
        if check == "is_import_running":
            errors.append(_('The index cannot be deleted becase '
                            'import is in progress.'))
        else:
            action = request.values.get('action', 'all')
            msg, errors = perform_delete_index(index_id, self.record_class, action)

        langs = AdminLangSettings.get_registered_language()
        if "ja" in [lang["lang_code"] for lang in langs]:
            tree_ja = self.record_class.get_index_tree(lang="ja")
        tree = self.record_class.get_index_tree(lang="other_lang")
        for lang in langs:
            lang_code = lang["lang_code"]
            if lang_code == "ja":
                save_index_trees_to_redis(tree_ja, lang=lang_code)
            else:
                save_index_trees_to_redis(tree, lang=lang_code)

        return make_response(jsonify(
            {'status': 200, 'message': msg, 'errors': errors}), 200)


class IndexTreeActionResource(ContentNegotiatedMethodView):
    """Tree get move action view."""

    view_name = '{0}_tree_action'

    def __init__(self, ctx, record_serializers=None,
                 default_media_type=None, **kwargs):
        """Constructor."""
        super(IndexTreeActionResource, self).__init__(
            method_serializers={
                'GET': record_serializers,
                'PUT': record_serializers,
                'POST': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
                'PUT': default_media_type,
                'POST': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    def get(self, **kwargs):
        """Get tree json."""
        def _check_edit_permission(is_admin, tree, can_edit_indexes):
            if is_admin:
                for i in tree:
                    i['settings']['can_edit'] = True
                    if len(i['children']) > 0:
                        _check_edit_permission(is_admin, i['children'], can_edit_indexes)
            else:
                for i in tree:
                    i['settings']['can_edit'] = False
                    if str(i['id']) in can_edit_indexes:
                        i['settings']['can_edit'] = True
                    elif str(i['id']) not in can_edit_indexes and \
                            'settings' in i and i['settings'].get('checked', False):
                        i['settings']['checked'] = False
                    if len(i['children']) > 0:
                        _check_edit_permission(is_admin, i['children'], can_edit_indexes)

        from invenio_communities.models import Community
        try:
            action = request.values.get('action')
            comm_id = request.values.get('community')

            more_id_list = request.values.get('more_ids')
            more_ids = []
            if more_id_list is not None:
                more_ids = more_id_list.split('/')

            pid = kwargs.get('pid_value')

            if pid:
                if comm_id:
                    comm = Community.get(comm_id)
                    tree = self.record_class.get_contribute_tree(
                        pid, int(comm.root_node_id))
                else:
                    tree = self.record_class.get_contribute_tree(pid)
            elif action and 'browsing' in action and comm_id is None:
                if more_id_list is None:
                    tree = self.record_class.get_browsing_tree()
                    
                else:
                    tree = self.record_class.get_more_browsing_tree(
                        more_ids=more_ids)
            
            elif action and 'browsing' in action and comm_id is not None:
                comm = Community.get(comm_id)

                if comm is not None:
                    if more_id_list is None:
                        tree = self.record_class.get_browsing_tree(
                            int(comm.root_node_id))
                    else:
                        tree = self.record_class.get_more_browsing_tree(
                            pid=int(comm.root_node_id), more_ids=more_ids)
                else:
                    tree = []
            else:
                tree = []
                role_ids = []
                
                if current_user and current_user.is_authenticated:
                    for role in current_user.roles:
                        if role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER']:
                            role_ids = []
                            tree = self.record_class.get_index_tree()
                            break
                        else:
                            role_ids.append(role.id)
                if role_ids:
                    from invenio_communities.models import Community
                    comm_list = Community.query.filter(
                        Community.group_id.in_(role_ids)
                    ).all()
                    check_list = []
                    for comm in comm_list:
                        indexes = [
                            i.id for i in Indexes.get_all_parent_indexes(comm.root_node_id)
                            if i.parent == 0
                        ]
                        for index_id in indexes:
                            if index_id not in check_list:
                                tree += self.record_class.get_index_tree(index_id)
                                check_list.append(index_id)
            
            return make_response(jsonify(tree), 200)
        except Exception as ex:
            current_app.logger.error('IndexTree Action Exception: ', ex)
            raise InvalidDataRESTError()

    @need_record_permission('update_permission_factory')
    def put(self, index_id, **kwargs):
        """Move a index."""
        from weko_search_ui.tasks import is_import_running

        data = self.loaders[request.mimetype]()
        if not data:
            raise InvalidDataRESTError()

        msg = ''
        status = 200
        check = is_import_running()
        if check == "is_import_running":
            status = 202
            msg = _('The index cannot be moved becase '
                    'import is in progress.')
        else:
            # Moving
            moved = self.record_class.move(index_id, **data)
            if not moved or not moved.get('is_ok'):
                status = 202
                msg = moved.get('msg')
            else:
                status = 201
                msg = _('Index moved successfully.')
            langs = AdminLangSettings.get_registered_language()
            if "ja" in [lang["lang_code"] for lang in langs]:
                    tree_ja = self.record_class.get_index_tree(lang="ja")
            tree = self.record_class.get_index_tree(lang="other_lang")
            for lang in langs:
                lang_code = lang["lang_code"]
                if lang_code == "ja":
                        save_index_trees_to_redis(tree_ja, lang=lang_code)
                else:
                    save_index_trees_to_redis(tree, lang=lang_code)
        return make_response(
            jsonify({'status': status, 'message': msg}), status)


class GetIndex(ContentNegotiatedMethodView):
    """Get Index Tree API."""

    view_name = '{0}_get_index_tree'

    def __init__(self, ctx, record_serializers=None, default_media_type=None, **kwargs):
        """Constructor."""
        super(GetIndex, self).__init__(
            method_serializers={
                'GET': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @require_api_auth(allow_anonymous=True)
    @require_oauth_scopes(read_index_scope.id)
    @limiter.limit('')
    def get(self, **kwargs):
        """Get tree json."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):
        try:
            pid = kwargs.get('index_id')

            # Get update time
            if pid and pid != 0:
                index = self.record_class.get_index(pid)
                if not index:
                    raise IndexNotFound404Error()
                updated = index.updated
            else:
                all_indexes = self.record_class.get_all_indexes()
                all_indexes = sorted(all_indexes, key=lambda x: x.updated, reverse=True)
                updated = all_indexes[0].updated if len(all_indexes) > 0 else datetime.now()

            # Check Etag
            hash_str = str(pid) + updated.strftime("%a, %d %b %Y %H:%M:%S GMT")
            etag = generate_etag(hash_str.encode('utf-8'))
            self.check_etag(etag, weak=True)

            # Check Last-Modified
            if not request.if_none_match:
                self.check_if_modified_since(dt=updated)

            # Language setting
            language = request.headers.get('Accept-Language')
            if language == 'ja':
                get_current_locale().language = language

            # Get index tree
            if pid and pid != 0:
                tree = self.record_class.get_index_tree(pid)
                reset_tree(tree=tree)
                if len(tree) == 0:
                    raise PermissionError()
                result_tree = dict(
                    index=tree[0]
                )
            else:
                tree = self.record_class.get_index_tree(pid=0)
                reset_tree(tree=tree)
                result_tree = dict(
                    index=dict(
                        children=tree,
                        cid=0,
                        name='Root-index',
                        id='0',
                        public_state=True,
                        value='Root-index'
                    )
                )

            # Check pretty
            indent = 4 if request.args.get('pretty') == 'true' else None

            # Create Response
            res = Response(
                response=json.dumps(result_tree, indent=indent),
                status=200,
                content_type='application/json')
            res.set_etag(etag)
            res.last_modified = updated
            return res

        except (SameContentException, PermissionError, IndexNotFound404Error) as e:
            raise e

        except SQLAlchemyError:
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()


class GetParentIndex(ContentNegotiatedMethodView):
    """Get Parent Index Tree API."""

    view_name = '{0}_get_parent_index_tree'

    def __init__(self, ctx, record_serializers=None, default_media_type=None, **kwargs):
        """Constructor."""
        super(GetParentIndex, self).__init__(
            method_serializers={
                'GET': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    def getParents(self, pid):
        parents = []
        index = self.record_class.get_index(pid)
        parents.append(index)
        if index.parent and index.parent != 0:
            parents = parents + self.getParents(index.parent)
        return parents

    @require_api_auth(allow_anonymous=True)
    @require_oauth_scopes(read_index_scope.id)
    @limiter.limit('')
    def get(self, **kwargs):
        """Get tree json."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    def get_v1(self, **kwargs):
        try:
            pid = kwargs.get('index_id')

            index = self.record_class.get_index(pid)
            if not index:
                raise IndexNotFound404Error()

            # Get update time
            updated = index.updated

            # Check Etag
            hash_str = str(pid) + updated.strftime("%a, %d %b %Y %H:%M:%S GMT")
            etag = generate_etag(hash_str.encode('utf-8'))
            self.check_etag(etag, weak=True)

            # Check Last-Modified
            if not request.if_none_match:
                self.check_if_modified_since(dt=updated)

            # Language setting
            language = request.headers.get('Accept-Language')
            if language == 'ja':
                get_current_locale().language = language

            # Get index tree
            tree = self.record_class.get_index_tree(pid=0)
            reset_tree(tree=tree)

            # Get parent
            parents = self.getParents(pid)

            # Get index from tree
            parent_nodes = []
            for parent in reversed(parents):
                child = next(iter(filter(lambda child: child['cid'] == parent.id, tree)), None)
                if child is None:
                    raise PermissionError()
                parent_nodes.append(child)
                tree = child.pop('children')

            # Connect parent node
            parent_tree = None
            current_parent = None
            for parent in reversed(parent_nodes):
                if parent_tree is None:
                    parent_tree = parent
                else:
                    current_parent['parent'] = parent
                current_parent = parent
            result_tree = dict(
                index=parent_tree
            )

            # Check pretty
            indent = 4 if request.args.get('pretty') == 'true' else None

            # Setting Response
            res = Response(
                response=json.dumps(result_tree, indent=indent),
                status=200,
                content_type='application/json')
            res.set_etag(etag)
            res.last_modified = updated
            return res

        except (SameContentException, PermissionError, IndexNotFound404Error) as e:
            raise e

        except SQLAlchemyError:
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()


class IndexManagementAPI(ContentNegotiatedMethodView):
    """Get Index Tree API."""

    view_name = '{0}_index_management_api'

    def __init__(self, ctx, record_serializers=None, default_media_type=None, **kwargs):
        """Constructor."""
        super(IndexManagementAPI, self).__init__(
            method_serializers={
                'GET': record_serializers,
            },
            default_method_media_type={
                'GET': default_media_type,
            },
            default_media_type=default_media_type,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    @require_api_auth(allow_anonymous=True)
    @require_oauth_scopes(read_index_scope.id)
    @roles_required([], allow_anonymous=True)
    @limiter.limit('')
    def get(self, **kwargs):
        """Get index tree."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    @require_api_auth(allow_anonymous=False)
    @roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,WEKO_ADMIN_PERMISSION_ROLE_REPO])
    @require_oauth_scopes(create_index_scope.id)
    @limiter.limit('')
    def post(self, **kwargs):
        """Create a new index tree node."""
        version = kwargs.get('version')
        func_name = f'post_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()
        
    @require_api_auth(allow_anonymous=False)
    @roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,WEKO_ADMIN_PERMISSION_ROLE_REPO])
    @require_oauth_scopes(update_index_scope.id)
    @limiter.limit('')
    def put(self, **kwargs):
        """Update an existing index tree node."""
        version = kwargs.get('version')
        func_name = f'put_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()

    @require_api_auth(allow_anonymous=False)
    @roles_required([WEKO_ADMIN_PERMISSION_ROLE_SYSTEM,WEKO_ADMIN_PERMISSION_ROLE_REPO])
    @require_oauth_scopes(delete_index_scope.id)
    @limiter.limit('')
    def delete(self, **kwargs):
        """Delete an existing index tree node."""
        version = kwargs.get('version')
        func_name = f'delete_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
        else:
            raise VersionNotFoundRESTError()


    def get_v1(self, **kwargs):
        """Get index tree."""
        try:
            pid = kwargs.get('index_id')

            # Get update time
            if pid and pid != 0:
                index = self.record_class.get_index(pid)
                if not index:
                    raise IndexNotFound404Error()
                updated = index.updated
            else:
                all_indexes = self.record_class.get_all_indexes()
                current_app.logger.error(all_indexes)
                all_indexes = sorted(all_indexes, key=lambda x: x.updated, reverse=True)
                updated = all_indexes[0].updated if len(all_indexes) > 0 else datetime.now()

            # Check Etag
            hash_str = str(pid) + updated.strftime("%a, %d %b %Y %H:%M:%S GMT")
            etag = generate_etag(hash_str.encode('utf-8'))
            self.check_etag(etag, weak=True)

            # Check Last-Modified
            if not request.if_none_match:
                self.check_if_modified_since(dt=updated)

            # Get index tree
            if pid and pid != 0:
                tree = self.record_class.get_index_tree(pid, lang="ja")
                reset_tree(tree=tree)
                if len(tree) == 0:
                    raise PermissionError()
                result_tree_ja = dict(
                    index=tree[0]
                )
                
                tree = self.record_class.get_index_tree(pid, lang="en")
                reset_tree(tree=tree)
                result_tree_en = dict(
                    index=tree[0]
                )
            else:
                tree = self.record_class.get_index_tree(pid=0, lang="ja")
                current_app.logger.error(tree)
                
                reset_tree(tree=tree)
                current_app.logger.error(tree)
                result_tree_ja = dict(
                    index=dict(
                        children=tree,
                        cid=0,
                        name='Root-index',
                        id='0',
                        public_state=True,
                        value='Root-index'
                    )
                )
                
                tree = self.record_class.get_index_tree(pid=0, lang="en")
                reset_tree(tree=tree)
                result_tree_en = dict(
                    index=dict(
                        children=tree,
                        cid=0,
                        name='Root-index',
                        id='0',
                        public_state=True,
                        value='Root-index'
                    )
                )

            merged_tree = self.merge_index_trees(result_tree_ja, result_tree_en)

            indent = 4 if request.args.get('pretty') == 'true' else None

            res = Response(
                response=json.dumps(merged_tree, indent=indent),
                status=200,
                content_type='application/json'
            )
            res.set_etag(etag)
            res.last_modified = updated
            return res
        
        except (SameContentException, PermissionError, IndexNotFound404Error) as e:
            raise e

        except SQLAlchemyError:
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()

    def merge_index_trees(self, tree_ja, tree_en):
        """Merge Japanese and English index trees."""
        def merge_nodes(node_ja, node_en):
            merged_node = node_ja.copy()
            merged_node.update({
                "index_name": merged_node.get("value", ""),
                "index_name_english": node_en.get("value", ""),
                "index_link_name_english": node_en.get("index_link_name", ""),
                "value_english": node_en.get("value", ""),
            })
            
            # Merge children recursively
            children_ja = {child["cid"]: child for child in node_ja.get("children", [])}
            children_en = {child["cid"]: child for child in node_en.get("children", [])}
            merged_children = []
            for cid in set(children_ja.keys()).union(children_en.keys()):
                merged_children.append(merge_nodes(children_ja.get(cid), children_en.get(cid)))
            merged_node["children"] = merged_children
            
            return merged_node
        
        return {"index": merge_nodes(tree_ja["index"], tree_en["index"])}
    
    def post_v1(self, **kwargs):
        """Create a new index tree node."""
        try:
            try:
                request_data = request.get_json()
                if not isinstance(request_data,dict) :
                    return make_response(jsonify({'status': 400, 'error': 'Bad Request: No data provided'}), 400)
            except:
                return make_response(jsonify({'status': 400, 'error': 'Bad Request: No data provided'}), 400)

            raw_index_data = request_data.get("index",{})
            
            parent_id = int(raw_index_data.get("parent_id", "0"))
            if parent_id != 0:
                index_obj = self.record_class.get_index(parent_id)
                if not index_obj:
                    return make_response(jsonify({'status': 404, 'error': 'Index not found'}), 404)
                else:
                    lst = {column.name: getattr(index_obj, column.name) for column in index_obj.__table__.columns}
                    if not can_user_access_index(lst):
                        return make_response(jsonify({'status': 403, 'error': f'Permission denied: You do not have access to parent index {parent_id}.'}), 403)
           
            index_id = int(time.time() * 1000)

            indexes = {
                "id": index_id,
                "value": raw_index_data.get("index_name", "New Index"),
            }

            create_result = self.record_class.create(
                pid=raw_index_data.get("parent_id", "0"),
                indexes=indexes
            )
            
            if not create_result:
                return make_response(jsonify({'status': 500, 'error': 'Internal Server Error: Failed to create index'}), 500)
            
            index_data = {
                "id": index_id,
                "parent": int(raw_index_data.get("parent_id", "0")),
                "index_name": raw_index_data.get("index_name", "New Index"),
                "index_name_english": raw_index_data.get("index_name_english", "New Index"),
                "index_link_name": raw_index_data.get("index_link_name", ""),
                "index_link_name_english": raw_index_data.get("index_link_name_english", "New Index"),
                "index_link_enabled": raw_index_data.get("index_link_enabled", False),
                "comment": raw_index_data.get("comment", ""),
                "more_check": raw_index_data.get("more_check", False),
                "display_no": raw_index_data.get("display_no", 5),
                "harvest_public_state": raw_index_data.get("harvest_public_state", True),
                "display_format": raw_index_data.get("display_format", "1"),
                "public_state": raw_index_data.get("public_state", False),
                "public_date": raw_index_data.get("public_date", None),
                "rss_status": raw_index_data.get("rss_status", False),
                "browsing_role": raw_index_data.get("browsing_role", "3,4,-98,-99"),
                "contribute_role": raw_index_data.get("contribute_role", ""),
                "browsing_group": raw_index_data.get("browsing_group", "3,4,-98,-99"),
                "contribute_group": raw_index_data.get("contribute_group", ""),
                "online_issn": raw_index_data.get("online_issn", ""),
            }
            
            updated_index = self.record_class.update(index_id, **index_data)

            if not updated_index:
                return make_response(jsonify({'status': 500, 'error': 'Internal Server Error: Failed to update index'}), 500)

            response_data = {
                "index": {
                    "created": datetime.utcnow().isoformat(),
                    "updated": datetime.utcnow().isoformat(),
                    "id": index_id,
                    "parent": updated_index.parent,
                    "position": updated_index.position,
                    "index_name": updated_index.index_name,
                    "index_name_english": updated_index.index_name_english,
                    "index_link_name": updated_index.index_link_name,
                    "index_link_name_english": updated_index.index_link_name_english,
                    "index_link_enabled": updated_index.index_link_enabled,
                    "comment": updated_index.comment,
                    "more_check": updated_index.more_check,
                    "display_no": updated_index.display_no,
                    "harvest_public_state": updated_index.harvest_public_state,
                    "display_format": updated_index.display_format,
                    "public_state": updated_index.public_state,
                    "public_date": updated_index.public_date,
                    "rss_status": updated_index.rss_status,
                    "coverpage_state": updated_index.coverpage_state,
                    "browsing_role": updated_index.browsing_role,
                    "contribute_role": updated_index.contribute_role,
                    "browsing_group": updated_index.browsing_group,
                    "contribute_group": updated_index.contribute_group,
                    "owner_user_id": updated_index.owner_user_id,
                    "online_issn": updated_index.online_issn
                }
            }
            
            return make_response(jsonify(response_data), 200)

        except (SameContentException, PermissionError, IndexNotFound404Error) as e:
            raise e

        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()

    def put_v1(self, index_id, **kwargs):
        """Update an existing index tree node."""
        try:
            index_obj = self.record_class.get_index(index_id)
            if not index_obj:
                return make_response(jsonify({'status': 404, 'error': 'Index not found'}), 404)
            else:
                lst = {column.name: getattr(index_obj, column.name) for column in index_obj.__table__.columns}
                if not can_user_access_index(lst):
                    return make_response(jsonify({'status': 403, 'error': f'Permission denied: You do not have access to index {index_id}.'}), 403)
            
            request_data = request.get_json()
            if not request_data or "index" not in request_data:
                return make_response(jsonify({'status': 400, 'error': 'Bad Request: No data provided'}), 400)

            raw_index_data = request_data["index"]
            if not isinstance(raw_index_data, dict):
                return make_response(jsonify({'status': 400, 'error': 'Bad Request: Invalid format'}), 400)

            index_data = {
                "id": index_id,
                "parent": raw_index_data.get("parent_id", index_obj.parent),
                "index_name": raw_index_data.get("index_name", index_obj.index_name),
                "index_name_english": raw_index_data.get("index_name_english", index_obj.index_name_english),
                "index_link_name": raw_index_data.get("index_link_name", index_obj.index_link_name),
                "index_link_name_english": raw_index_data.get("index_link_name_english", index_obj.index_link_name_english),
                "index_link_enabled": raw_index_data.get("index_link_enabled", index_obj.index_link_enabled),
                "comment": raw_index_data.get("comment", index_obj.comment),
                "more_check": raw_index_data.get("more_check", index_obj.more_check),
                "display_no": raw_index_data.get("display_no", index_obj.display_no),
                "harvest_public_state": raw_index_data.get("harvest_public_state", index_obj.harvest_public_state),
                "display_format": raw_index_data.get("display_format", index_obj.display_format),
                "public_state": raw_index_data.get("public_state", index_obj.public_state),
                "public_date": raw_index_data.get("public_date", index_obj.public_date),
                "rss_status": raw_index_data.get("rss_status", index_obj.rss_status),
                "browsing_role": raw_index_data.get("browsing_role", index_obj.browsing_role),
                "contribute_role": raw_index_data.get("contribute_role", index_obj.contribute_role),
                "browsing_group": raw_index_data.get("browsing_group", index_obj.browsing_group),
                "contribute_group": raw_index_data.get("contribute_group", index_obj.contribute_group),
                "online_issn": raw_index_data.get("online_issn", index_obj.online_issn),
            }

            updated_index = self.record_class.update(index_id, **index_data)

            if not updated_index:
                return make_response(jsonify({'status': 500, 'error': 'Internal Server Error: Failed to update index'}), 500)

            response_data = {
                "index": {
                    "created": updated_index.created.isoformat(),
                    "updated": datetime.utcnow().isoformat(),
                    "id": updated_index.id,
                    "parent": updated_index.parent,
                    "position": updated_index.position,
                    "index_name": updated_index.index_name,
                    "index_name_english": updated_index.index_name_english,
                    "index_link_name": updated_index.index_link_name,
                    "index_link_name_english": updated_index.index_link_name_english,
                    "index_link_enabled": updated_index.index_link_enabled,
                    "comment": updated_index.comment,
                    "more_check": updated_index.more_check,
                    "display_no": updated_index.display_no,
                    "harvest_public_state": updated_index.harvest_public_state,
                    "display_format": updated_index.display_format,
                    "public_state": updated_index.public_state,
                    "public_date": updated_index.public_date,
                    "rss_status": updated_index.rss_status,
                    "coverpage_state": updated_index.coverpage_state,
                    "browsing_role": updated_index.browsing_role,
                    "contribute_role": updated_index.contribute_role,
                    "browsing_group": updated_index.browsing_group,
                    "contribute_group": updated_index.contribute_group,
                    "owner_user_id": updated_index.owner_user_id,
                    "online_issn": updated_index.online_issn
                }
            }
            
            return make_response(jsonify(response_data), 200)

        except (SameContentException, PermissionError, IndexNotFound404Error, BadRequest) as e:
            raise e

        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()

    def delete_v1(self, index_id, **kwargs):
        """Delete an existing index tree node."""
        try:
            index_obj = self.record_class.get_index(index_id)
            if not index_obj:
                return make_response(jsonify({'status': 404, 'error': 'Index not found'}), 404)
            else:
                lst = {column.name: getattr(index_obj, column.name) for column in index_obj.__table__.columns}
                if not can_user_access_index(lst):
                    return make_response(jsonify({'status': 403, 'error': f'Permission denied: You do not have access to index {index_id}.'}), 403)
            
            delete_result = self.record_class.delete(index_id)

            if not delete_result:
                return make_response(jsonify({'status': 500, 'error': 'Internal Server Error: Failed to delete index'}), 500)

            return make_response(jsonify({'status': 200, 'message': 'Index deleted successfully.'}), 200)

        except (SameContentException, PermissionError, IndexNotFound404Error) as e:
            raise e

        except SQLAlchemyError:
            db.session.rollback()
            raise InternalServerError()

        except Exception:
            current_app.logger.error(traceback.print_exc())
            raise InternalServerError()
