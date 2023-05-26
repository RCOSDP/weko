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

"""Blueprint for schema rest."""
import re
from flask import Blueprint, current_app, jsonify, make_response, request
from flask_login import current_user
from werkzeug.http import generate_etag
from werkzeug.exceptions import Forbidden, NotFound
from elasticsearch.exceptions import ElasticsearchException
from invenio_pidstore.errors import PIDInvalidAction, PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_pidstore.resolver import Resolver
from invenio_records_rest.links import default_links_factory
from invenio_records_rest.utils import obj_or_import_string
from invenio_records_rest.views import pass_record
from invenio_records_rest.views import \
    create_error_handlers as records_rest_error_handlers
from invenio_records_files.utils import record_file_factory
from invenio_rest import ContentNegotiatedMethodView
from invenio_db import db
from invenio_rest.views import create_api_errorhandler
from invenio_stats.views import QueryRecordViewCount, QueryFileStatsCount
from weko_deposit.api import WekoRecord
from weko_records.serializers import citeproc_v1
from weko_items_ui.config import WEKO_ITEMS_UI_MS_MIME_TYPE, WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT
from sqlalchemy.exc import SQLAlchemyError

from .views import escape_str
from .permissions import page_permission_factory, file_permission_factory
from .errors import VersionNotFoundRESTError, InternalServerError \
  ,RecordsNotFoundRESTError ,PermissionError ,DateFormatRESTError, FilesNotFoundRESTError, ModeNotFoundRESTError
from .utils import check_etag, check_pretty


def create_error_handlers(blueprint):
    """Create error handlers on blueprint."""
    blueprint.errorhandler(PIDInvalidAction)(create_api_errorhandler(
        status=403, message='Invalid action'
    ))
    records_rest_error_handlers(blueprint)


def create_blueprint(endpoints):
    """Create Weko-Records-UI-Cites-REST blueprint.

    See: :data:`invenio_deposit.config.DEPOSIT_REST_ENDPOINTS`.

    :param endpoints: List of endpoints configuration.
    :returns: The configured blueprint.
    """
    blueprint = Blueprint(
        'weko_records_ui_cites_rest',
        __name__,
        url_prefix='',
    )
    
    @blueprint.teardown_request
    def dbsession_clean(exception):
        current_app.logger.debug("weko_records_ui dbsession_clean: {}".format(exception))
        if exception is None:
            try:
                db.session.commit()
            except:
                db.session.rollback()
        db.session.remove()

    create_error_handlers(blueprint)

    for endpoint, options in (endpoints or {}).items():

        if 'record_serializers' in options:
            serializers = options.get('record_serializers')
            serializers = {mime: obj_or_import_string(func)
                           for mime, func in serializers.items()}
        else:
            serializers = {}

        record_class = obj_or_import_string(options['record_class'])

        ctx = dict(
            read_permission_factory=obj_or_import_string(
                options.get('read_permission_factory_imp')
            ),
            record_class=record_class,
            links_factory=obj_or_import_string(
                options.get('links_factory_imp'),
                default=default_links_factory
            ),
            # pid_type=options.get('pid_type'),
            # pid_minter=options.get('pid_minter'),
            # pid_fetcher=options.get('pid_fetcher'),
            loaders={
                options.get('default_media_type'): lambda: request.get_json()},
            default_media_type=options.get('default_media_type'),
        )

        cites = WekoRecordsCitesResource.as_view(
            WekoRecordsCitesResource.view_name.format(endpoint),
            serializers=serializers,
            # pid_type=options['pid_type'],
            ctx=ctx,
            default_media_type=options.get('default_media_type'),
        )
        blueprint.add_url_rule(
            options.pop('cites_route'),
            view_func=cites,
            methods=['GET'],
        )
        wrr = WekoRecordsResource.as_view(
            WekoRecordsResource.view_name.format(endpoint),
            serializers=serializers,
            # pid_type=options['pid_type'],
            ctx=ctx,
            default_media_type=options.get('default_media_type'),
            )
        blueprint.add_url_rule(
            options.pop('item_route'),
            view_func=wrr,
            methods=['GET'],
        )
        wrs = WekoRecordsStats.as_view(
            WekoRecordsStats.view_name.format(endpoint),
            serializers=serializers,
            # pid_type=options['pid_type'],
            ctx=ctx,
            default_media_type=options.get('default_media_type'),
            )
        blueprint.add_url_rule(
            options.pop('records_stats_route'),
            view_func=wrs,
            methods=['GET'],
        )
        wfs = WekoFilesStats.as_view(
            WekoFilesStats.view_name.format(endpoint),
            serializers=serializers,
            # pid_type=options['pid_type'],
            ctx=ctx,
            default_media_type=options.get('default_media_type'),
            )
        blueprint.add_url_rule(
            options.pop('files_stats_route'),
            view_func=wfs,
            methods=['GET'],
        )
        wfg = WekoFilesGet.as_view(
            WekoFilesGet.view_name.format(endpoint),
            serializers=serializers,
            # pid_type=options['pid_type'],
            ctx=ctx,
            default_media_type=options.get('default_media_type'),
            )
        blueprint.add_url_rule(
            options.pop('files_get_route'),
            view_func=wfg,
            methods=['GET'],
        )
    return blueprint


