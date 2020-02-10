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

"""WEKO3 module docstring."""
import json
from flask import Response, abort, current_app, jsonify, make_response, request
from flask_admin import BaseView, expose
from flask_babelex import gettext as _
from .config import INVENIO_RESYNC_INDEXES_STATUS, INVENIO_RESYNC_INDEXES_MODE,\
    INVENIO_RESYNC_INDEXES_SAVING_FORMAT
from .api import ResyncHandler
from .tasks import run_sync_import
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from .utils import read_capability, sync_baseline, sync_audit,\
    sync_incremental


class AdminResyncClient(BaseView):
    """BaseView for Admin Resource List."""

    @expose('/', methods=['GET'])
    def index(self):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        return self.render(
            current_app.config['INVENIO_RESOURCESYNCCLIENT_ADMIN_TEMPLATE'],
            status=json.dumps(current_app.config.get(
                'INVENIO_RESYNC_INDEXES_STATUS',
                INVENIO_RESYNC_INDEXES_STATUS
            )),
            resync_mode=json.dumps(current_app.config.get(
                'INVENIO_RESYNC_INDEXES_MODE',
                INVENIO_RESYNC_INDEXES_MODE
            )),
            saving_format=json.dumps(current_app.config.get(
                'INVENIO_RESYNC_INDEXES_SAVING_FORMAT',
                INVENIO_RESYNC_INDEXES_SAVING_FORMAT
            )),

        )

    @expose('/get_list', methods=['GET'])
    def get_list(self):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        result = ResyncHandler.get_list_resync()
        result = list(map(lambda item: item.to_dict(), result))
        return jsonify(data=result)

    @expose('/create', methods=['POST'])
    def create_resync(self):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        resync = ResyncHandler(**request.get_json())
        result = resync.create()
        if result.get('success'):
            return jsonify(
                success=result.get('success'),
                data=result.get("data")
            )
        else:
            return jsonify(
                success=result.get('success'),
                errmsg=result.get("errmsg")
            )

    @expose('/update/<resync_id>', methods=['POST'])
    def update_resync(self, resync_id):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        resync = ResyncHandler.get_resync(resync_id)
        if resync:
            result = resync.update(request.get_json())
            if result.get('success'):
                return jsonify(
                    success=result.get('success'),
                    data=result.get("data")
                )
            else:
                return jsonify(
                    success=result.get('success'),
                    errmsg=result.get("errmsg")
                )
        else:
            return jsonify(
                success=False,
                errmsg=["Resync is not exist"]
            )

    @expose('/delete/<resync_id>', methods=['POST'])
    def delete_resync(self, resync_id):
        """Renders an admin resource list view.

        :param
        :return: The rendered template.
        """
        resync = ResyncHandler.get_resync(resync_id)
        if not resync:
            return jsonify(
                success=False,
                errmsg=["Resync is not exist"]
            )
        result = resync.delete()
        if result.get('success'):
            return jsonify(
                success=result.get('success'),
            )
        else:
            return jsonify(
                success=result.get('success'),
                errmsg=result.get("errmsg")
            )

    @expose('/run/<resync_id>', methods=['GET'])
    def run(self, resync_id):
        """Run harvesting."""
        run_sync_import.apply_async(args=(resync_id,
            datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'),
        ))
        return jsonify(
            success=True
        )

    @expose('/get_logs/<resync_id>', methods=['GET'])
    def get_logs(self, resync_id):
        """Run harvesting."""
        resync = ResyncHandler.get_resync(resync_id)
        logs = resync.get_logs()
        if logs:
            return jsonify(
                logs=logs,
                success=True
            )
        else:
            return jsonify(
                success=False
            )

    @expose("/sync/<resync_id>", methods=['GET'])
    def sync(self, resync_id):
        """Sync a resource sync. Save data to local"""
        resync_index = ResyncHandler.get_resync(resync_id)
        if not resync_index:
            raise ValueError('No Resync Index found')
        # Validate base_url
        base_url = resync_index.base_url
        capability = read_capability(base_url)
        mode = resync_index.resync_mode
        save_dir = resync_index.resync_save_dir
        map = [base_url]
        if save_dir:
            map.append(save_dir)

        parts = urlsplit(map[0])
        uri_host = urlunsplit([parts[0], parts[1], '', '', ''])
        from_date = request.args.get('from_date')
        to_date = request.args.get('to_date')

        # map = [base_url, save_dir]

        try:
            if mode == current_app.config.get(
                'INVENIO_RESYNC_INDEXES_MODE',
                INVENIO_RESYNC_INDEXES_MODE
            ).get('baseline'):
                if not capability or (
                    capability != 'resourcelist' and
                        capability != 'resourcedump'):
                    raise ValueError('Bad URL')
                result = False
                while map[0] != uri_host and not result:
                    result = sync_baseline(map=map,
                                           base_url=base_url,
                                           dryrun=False,
                                           from_date=from_date,
                                           to_date=to_date)
                return make_response('OK', 200)
            elif mode == current_app.config.get(
                'INVENIO_RESYNC_INDEXES_MODE',
                INVENIO_RESYNC_INDEXES_MODE
            ).get('audit'):
                if not capability or (
                        capability != 'resourcelist' and
                        capability != 'changelist'):
                    raise ValueError('Bad URL')
                # do the same logic with Baseline
                # to make sure right url is used
                result = False
                while map[0] != uri_host and not result:
                    result = sync_baseline(map=map, base_url=base_url,
                                           dryrun=True)
                return jsonify(sync_audit(map))
            elif mode == current_app.config.get(
                'INVENIO_RESYNC_INDEXES_MODE',
                INVENIO_RESYNC_INDEXES_MODE
            ).get('Incremental'):
                if not capability or (
                        capability != 'changelist' and
                        capability != 'changedump'):
                    raise (
                        'Bad URL, not a changelist/changedump,'
                        ' cannot sync incremental')
                result = False
                while map[0] != uri_host and not result:
                    result = sync_incremental(map, base_url, from_date, to_date)
                    return jsonify({'result': result})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})


invenio_admin_resync_client = {
    'view_class': AdminResyncClient,
    'kwargs': {
        'category': _('Resource Sync'),
        'name': _('Resync'),
        'endpoint': 'resync'
    }
}


__all__ = (
    'invenio_admin_resync_client',
)
