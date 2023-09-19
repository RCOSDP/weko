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

import inspect
import json

from flask import Blueprint, current_app, request, Response
from werkzeug.http import generate_etag
from elasticsearch.exceptions import ElasticsearchException
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_pidstore.errors import PIDInvalidAction
from invenio_records_rest.views import create_error_handlers as records_rest_error_handlers
from invenio_rest import ContentNegotiatedMethodView
from invenio_rest.errors import SameContentException
from invenio_db import db
from invenio_rest.views import create_api_errorhandler
from weko_admin.models import RankingSettings
from sqlalchemy.exc import SQLAlchemyError

from .errors import VersionNotFoundRESTError, InternalServerError, \
    PermissionError, NoRankingtypeError, RequestParameterError
from .utils import get_ranking, create_limmiter
from .scopes import ranking_read_scope

limiter = create_limmiter()


def create_error_handlers(blueprint):
    """Create error handlers on blueprint."""
    blueprint.errorhandler(PIDInvalidAction)(create_api_errorhandler(
        status=403, message='Invalid action'
    ))
    records_rest_error_handlers(blueprint)


def create_blueprint(endpoints):
    """Create Weko-Items-UI-REST blueprint.

    See: :data:`weko_items_ui.config.WEKO_ITEMS_UI_REST_ENDPOINTS`.

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
        current_app.logger.debug("weko_items_ui dbsession_clean: {}".format(exception))
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

    @require_api_auth(True)
    @require_oauth_scopes(ranking_read_scope.id)
    @limiter.limit('')
    def get(self, **kwargs):
        """Get ranking json."""
        version = kwargs.get('version')
        func_name = f'get_{version}'
        if func_name in [func[0] for func in inspect.getmembers(self, inspect.ismethod)]:
            return getattr(self, func_name)(**kwargs)
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

            # Get ranking
            ranking = get_ranking(settings)
            result = dict(
                ranking_type=ranking_type,
                ranking=ranking.get(ranking_type, []),
            )

            # Check Etag
            etag = generate_etag(str(result).encode('utf-8'))
            self.check_etag(etag, weak=True)

            # Check pretty
            indent = 4 if request.args.get('pretty') == 'true' else None

            # Create Response
            res = Response(
                response=json.dumps(result, indent=indent),
                status=200,
                content_type='application/json')
            res.set_etag(etag)
            return res

        except (SameContentException, PermissionError, NoRankingtypeError) as e:
            raise e

        except TypeError:
            raise RequestParameterError()

        except ValueError:
            raise RequestParameterError()

        except SQLAlchemyError:
            raise InternalServerError()

        except ElasticsearchException:
            raise InternalServerError()

        except Exception:
            raise InternalServerError()