class WekoRecordsCitesResource(ContentNegotiatedMethodView):
    """Schema files resource."""

    view_name = '{0}_cites'

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super(WekoRecordsCitesResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)

    # @pass_record
    # @need_record_permission('read_permission_factory')
    def get(self, pid_value, **kwargs):
        """Render citation for record according to style and language."""
        style = request.values.get('style', 1)  # style or 'science'
        locale = request.values.get('locale', 2)
        try:
            pid = PersistentIdentifier.get('depid', pid_value)
            record = WekoRecord.get_record(pid.object_uuid)
            result = citeproc_v1.serialize(pid, record, style=style,
                                           locale=locale)
            result = escape_str(result)
            return make_response(jsonify(result), 200)
        except Exception:
            current_app.logger.exception(
                'Citation formatting for record {0} failed.'.format(
                    str(record.id)))
            return make_response(jsonify("Not found"), 404)


class WekoRecordsResource(ContentNegotiatedMethodView):
    """Schema files resource."""

    view_name = '{0}_get_records'

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super(WekoRecordsResource, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)
            
    # @require_api_auth()
    # @require_oauth_scopes(get_index_scope.id)
    def get(self, **kwargs):
        """Get records json."""
        from .config import WEKO_RECORDS_RESOURCE_API_VERSION
        version = kwargs.get('version')
        get_index = WEKO_RECORDS_RESOURCE_API_VERSION.get(version)
        if get_index:
            return get_index(self,**kwargs)
        else:
            raise VersionNotFoundRESTError()
          
    def get_v1(self, pid_value, **kwargs):
        try:
            # Get Record by pid_value
            pid = PersistentIdentifier.get('depid', pid_value)
            record = WekoRecord.get_record(pid.object_uuid)

            # Check Permission
            page_permission = page_permission_factory(record)
            if not page_permission.can():
                raise PermissionError()

            # Check Etag
            etag = generate_etag(str(record).encode('utf-8'))
            if check_etag(etag):
                return make_response("304 Not Modified",304)
            
            # Check pretty
            check_pretty()
                
            # Response Header Setting
            res = make_response(jsonify(record), 200)
            res.set_etag(etag)
            
            return res

        except PIDDoesNotExistError:
            raise RecordsNotFoundRESTError()

        except SQLAlchemyError:
            raise InternalServerError()
          
        except PermissionError:
            raise PermissionError()
          
        except Exception:
            raise InternalServerError()


class WekoRecordsStats(ContentNegotiatedMethodView):
    """Schema Records resource."""

    view_name = '{0}_get_records_stats'

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super(WekoRecordsStats, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)
            
    # @require_api_auth()
    # @require_oauth_scopes(get_index_scope.id)
    def get(self, **kwargs):
        """Get tree json."""
        from .config import WEKO_RECORDS_STATS_API_VERSION
        version = kwargs.get('version')
        get_index = WEKO_RECORDS_STATS_API_VERSION.get(version)
        if get_index:
            return get_index(self,**kwargs)
        else:
            raise VersionNotFoundRESTError()
          
    def get_v1(self, pid_value, **kwargs):
        try:
            import re
            # Get object_uuid by pid_value
            pid = PersistentIdentifier.get('depid', pid_value)
            record = WekoRecord.get_record(pid.object_uuid)
            
            # Check Permission
            if not page_permission_factory(record).can():
                raise PermissionError()
            
            # Get date param
            date = request.values.get('date', type=str)
            
            # Check date pattern
            if date:
                date = re.fullmatch(r'\d{4}-([1-9]|1[0-2])', date)
                if not date :
                    raise DateFormatRESTError()
                date = date.group()

            # Get target class
            query_record_stats = QueryRecordViewCount()
            result = query_record_stats.get_data(pid.object_uuid, date)
            
            if date:
                result['period'] = date
            else:
                result['period'] = 'total'

            # Check Etag
            etag = generate_etag(str(record).encode('utf-8'))
            if check_etag(etag):
                return make_response("304 Not Modified",304)
            
            # Check pretty
            check_pretty()
            
            # Response Header Setting
            res = make_response(jsonify(result), 200)
            res.set_etag(etag)
            
            return res

        except PIDDoesNotExistError:
            raise RecordsNotFoundRESTError()

        except SQLAlchemyError:
            raise InternalServerError()

        except ElasticsearchException:
            raise InternalServerError()          

        except PermissionError:
            raise PermissionError()
                
        except Exception:
            raise InternalServerError()


