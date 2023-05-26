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
from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, jsonify, make_response, request
from flask_login import current_user
from werkzeug.http import generate_etag
from werkzeug.exceptions import Forbidden, NotFound
from elasticsearch.exceptions import ElasticsearchException
from invenio_pidstore.errors import PIDInvalidAction, PIDDoesNotExistError
from invenio_records_rest.views import \
    create_error_handlers as records_rest_error_handlers
from invenio_rest import ContentNegotiatedMethodView
from invenio_db import db
from invenio_rest.views import create_api_errorhandler
from weko_admin.models import  RankingSettings
from sqlalchemy.exc import SQLAlchemyError

from invenio_records_rest.links import default_links_factory
from invenio_records_rest.utils import obj_or_import_string

from .utils import get_ranking, check_etag, check_pretty
from .errors import VersionNotFoundRESTError, InternalServerError \
  ,PermissionError , NoRankingtypeError, RequestParameterError



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
        'weko_items_ui_rest',
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
      
        rank = WekoRanking.as_view(
            WekoRanking.view_name.format(endpoint),
            default_media_type=options.get('default_media_type'),
        )
        blueprint.add_url_rule(
            options.get('rank_route'),
            view_func=rank,
            methods=['GET'],
        )
    return blueprint

class WekoRanking(ContentNegotiatedMethodView):
    """Item Ranking API"""

    view_name = '{0}_ranking'

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(WekoRanking, self).__init__(
            *args,
            **kwargs
        )

    # @pass_record
    # @need_record_permission('read_permission_factory')
    def get(self, **kwargs):
        """Get ranking json."""
        from .config import WEKO_RANKING_API_VERSION
        version = kwargs.get('version')
        get_index = WEKO_RANKING_API_VERSION.get(version)
        if get_index:
            return get_index(self,**kwargs)
        else:
            raise VersionNotFoundRESTError()
    
    def get_v1(self, ranking_type, **kwargs):
        try:

            # get ranking settings
            settings = RankingSettings.get()
            
            if not settings:
                upd_data = RankingSettings()
                dafault_data = current_app.config['WEKO_ITEMS_UI_RANKING_DEFAULT_SETTINGS']
                upd_data.is_show = dafault_data['is_show']
                upd_data.new_item_period = dafault_data['new_item_period']
                upd_data.statistical_period = dafault_data['statistical_period']
                upd_data.display_rank = dafault_data['display_rank']
                upd_data.rankings = dafault_data['rankings']
                RankingSettings.update(data=upd_data)
                settings = RankingSettings.get()
                
            # param check
            if ranking_type not in settings.rankings.keys():
                raise NoRankingtypeError()
              
            if not settings.rankings[ranking_type]:
                raise PermissionError()
              
            for k in settings.rankings.keys():
                if k != ranking_type:
                    settings.rankings[k] = False
            # option param setting
            item_period = request.values.get('item_period', type=int)
            if item_period:
                settings.new_item_period = int(item_period)
            
            statistical_period = request.values.get('statistical_period', type=int)
            if statistical_period:
                settings.statistical_period = int(statistical_period)
                
            display_rank = request.values.get('display_rank')
            if display_rank:
                settings.display_rank = int(display_rank)
            result = get_ranking(settings)
            
            # Check Etag
            etag = generate_etag(str(result).encode('utf-8'))
            if check_etag(etag):
                return make_response("304 Not Modified",304)
            
            # Check pretty
            check_pretty()
            # Response Header Setting
            res = make_response(jsonify(result), 200)
            res.set_etag(etag)
            
            return res
        
        except NoRankingtypeError:
            raise NoRankingtypeError()

        except TypeError:
            raise RequestParameterError()
          
        except ValueError:
            raise RequestParameterError() 
        
        except SQLAlchemyError:
            raise InternalServerError()
          
        except ElasticsearchException:
            raise InternalServerError()

        except PermissionError:
            raise PermissionError()

        except Exception:
            raise InternalServerError()

WEKO_RANKING_API_VERSION = {
    "v1.0":WekoRanking.get_v1
}
"""API version."""