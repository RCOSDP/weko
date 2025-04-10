# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""InvenioStats views."""
import traceback
import uuid

import calendar
from datetime import datetime, timedelta
from functools import wraps

from elasticsearch.exceptions import NotFoundError
from flask import Blueprint, abort, current_app, jsonify, request
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.models import PersistentIdentifier
from invenio_rest.views import ContentNegotiatedMethodView
from invenio_db import db

from . import config
from .errors import InvalidRequestInputError, UnknownQueryError
from .proxies import current_stats
from .utils import QueryCommonReportsHelper, QueryFileReportsHelper, \
    QueryItemRegReportHelper, QueryRecordViewPerIndexReportHelper, \
    QueryRecordViewReportHelper, QuerySearchReportHelper, current_user

blueprint = Blueprint(
    'invenio_stats',
    __name__,
    url_prefix='/stats',
)


def stats_api_access_required(f):
    """Decorator for checking access to invenio-stats api."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        p = current_stats.permission_factory()
        if p is not None and not p.can():
            return abort(403)
        return f(*args, **kwargs)
    return wrapper


class WekoQuery(ContentNegotiatedMethodView):
    """Docstring for WekoQuery."""

    def __init__(self, **kwargs):
        """Constructor."""
        super(WekoQuery, self).__init__(
            serializers={
                'application/json':
                lambda data, *args, **kwargs: jsonify(data),
            },
            default_method_media_type={
                'GET': 'application/json',
            },
            default_media_type='application/json',
            **kwargs)


class StatsQueryResource(WekoQuery):
    """REST API resource providing access to statistics."""

    view_name = 'stat_query'

    def post(self, **kwargs):
        """Get statistics."""
        data = request.get_json(force=False)
        if data is None:
            data = {}
        result = {}
        for query_name, config in data.items():
            if config is None or not isinstance(config, dict) \
                    or (set(config.keys()) != {'stat', 'params'}
                        and set(config.keys()) != {'stat'}):
                raise InvalidRequestInputError(
                    'Invalid Input. It should be of the form '
                    '{ STATISTIC_NAME: { "stat": STAT_TYPE, '
                    r'"params": STAT_PARAMS \}}'
                )
            stat = config['stat']
            params = config.get('params', {})
            try:
                query_cfg = current_stats.queries[stat]
            except KeyError:
                raise UnknownQueryError(stat)

            permission = current_stats.permission_factory(stat, params)
            if permission is not None and not permission.can():
                message = ('You do not have a permission to query the '
                           'statistic "{}" with those '
                           'parameters'.format(stat))
                if current_user.is_authenticated:
                    abort(403, message)
                abort(401, message)
            try:
                query = query_cfg.query_class(**query_cfg.query_config)
                result[query_name] = query.run(**params)
            except ValueError as e:
                raise InvalidRequestInputError(e.args[0])
            except NotFoundError as e:
                return None
        return self.make_response(result)


class QueryRecordViewCount(WekoQuery):
    """REST API resource providing record view count."""

    view_name = 'get_record_view_count'

    def _get_data(self, record_id, query_date=None, get_period=False):
        """Get data."""

        result = {}
        period = []
        country = {}
        unknown_view = 0

        try:
            if not query_date:
                params = {'record_id': record_id,
                          'interval': 'month'}
            else:
                year = int(query_date[0: 4])
                month = int(query_date[5: 7])
                _, lastday = calendar.monthrange(year, month)
                params = {'record_id': record_id,
                          'interval': 'month',
                          'start_date': query_date + '-01',
                          'end_date': query_date + '-' + str(lastday).zfill(2)
                          + 'T23:59:59'}
            query_period_cfg = current_stats.queries[
                'bucket-record-view-histogram']
            query_period = query_period_cfg.query_class(
                **query_period_cfg.query_config)

            # total
            query_total_cfg = current_stats.queries['bucket-record-view-total']
            query_total = query_total_cfg.query_class(
                **query_total_cfg.query_config)
            res_total = query_total.run(**params)

            result['total'] = res_total['count']
            for d in res_total['buckets']:
                country[d['key']] = d['count']
                unknown_view += d['count']
            result['country'] = country
            # period
            if get_period:
                provide_year = int(getattr(config, 'PROVIDE_PERIOD_YEAR'))
                sYear = datetime.now().year
                sMonth = datetime.now().month
                eYear = sYear - provide_year
                start = datetime(sYear, sMonth, 15)
                end = datetime(eYear, 1, 1)
                while end < start:
                    period.append(start.strftime('%Y-%m'))
                    start -= timedelta(days=16)
                    start = datetime(start.year, start.month, 15)
                result['period'] = period

            unknown_view = result['total'] - unknown_view
            if unknown_view:
                country[str(getattr(config, 'WEKO_STATS_UNKNOWN_LABEL'))] = \
                    unknown_view
                result['country'] = country
        except Exception as e:
            current_app.logger.debug(e)
            result['total'] = 0
            result['country'] = country
            result['period'] = period

        return result

    def get_data(self, record_id, query_date=None, get_period=False):
        """Public interface of _get_data."""
        result = dict(
            total=0,
            country=dict(),
            period=list()
        )

        recid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            object_uuid=record_id).first()

        if recid:
            versioning = PIDVersioning(child=recid)

            if not versioning.exists:
                return self._get_data(record_id, query_date, get_period)

            _data = list(self._get_data(
                record_id=child.object_uuid,
                query_date=query_date,
                get_period=True) for child in versioning.children.all())

            countries = result['country']
            for _idx in _data:
                for key, value in _idx['country'].items():
                    countries[key] = countries.get(key, 0) + value
                result['total'] = result['total'] + _idx['total']
                result['period'] = _idx.get('period', [])

        return result

    def get_data_by_pid_value(self, pid_value, query_date=None, get_period=False):
        """Public interface of _get_data."""
        result = dict(
            total=0,
            country=dict(),
            period=list()
        )

        recid = PersistentIdentifier.query.filter_by(
            pid_type='recid',
            pid_value=pid_value).first()

        if recid:
            versioning = PIDVersioning(child=recid)

            if not versioning.exists:
                return self._get_data(recid.object_uuid, query_date, get_period)

            _data = list(self._get_data(
                record_id=child.object_uuid,
                query_date=query_date,
                get_period=True) for child in versioning.children.all())

            countries = result['country']
            for _idx in _data:
                for key, value in _idx['country'].items():
                    countries[key] = countries.get(key, 0) + value
                result['total'] = result['total'] + _idx['total']
                result['period'] = _idx.get('period', [])

        return result

    def get(self, **kwargs):
        """Get total record view count."""
        record_id = kwargs.get('record_id')
        return self.make_response(self.get_data(record_id, get_period=True))

    def post(self, **kwargs):
        """Get record view count with date."""
        record_id = kwargs.get('record_id')
        d = request.get_json(force=False)
        if d['date'] == 'total':
            date = None
        else:
            date = d['date']
        return self.make_response(self.get_data(record_id, date))


class QueryFileStatsCount(WekoQuery):
    """REST API resource providing file download/preview count."""

    view_name = 'get_file_stats_count'

    def get_data(self, bucket_id, file_key, query_date=None,
                 get_period=False, root_file_id=None):
        """Get data."""
        from invenio_files_rest.models import ObjectVersion
        result = {}
        period = []
        country_list = []
        mapping = {}
        unknown_download = 0
        unknown_preview = 0

        # get root_file_id for general file download/preview event
        if not root_file_id:
            obv = ObjectVersion.get(bucket_id, file_key)
            root_file_id = str(obv.root_file_id) if obv else ''
        # get root_file_id for url file download/preview event
        if not root_file_id and '{URL_SLASH}' in file_key:
            file_key = file_key.replace('{URL_SLASH}', '/')
            file_id_key = '{}_{}'.format(bucket_id, file_key)
            root_file_id = str(uuid.uuid3(uuid.NAMESPACE_URL, file_id_key))

        params = {'bucket_id': bucket_id,
                  'file_key': file_key,
                  'interval': 'month',
                  'root_file_id': root_file_id}

        if query_date:
            year = int(query_date[0: 4])
            month = int(query_date[5: 7])
            _, lastday = calendar.monthrange(year, month)
            params.update({
                'start_date': query_date + '-01',
                'end_date': query_date + '-' + str(lastday).zfill(2)
                + 'T23:59:59'
            })

        try:
            try:
                # file download
                query_download_total_cfg = current_stats.queries[
                    'bucket-file-download-total']
                query_download_total = query_download_total_cfg.query_class(
                    **query_download_total_cfg.query_config)
                res_download_total = query_download_total.run(**params)
            except Exception as e:
                res_download_total = {'value': 0, 'buckets': []}
            try:
                # file preview
                query_preview_total_cfg = current_stats.queries[
                    'bucket-file-preview-total']
                query_preview_total = query_preview_total_cfg.query_class(
                    **query_preview_total_cfg.query_config)
                res_preview_total = query_preview_total.run(**params)
            except Exception as e:
                res_preview_total = {'value': 0, 'buckets': []}
            # total
            result['download_total'] = res_download_total['value']
            result['preview_total'] = res_preview_total['value']
            # country
            for d in res_download_total['buckets']:
                data = {}
                data['country'] = d['key']
                data['download_counts'] = d['value']
                data['preview_counts'] = 0
                unknown_download += d['value']
                country_list.append(data)
                mapping[d['key']] = len(country_list) - 1
            for d in res_preview_total['buckets']:
                if d['key'] in mapping:
                    country_list[mapping[d['key']]
                                 ]['preview_counts'] = d['value']
                else:
                    data = {}
                    data['country'] = d['key']
                    data['download_counts'] = 0
                    data['preview_counts'] = d['value']
                    country_list.append(data)
                unknown_preview += d['value']
            result['country_list'] = country_list
            # period
            if get_period:
                provide_year = int(getattr(config, 'PROVIDE_PERIOD_YEAR'))
                sYear = datetime.now().year
                sMonth = datetime.now().month
                eYear = sYear - provide_year
                start = datetime(sYear, sMonth, 15)
                end = datetime(eYear, 1, 1)
                while end < start:
                    period.append(start.strftime('%Y-%m'))
                    start -= timedelta(days=16)
                    start = datetime(start.year, start.month, 15)
                result['period'] = period

            unknown_download = result['download_total'] - unknown_download
            unknown_preview = result['preview_total'] - unknown_preview
            if unknown_download or unknown_preview:
                data = dict(
                    country=str(getattr(config, 'WEKO_STATS_UNKNOWN_LABEL')),
                    download_counts=unknown_download,
                    preview_counts=unknown_preview
                )
                country_list.append(data)
                result['country_list'] = country_list
        except Exception as e:
            current_app.logger.debug(e)
            result['download_total'] = 0
            result['preview_total'] = 0
            result['country_list'] = country_list
            result['period'] = period

        return result

    def get(self, **kwargs):
        """Get total file download/preview count."""
        bucket_id = kwargs.get('bucket_id')
        file_key = kwargs.get('file_key')
        return self.make_response(
            self.get_data(
                bucket_id,
                file_key,
                get_period=True))

    def post(self, **kwargs):
        """Get file download/preview count with date."""
        bucket_id = kwargs.get('bucket_id')
        file_key = kwargs.get('file_key')
        d = request.get_json(force=False)
        if d['date'] == 'total':
            date = None
        else:
            date = d['date']
        return self.make_response(self.get_data(bucket_id, file_key, date))


class QueryItemRegReport(WekoQuery):
    """REST API resource providing item registration report."""

    view_name = 'get_item_registration_report'

    @stats_api_access_required
    def get(self, **kwargs):
        """Get item registration report."""
        page_index = 0
        try:
            page_index = int(request.args.get('p', 1)) - 1
        except Exception as e:
            traceback.print_exc()
            current_app.logger.error(e)

        repository_id = request.args.get('repo')
        if repository_id:
            kwargs['repository_id'] = repository_id
        kwargs['page_index'] = page_index
        return self.make_response(QueryItemRegReportHelper.get(**kwargs))


class QueryRecordViewReport(WekoQuery):
    """REST API resource providing record view report."""

    view_name = 'get_record_view_report'

    @stats_api_access_required
    def get(self, **kwargs):
        """Get record view report."""
        repository_id = request.args.get('repository_id')
        if repository_id:
            kwargs['repository_id'] = repository_id
        result = QueryRecordViewReportHelper.get(**kwargs)
        return self.make_response(result)


class QueryRecordViewPerIndexReport(WekoQuery):
    """REST API resource providing record view per index report."""

    view_name = 'get_record_view_per_index_report'

    @stats_api_access_required
    def get(self, **kwargs):
        """Get record view per index report.

        Nested aggregations are currently unsupported so manually aggregating.
        """
        repository_id = request.args.get('repository_id')
        if repository_id:
            kwargs['repository_id'] = repository_id
        result = QueryRecordViewPerIndexReportHelper.get(**kwargs)
        return self.make_response(result)


class QueryFileReports(WekoQuery):
    """REST API resource providing file reports.

    file_download
    file_preview
    file_using_per_user
    """

    view_name = 'get_file_reports'

    @stats_api_access_required
    def get(self, **kwargs):
        """Get file reports."""
        repository_id = request.args.get('repository_id')
        if repository_id:
            kwargs['repository_id'] = repository_id
        result = QueryFileReportsHelper.get(**kwargs)
        return self.make_response(result)


class QueryCommonReports(WekoQuery):
    """REST API resource providing common reports."""

    view_name = 'get_common_report'

    def get(self, **kwargs):
        """Get file reports."""
        repository_id = request.args.get('repository_id')
        if repository_id:
            kwargs['repository_id'] = repository_id
        result = QueryCommonReportsHelper.get(**kwargs)
        return self.make_response(result)


class QueryCeleryTaskReport(WekoQuery):
    """REST API resource providing celery task report."""

    view_name = 'get_celery_task_report'

    def parse_bucket_response(self, raw_res, pretty_result):
        """Parsing bucket response."""
        if 'buckets' in raw_res:
            field_name = raw_res['field']
            value = raw_res['buckets'][0]['key']
            pretty_result[field_name] = value
            return self.parse_bucket_response(
                raw_res['buckets'][0], pretty_result)
        else:
            return pretty_result

    @stats_api_access_required
    def get(self, **kwargs):
        """Get celery task report."""
        result = {}
        list = []
        task_name = kwargs.get('task_name')
        try:
            params = {'task_name': task_name, 'is_restricted': False}

            # Get exec logs in certain time frame
            query_cfg = current_stats.queries['get-celery-task-report']
            query = query_cfg.query_class(**query_cfg.query_config)
            result = query.run(**params)

            pretty_result = []
            for report in result['buckets']:
                current_report = {}
                current_report['task_id'] = report['key']
                pretty_report = self.parse_bucket_response(
                    report, current_report)
                pretty_result.append(current_report)

        except Exception as e:
            current_app.logger.debug(e)
            return self.make_response([])

        return self.make_response(pretty_result)


class QuerySearchReport(ContentNegotiatedMethodView):
    """REST API resource providing search report."""

    view_name = 'get_search_report'

    def __init__(self, **kwargs):
        """Constructor."""
        super(QuerySearchReport, self).__init__(
            serializers={
                'application/json':
                lambda data, *args, **kwargs: jsonify(data),
            },
            default_method_media_type={
                'GET': 'application/json',
            },
            default_media_type='application/json',
            **kwargs)

    @stats_api_access_required
    def get(self, **kwargs):
        """Get number of searches per keyword."""
        repository_id = request.args.get('repository_id')
        if repository_id:
            kwargs['repository_id'] = repository_id
        result = QuerySearchReportHelper.get(**kwargs)
        return self.make_response(result)


stats_view = StatsQueryResource.as_view(
    StatsQueryResource.view_name,
)

record_view_count = QueryRecordViewCount.as_view(
    QueryRecordViewCount.view_name,
)

file_stats_count = QueryFileStatsCount.as_view(
    QueryFileStatsCount.view_name,
)

item_reg_report = QueryItemRegReport.as_view(
    QueryItemRegReport.view_name,
)

celery_task_report = QueryCeleryTaskReport.as_view(
    QueryCeleryTaskReport.view_name,
)

search_report = QuerySearchReport.as_view(
    QuerySearchReport.view_name,
)

record_view_report = QueryRecordViewReport.as_view(
    QueryRecordViewReport.view_name,
)

record_view_per_index_report = QueryRecordViewPerIndexReport.as_view(
    QueryRecordViewPerIndexReport.view_name,
)

file_reports = QueryFileReports.as_view(
    QueryFileReports.view_name,
)

common_reports = QueryCommonReports.as_view(
    QueryCommonReports.view_name,
)

blueprint.add_url_rule(
    '',
    view_func=stats_view,
)

blueprint.add_url_rule(
    '/<string:record_id>',
    view_func=record_view_count,
)

blueprint.add_url_rule(
    '/<string:bucket_id>/<string:file_key>',
    view_func=file_stats_count,
)

blueprint.add_url_rule(
    '/report/search_keywords/<int:year>/<int:month>',
    view_func=search_report,
)

blueprint.add_url_rule(
    '/<string:target_report>/<string:start_date>/<string:end_date>/<string'
    ':unit>',
    view_func=item_reg_report,
)

blueprint.add_url_rule(
    '/tasks/<string:task_name>',
    view_func=celery_task_report,
)

blueprint.add_url_rule(
    '/report/record/record_view/<int:year>/<int:month>',
    view_func=record_view_report,
)

blueprint.add_url_rule(
    '/report/record/record_view_per_index/<int:year>/<int:month>',
    view_func=record_view_per_index_report,
)

blueprint.add_url_rule(
    '/report/file/<string:event>/<int:year>/<int:month>',
    view_func=file_reports,
)

blueprint.add_url_rule(
    '/<string:event>/<int:year>/<int:month>',
    view_func=common_reports,
)

@blueprint.teardown_request
def dbsession_clean(exception):
    current_app.logger.debug("invenio_stats dbsession_clean: {}".format(exception))
    if exception is None:
        try:
            db.session.commit()
        except:
            db.session.rollback()
    db.session.remove()