class WekoFilesStats(ContentNegotiatedMethodView):
    """Schema files resource."""

    view_name = '{0}_get_files_stats'

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super(WekoFilesStats, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)
            
    # @require_api_auth()
    # @require_oauth_scopes(get_index_scope.id)
    def get(self, **kwargs):
        """Get tree json."""
        from .config import WEKO_FILES_STATS_API_VERSION
        version = kwargs.get('version')
        get_index = WEKO_FILES_STATS_API_VERSION.get(version)
        if get_index:
            return get_index(self,**kwargs)
        else:
            raise VersionNotFoundRESTError()
          
    def get_v1(self, pid_value, file_key, **kwargs):
        try:
            # Get object_uuid by pid_value
            pid = PersistentIdentifier.get('recid', pid_value)
            record = WekoRecord.get_record(pid.object_uuid)
            
            # Check Permission
            if not page_permission_factory(record).can():
                raise PermissionError()
            
            # Check File exist
            current_app.config['WEKO_ITEMS_UI_MS_MIME_TYPE'] = WEKO_ITEMS_UI_MS_MIME_TYPE
            current_app.config['WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT'] = WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT
            fileobj = record_file_factory(
                pid, record, kwargs.get('filename')
            )

            if not fileobj:
                raise FilesNotFoundRESTError()

            # Check file contents permission
            if not file_permission_factory(record, fjson=fileobj).can():
                if not current_user.is_authenticated:
                    print(current_user.is_authenticated)
                raise PermissionError()
            
            # Get date param
            date = request.values.get('date', type=str)
            
            # Check date pattern
            if date:
                date = re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', date)
                print(date)
                if not date :
                    raise DateFormatRESTError()
                date = date.group()
            
            query_record_stats = QueryFileStatsCount()       
            result = query_record_stats.get_data(pid.object_uuid, file_key, date)
            if date:
                result['period'] = date
            else:
                result['period'] = 'total'

            # Check Etag
            etag = generate_etag(str(record).encode('utf-8'))
            if check_etag(etag):
                return make_response("304 Not Modified",304)
            
            # Check pretty
            check_pretty()
            
            # Response Header Setting
            res = make_response(jsonify(result), 200)
            res.set_etag(etag)
            
            return res

        except PIDDoesNotExistError:
            raise RecordsNotFoundRESTError()

        except SQLAlchemyError:
            raise InternalServerError()

        except ElasticsearchException:
            raise InternalServerError()

        except PermissionError:
            raise PermissionError()

        except Exception:
            raise InternalServerError()
          
class WekoFilesGet(ContentNegotiatedMethodView):
    """Schema files resource."""

    view_name = '{0}_get_files'

    def __init__(self, serializers, ctx, *args, **kwargs):
        """Constructor."""
        super(WekoFilesGet, self).__init__(
            serializers,
            *args,
            **kwargs
        )
        for key, value in ctx.items():
            setattr(self, key, value)    
          
    # @require_api_auth()
    # @require_oauth_scopes(get_index_scope.id)
    def get(self, **kwargs):
        """Get tree json."""
        from .config import WEKO_FILES_GET_API_VERSION
        version = kwargs.get('version')
        get_index = WEKO_FILES_GET_API_VERSION.get(version)
        if get_index:
            return get_index(self,**kwargs)
        else:
            raise VersionNotFoundRESTError()
    
    def get_v1(self, pid_value, file_key, **kwargs):
        try:
            from .fd import file_ui
            # Get object_uuid by pid_value
            pid = PersistentIdentifier.get('recid', pid_value)
            record = WekoRecord.get_record(pid.object_uuid)

            # Mode Check
            mode = request.values.get('mode')
            if mode == 'preview':
                is_preview = True
            elif mode == 'download':
                is_preview = False
            else:
                raise ModeNotFoundRESTError()

            # Get File Request
            current_app.config['WEKO_ITEMS_UI_MS_MIME_TYPE'] = WEKO_ITEMS_UI_MS_MIME_TYPE
            current_app.config['WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT'] = WEKO_ITEMS_UI_FILE_SISE_PREVIEW_LIMIT
            kwargs['filename'] = file_key
            
            try:
                dl_response = file_ui(
                    pid,
                    record,
                    _record_file_factory=None,
                    is_preview=is_preview,
                    **kwargs)
            except Forbidden:
                raise PermissionError()
            except NotFound:
                raise FilesNotFoundRESTError()
            
            # Check Etag
            hash_str = str(record) + mode + file_key
            etag = generate_etag(hash_str.encode('utf-8'))
            if check_etag(etag):
                return make_response("304 Not Modified",304)
            
            # Response Header Setting
            dl_response.set_etag(etag)
            
            return dl_response

        except PIDDoesNotExistError:
            raise RecordsNotFoundRESTError()

        except SQLAlchemyError:
            raise InternalServerError()
          
        except ModeNotFoundRESTError:
            raise ModeNotFoundRESTError()

        except PermissionError:
            raise PermissionError()

        except FilesNotFoundRESTError:
            raise FilesNotFoundRESTError()

        except Exception:
            raise InternalServerError()