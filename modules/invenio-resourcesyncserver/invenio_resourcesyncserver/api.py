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

import datetime
import os
import shutil
import sys
import tempfile
import traceback
from datetime import timedelta

from flask import current_app, request, send_file
from invenio_communities.models import Community
from invenio_db import db
from invenio_pidrelations.contrib.versioning import PIDVersioning
from invenio_pidstore.models import PersistentIdentifier
from resync import Resource, ResourceList
from resync.change_dump import ChangeDump
from resync.change_dump_manifest import ChangeDumpManifest
from resync.change_list import ChangeList
from resync.list_base_with_index import ListBaseWithIndex
from resync.resource_dump import ResourceDump
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.w3c_datetime import str_to_datetime
from sqlalchemy.exc import SQLAlchemyError
from weko_deposit.api import ItemTypes, WekoRecord
from weko_index_tree.api import Indexes
from weko_items_ui.utils import _export_item, check_item_type_name, \
    make_stats_file, package_export_file

from .config import INVENIO_CAPABILITY_URL, VALIDATE_MESSAGE, WEKO_ROOT_INDEX
from .models import ChangeListIndexes, ResourceListIndexes
from .query import get_items_by_index_tree

import urllib.parse


class ResourceListHandler(object):
    """Define API for ResourceListIndexes creation and update."""

    def __init__(self, **kwargs):
        """Add extra options."""
        self.id = kwargs.get('id')
        self.status = kwargs.get('status')
        self.repository_id = kwargs.get('repository_id')
        self.resource_dump_manifest = kwargs.get('resource_dump_manifest')
        self.url_path = kwargs.get('url_path')
        self.created = kwargs.get('created')
        self.updated = kwargs.get('updated')
        self.index = kwargs.get('index') or self.get_index()

    def get_index(self):
        """Get Index obj relate to repository_id."""
        if self.repository_id:
            return Indexes.get_index(self.repository_id)
        else:
            return None

    def to_dict(self):
        """Generate Resource Object to Dict."""
        repository_name = self.index.index_name_english if str(
            self.repository_id
        ) != "0"\
            else 'Root Index'

        return dict(**{
            'id': self.id,
            'status': self.status,
            'repository_id': self.repository_id,
            'resource_dump_manifest': self.resource_dump_manifest,
            'url_path': self.url_path,
            'repository_name': repository_name
        })

    @classmethod
    def create(cls, data=None):
        """Create the ResourceListIndexes.

        :param data: the index information.
        :returns: The :class:`ResourceListIndexes`.
        """
        if data is None:
            data = {}
        new_data = dict(**{
            'status': data.get('status', False),
            'repository_id': data.get('repository_id', ''),
            'resource_dump_manifest': data.get('resource_dump_manifest', False),
            'url_path': data.get('url_path', ''),
        })
        if ResourceListHandler.get_resource_by_repository_id(
            new_data.get('repository_id')
        ):
            return {
                'success': False,
                'message': current_app.config.get(
                    'VALIDATE_MESSAGE',
                    VALIDATE_MESSAGE
                )
            }
        try:
            with db.session.begin_nested():
                resource = ResourceListIndexes(**new_data)
                db.session.add(resource)
            db.session.commit()
            return {
                'success': True,
                'data': ResourceListHandler(
                    id=resource.id,
                    status=resource.status,
                    repository_id=resource.repository_id,
                    resource_dump_manifest=resource.resource_dump_manifest,
                    url_path=resource.url_path,
                    created=resource.created,
                    updated=resource.updated
                )
            }
        except SQLAlchemyError as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return {
                'success': False,
                'message': str(ex)
            }

    def update(self, data=None):
        """
        Update the index detail info.

        :param data: new Resource info for update.
        :return: Updated Resource info
        """
        if data is None:
            data = {}
        resource = ResourceListHandler.get_resource_by_repository_id(
            data.get('repository_id')
        )
        if resource and str(resource.id) != str(self.id):
            return {
                'success': False,
                'message': current_app.config.get(
                    'VALIDATE_MESSAGE',
                    VALIDATE_MESSAGE
                )
            }
        try:
            with db.session.begin_nested():
                resource = self.get_resource(self.id, 'modal')
                if not resource:
                    return {
                        'success': False,
                        'message': ''
                    }
                resource.status = data.get('status', self.status)
                resource.repository_id = data.get(
                    'repository_id',
                    self.repository_id
                )
                resource.resource_dump_manifest = data.get(
                    'resource_dump_manifest',
                    self.resource_dump_manifest)
                resource.url_path = data.get('url_path', self.url_path)
                db.session.merge(resource)
            db.session.commit()
            return {
                'success': True,
                'data': ResourceListHandler(
                    id=resource.id,
                    status=resource.status,
                    repository_id=resource.repository_id,
                    resource_dump_manifest=resource.resource_dump_manifest,
                    url_path=resource.url_path,
                    created=resource.created,
                    updated=resource.updated
                )
            }
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return {
                'success': False,
                'message': str(ex)
            }

    def delete(self):
        """
        Update the index detail info.

        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                resource = self.get_resource(self.id, 'modal')
                if not resource:
                    return
                db.session.delete(resource)
            db.session.commit()
            return True
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return False

    @classmethod
    def get_resource(cls, resource_id, type_result='obj'):
        """
        Update the index detail info.

        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                resource = db.session.query(ResourceListIndexes).filter(
                    ResourceListIndexes.id == resource_id).one_or_none()
                if type_result == 'obj':
                    return ResourceListHandler(
                        id=resource.id,
                        status=resource.status,
                        repository_id=resource.repository_id,
                        resource_dump_manifest=resource.resource_dump_manifest,
                        url_path=resource.url_path,
                        created=resource.created,
                        updated=resource.updated
                    )
                else:
                    return resource
        except Exception as ex:
            current_app.logger.debug(ex)
            return

    @classmethod
    def get_list_resource(cls, type_result='obj', user=None):
        """
        Update the index detail info.

        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                if not user:
                    list_result = db.session.query(ResourceListIndexes).all()
                else:
                    is_super = any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in user.roles)
                    if is_super:
                        list_result = db.session.query(ResourceListIndexes).all()
                    else:
                        index_list = []
                        repositories = Community.get_repositories_by_user(user)
                        for repository in repositories:
                            index = Indexes.get_child_list_recursive(repository.root_node_id)
                            index_list.extend(index)
                        list_result = db.session.query(ResourceListIndexes).filter(
                            ResourceListIndexes.repository_id.in_(index_list)).all()

                if type_result == 'obj':
                    new_list = []
                    for resource in list_result:
                        resource_dump_manifest = resource.resource_dump_manifest
                        parsed_url = urllib.parse.urlparse(resource.url_path)
                        replaced_url = parsed_url._replace(netloc=request.host)
                        new_res = ResourceListHandler(
                            id=resource.id,
                            status=resource.status,
                            repository_id=resource.repository_id,
                            resource_dump_manifest=resource_dump_manifest,
                            #url_path=resource.url_path,
                            url_path=replaced_url.geturl(),
                            created=resource.created,
                            updated=resource.updated
                        )
                        new_list.append(new_res)
                    return new_list
                else:
                    return list_result
        except Exception as ex:
            current_app.logger.debug(ex)
            return []

    @classmethod
    def get_resource_by_repository_id(cls, repository_id, type_result='obj'):
        """
        Update the index detail info.

        :param repository_id: Identifier of the Resource.
        :param type_result: one of two type 'obj' or 'modal'.
        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                resource = db.session.query(ResourceListIndexes).filter_by(
                    repository_id=repository_id).one_or_none()
                if resource:
                    if type_result == 'obj':
                        resource_dump_manifest = resource.resource_dump_manifest
                        return ResourceListHandler(
                            id=resource.id,
                            status=resource.status,
                            repository_id=resource.repository_id,
                            resource_dump_manifest=resource_dump_manifest,
                            url_path=resource.url_path,
                            created=resource.created,
                            updated=resource.updated
                        )
                    else:
                        return resource
                return None
        except Exception as ex:
            current_app.logger.debug(ex)
            return None

    def _validation(self, record_id=None):
        """
        Update the index detail info.

        :param record_id: Identifier of record.
        :return: Updated Resource info
        """
        from .utils import get_real_path
        if self.status:
            if self.repository_id == current_app.config.get(
                "WEKO_ROOT_INDEX",
                WEKO_ROOT_INDEX
            ):
                return True
            if self.index.public_state:
                if record_id:
                    record = WekoRecord.get_record_by_pid(record_id)
                    if record and record.get("path"):
                        list_path = get_real_path(record.get("path"))
                        if str(self.repository_id) in list_path:
                            return True
                else:
                    return True
        return False

    def get_resource_list_xml(self, from_date=None, to_date=None):
        """
        Get content of resource list.

        :return: (xml) resource list content
        """
        if not self._validation():
            return None
        r = get_items_by_index_tree(self.repository_id)

        rl = ResourceList()
        rl.up = INVENIO_CAPABILITY_URL.format(request.url_root)

        for item in r:
            if item:
                resource_date = str_to_datetime(item.get('_source').get(
                    '_updated'))
                if from_date and str_to_datetime(from_date) > resource_date:
                    continue
                if to_date and str_to_datetime(to_date) < resource_date:
                    continue
                id_item = item.get('_source').get('control_number')
                #url = '{}records/{}'.format(request.url_root, str(id_item))
                url = '{}resync/{}/records/{}'.format(
                    request.url_root,
                    str(self.repository_id),
                    str(id_item)
                )

                rl.add(Resource(url, lastmod=item.get('_source').get(
                    '_updated')))
        return rl.as_xml()

    def get_resource_dump_xml(self, from_date=None, to_date=None):
        """
        Get content of resource dump.

        :return: (xml) resource dump content
        """
        if not self._validation():
            return None

        from .utils import parse_date
        if from_date:
            from_date = parse_date(from_date)
        if to_date:
            to_date = parse_date(to_date)

        r = get_items_by_index_tree(self.repository_id)
        rd = ResourceDump()
        rd.up = INVENIO_CAPABILITY_URL.format(request.url_root)
        for item in r:
            if item:
                resource_date = parse_date(item.get('_source').get(
                    '_updated'))
                if from_date and from_date > resource_date:
                    continue
                if to_date and to_date < resource_date:
                    continue
                id_item = item.get('_source').get('control_number')
                url = '{}resync/{}/{}/file_content.zip'.format(
                    request.url_root,
                    self.repository_id,
                    str(id_item))
                rs = Resource(
                    url,
                    lastmod=item.get('_source').get('_updated'),
                    ln=[]
                )
                if self.resource_dump_manifest:
                    href = '{}resync/{}/{}/resourcedump_manifest.xml'.format(
                        request.url_root,
                        self.repository_id,
                        str(id_item)
                    )
                    rs.ln.append({
                        'rel': 'contents',
                        'href': href,
                        'type': 'application/xml'})
                rd.add(rs)
        return rd.as_xml()

    @classmethod
    def get_capability_content(cls):
        """
        Get capability_list.

        :return: (Resource Obj) list resource dump and resource list
        """
        list_resource = cls.get_list_resource()
        caplist = []
        for resource in list_resource:
            if resource._validation():
                caplist.append(Resource(
                    '{}/resourcelist.xml'.format(resource.url_path),
                    capability='resourcelist'))
                caplist.append(Resource(
                    '{}/resourcedump.xml'.format(resource.url_path),
                    capability='resourcedump'))
                #caplist.append(Resource(
                #    '{}/resourcelist.xml'.format(resource.url_path),
                #    capability='resourcelist'))
                #caplist.append(Resource(
                #    '{}/resourcedump.xml'.format(resource.url_path),
                #    capability='resourcedump'))
        return caplist

    def get_resource_dump_manifest(self, record_id):
        """
        Get resource dump manifest.

        :param record_id: Identifier of record.
        :return: (xml) content of resourcedumpmanifest
        """
        _validation = self._validation(record_id)
        if self.resource_dump_manifest and _validation:
            rdm = ResourceDumpManifest()
            rdm.up = '{}resync/{}/resourcedump.xml'.format(
                request.url_root,
                self.repository_id
            )
            record = WekoRecord.get_record_by_pid(record_id)
            if record:
                for file in record.files:
                    current_app.logger.debug(file.info())
                    file_info = file.info()
                    path = 'recid_{}/{}'.format(
                        record.get('recid'),
                        file_info.get('key'))
                    lastmod = str(datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc
                    ).isoformat())
                    rdm.add(Resource(
                        '{}record/{}/files/{}'.format(
                            request.url_root,
                            record.get('recid'),
                            file_info.get('key')),
                        lastmod=lastmod,
                        sha256=file_info.get('checksum').split(':')[1],
                        length=str(file_info.get('size')),
                        path=path
                    ))
            return rdm.as_xml()
        return None

    def get_record_content_file(self, record_id):
        """
        Get content record.

        :param record_id: Identifier of record
        :return: Zip file
        """
        include_contents = True
        result = {'items': []}
        temp_path = tempfile.TemporaryDirectory(
            prefix=current_app.config['INVENIO_RESOURCESYNCSERVER_TMP_PREFIX'])
        item_types_data = {}
        if not self._validation(record_id):
            return None
        # Set export folder
        export_path = temp_path.name + '/' + datetime.datetime.utcnow() \
            .strftime(
            "%Y%m%d%H%M%S")
        try:
            # Double check for limits
            record_path = export_path + '/recid_' + str(record_id)
            os.makedirs(record_path, exist_ok=True)
            exported_item, list_item_role = _export_item(
                record_id,
                None,
                include_contents,
                record_path,
            )

            result['items'].append(exported_item)

            item_type_id = exported_item.get('item_type_id')
            item_type = ItemTypes.get_by_id(item_type_id)
            if not item_types_data.get(item_type_id):
                item_type_name = check_item_type_name(
                    item_type.item_type_name.name)
                item_types_data[item_type_id] = {
                    'item_type_id': item_type_id,
                    'name': '{}({})'.format(
                        item_type_name,
                        item_type_id),
                    'root_url': request.url_root,
                    'jsonschema': 'items/jsonschema/' + item_type_id,
                    'keys': [],
                    'labels': [],
                    'recids': [],
                    'data': {},
                }
            item_types_data[item_type_id]['recids'].append(record_id)

            # Create export info file
            for item_type_id in item_types_data:
                headers, records = make_stats_file(
                    item_type_id,
                    item_types_data[item_type_id]['recids'],
                    list_item_role)
                keys, labels, is_systems, options = headers
                item_types_data[item_type_id]['recids'].sort()
                item_types_data[item_type_id]['keys'] = keys
                item_types_data[item_type_id]['labels'] = labels
                item_types_data[item_type_id]['is_systems'] = is_systems
                item_types_data[item_type_id]['options'] = options
                item_types_data[item_type_id]['data'] = records
                item_type_data = item_types_data[item_type_id]

                with open('{}/{}.{}'.format(export_path,
                                            item_type_data.get('name'),
                                            current_app.config.get(
                                                'WEKO_ADMIN_OUTPUT_FORMAT', 'tsv')
                                                .lower()),
                          'w') as file:
                    output_file = package_export_file(item_type_data)
                    file.write(output_file.getvalue())

            if self.resource_dump_manifest:
                with open('{}/{}.xml'.format(export_path,
                                             'manifest'),
                          'w') as file:
                    xml_output = self.get_resource_dump_manifest(
                        record_id
                    )
                    file.write(xml_output)

            # Create download file
            shutil.make_archive(export_path, 'zip', export_path)
        except Exception:
            current_app.logger.error('-' * 60)
            traceback.print_exc(file=sys.stdout)
            current_app.logger.error('-' * 60)
            return None

        return send_file(export_path + '.zip')


class ChangeListHandler(object):
    """Define API for ResourceListIndexes creation and update."""

    id = None
    status = None
    repository_id = None
    change_dump_manifest = None
    max_changes_size = None
    change_tracking_state = None
    url_path = None
    created = None
    updated = None
    index = None
    publish_date = None
    interval_by_date = None

    def __init__(self, **kwargs):
        """Add extra options."""
        self.id = kwargs.get('id')
        self.status = kwargs.get('status', False)
        self.repository_id = kwargs.get('repository_id')
        self.change_dump_manifest = kwargs.get('change_dump_manifest', False)
        self.max_changes_size = int(kwargs.get('max_changes_size', 10000))
        self.url_path = kwargs.get('url_path')
        self.created = kwargs.get('created')
        self.updated = kwargs.get('updated')
        self.index = kwargs.get('index') or self.get_index()
        self.publish_date = kwargs.get('publish_date')
        self.interval_by_date = kwargs.get('interval_by_date')
        if kwargs.get('change_tracking_state'):
            if isinstance(kwargs.get('change_tracking_state'), str):
                self.change_tracking_state = kwargs.get('change_tracking_state')
            if isinstance(kwargs.get('change_tracking_state'), list):
                self.change_tracking_state = str('&'.join(kwargs.get(
                    'change_tracking_state'
                )))

    def save(self):
        """Create the ChangeListIndexes.

        :returns: The :dict:`ChangeListIndexes`.
        """
        if self.id:
            cl = ChangeListHandler.get_change_list_by_repo_id(
                self.repository_id
            )
            if cl and str(cl.id) != str(self.id):
                return {
                    'success': False,
                    'message': current_app.config.get(
                        'VALIDATE_MESSAGE',
                        VALIDATE_MESSAGE
                    )
                }
            old_obj = self.get_change_list(self.id, 'modal')
            if old_obj:
                try:
                    with db.session.begin_nested():
                        old_obj.status = self.status
                        old_obj.repository_id = self.repository_id or \
                            old_obj.repository_id
                        old_obj.change_dump_manifest = \
                            self.change_dump_manifest
                        old_obj.max_changes_size = self.max_changes_size
                        old_obj.change_tracking_state = \
                            self.change_tracking_state
                        old_obj.interval_by_date = \
                            self.interval_by_date
                        old_obj.url_path = self.url_path
                        old_obj.publish_date = \
                            self.publish_date
                        db.session.merge(old_obj)
                    db.session.commit()
                    return {
                        'success': True,
                        'data': self
                    }
                except Exception as ex:
                    current_app.logger.debug(ex)
                    db.session.rollback()
                    return {
                        'success': False,
                        'data': str(ex)
                    }
            else:
                return None
        else:
            data = dict(**{
                'status': self.status or False,
                'repository_id': self.repository_id,
                'change_dump_manifest': self.change_dump_manifest,
                'max_changes_size': self.max_changes_size,
                'change_tracking_state': self.change_tracking_state,
                'url_path': self.url_path,
                'interval_by_date': self.interval_by_date,
                'publish_date': self.publish_date
            })
            cl = ChangeListHandler.get_change_list_by_repo_id(
                self.repository_id
            )
            if cl:
                return {
                    'success': False,
                    'message': current_app.config.get(
                        'VALIDATE_MESSAGE',
                        VALIDATE_MESSAGE
                    )
                }
            try:
                with db.session.begin_nested():
                    obj = ChangeListIndexes(**data)
                    db.session.add(obj)
                db.session.commit()
                self.id = obj.id
                return {
                    'success': True,
                    'data': self
                }
            except SQLAlchemyError as ex:
                current_app.logger.debug(ex)
                db.session.rollback()
                return {
                    'success': False,
                    'data': str(ex)
                }

    def get_change_list_content_xml(self, from_date,
                                    from_date_args=None, to_date_args=None):
        """
        Get change list xml.

        :return: Updated Change List info
        """
        if not self._validation():
            return None

        from .utils import parse_date
        if from_date_args:
            from_date_args = parse_date(from_date_args)
        if to_date_args:
            to_date_args = parse_date(to_date_args)

        change_list = ChangeList()
        change_list.up = INVENIO_CAPABILITY_URL.format(request.url_root)
        change_list.index = '{}resync/{}/changelist.xml'.format(
            request.url_root,
            self.repository_id,
        )

        record_changes = self._get_record_changes_with_interval(from_date)

        for data in record_changes:
            try:
                if from_date_args and from_date_args > parse_date(
                        data.get("updated")):
                    continue
                if to_date_args and to_date_args < parse_date(
                        data.get("updated")):
                    continue
                pid_object = PersistentIdentifier.get(
                    'recid',
                    data.get('record_id')
                )
                latest_pid = PIDVersioning(child=pid_object).last_child
                is_latest = str(latest_pid.pid_value) == "{}.{}".format(
                    data.get('record_id'),
                    data.get('record_version')
                )
                if not is_latest and data.get(
                    'status'
                ) != 'deleted':
                    loc = '{}resync/{}/records/{}'.format(
                        request.url_root,
                        self.repository_id,
                        '{}.{}'.format(
                            data.get('record_id'),
                            data.get('record_version')
                        )
                    )
                else:
                    loc = '{}resync/{}/records/{}'.format(
                        request.url_root,
                        self.repository_id,
                        data.get('record_id')
                    )
                rc = Resource(
                    loc,
                    lastmod=data.get("updated"),
                    change=data.get('status'),
                    md_at=data.get("updated"),
                )
                change_list.add(rc)
            except Exception:
                current_app.logger.error('-' * 60)
                traceback.print_exc(file=sys.stdout)
                current_app.logger.error('-' * 60)
                continue

        return change_list.as_xml()

    def get_change_list_index(self):
        """
        Get change list by report_id.

        Arguments:
        Returns:
            None.

        """
        if not self._validation():
            return None
        change_list = ListBaseWithIndex(
            capability_name='changelist',
        )
        change_list.up = INVENIO_CAPABILITY_URL.format(request.url_root)
        published_date = self.publish_date or datetime.datetime.utcnow()
        change_date = published_date
        day_now = datetime.datetime.now()

        while change_date < day_now:
            until = change_date + timedelta(days=self.interval_by_date)
            if until > day_now:
                until = day_now
            change = Resource(
                '{}/{}/changelist.xml'.format(
                    self.url_path,
                    change_date.strftime(r"%Y%m%d")
                ),
                capability='changelist',
                md_from=str(change_date.replace(tzinfo=datetime.timezone.utc).
                            isoformat()),
                md_until=str(until.replace(tzinfo=datetime.timezone.utc).
                             isoformat())
            )
            change_list.add(change)
            change_date = until
        return change_list.as_xml()

    def get_change_dump_index(self):
        """
        Delete unregister bucket by pid.

        Arguments:
        Returns:
            None.

        """
        if not self._validation():
            return None
        changedump = ListBaseWithIndex(
            capability_name='changedump',
        )
        changedump.up = INVENIO_CAPABILITY_URL.format(request.url_root)
        published_date = self.publish_date or datetime.datetime.utcnow()
        change_date = published_date
        day_now = datetime.datetime.now()

        while change_date < day_now:
            until = change_date + timedelta(days=self.interval_by_date)
            if until > day_now:
                until = day_now
            change = Resource(
                '{}/{}/changedump.xml'.format(
                    self.url_path,
                    change_date.strftime(r"%Y%m%d")
                ),
                capability='changedump',
                md_from=str(change_date.replace(tzinfo=datetime.timezone.utc).
                            isoformat()),
                md_until=str(until.replace(tzinfo=datetime.timezone.utc).
                             isoformat())
            )
            changedump.add(change)
            change_date = until
        return changedump.as_xml()

    def get_change_dump_xml(self, from_date):
        """
        Get change dump xml.

        :return: Updated Change List info
        """
        if not self._validation():
            return None
        change_dump = ChangeDump()
        change_dump.up = '{}resync/capability.xml'.format(request.url_root)
        change_dump.index = '{}resync/{}/changedump.xml'.format(
            request.url_root,
            self.repository_id
        )

        record_changes = self._get_record_changes_with_interval(from_date)

        for data in record_changes:
            try:
                next_ch = self._next_change(data, record_changes)
                if data.get('status') == 'deleted':
                    continue
                loc = '{}resync/{}/{}/change_dump_content.zip'.format(
                    request.url_root,
                    self.repository_id,
                    '{}.{}'.format(
                        data.get('record_id'),
                        data.get('record_version')
                    )
                )

                rc = Resource(
                    loc,
                    lastmod=data.get("updated"),
                    mime_type='application/zip',
                    md_from=data.get('updated'),
                    md_until=datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc
                    ).isoformat(),
                    ln=[]
                )
                if next_ch and next_ch.get('updated'):
                    rc.md_until = next_ch.get('updated')
                if self.change_dump_manifest:
                    ln = {
                        'rel': 'contents',
                        'href': '{}resync/{}/{}/changedump_manifest.xml'.format(
                            request.url_root,
                            self.repository_id,
                            '{}.{}'.format(
                                data.get('record_id'),
                                data.get('record_version')
                            )
                        ),
                        'type': 'application/xml'
                    }
                    rc.ln.append(ln)
                change_dump.add(rc)
            except Exception:
                current_app.logger.error('-' * 60)
                traceback.print_exc(file=sys.stdout)
                current_app.logger.error('-' * 60)
                continue

        return change_dump.as_xml()

    def _validation(self):
        """Validate."""
        if self.status:
            if self.repository_id:
                if self.index.public_state:
                    return True
            else:
                return True
        return False

    def get_change_dump_manifest_xml(self, record_id):
        """Get change dump manifest xml.

        :param record_id: Identifier of record
        :return xml
        """
        if not self._is_record_in_index(record_id) or not self._validation():
            return None
        cdm = ChangeDumpManifest()
        cdm.up = '{}resync/{}/changedump.xml'.format(
            request.url_root,
            self.repository_id
        )
        if self.change_dump_manifest:
            prev_id, prev_ver_id = record_id.split(".")
            current_record = WekoRecord.get_record_by_pid(record_id)
            from .utils import get_pid
            prev_record_pid = get_pid(
                '{}.{}'.format(prev_id, str(int(prev_ver_id) - 1))
            )
            if prev_record_pid:
                prev_record = WekoRecord.get_record(
                    id_=prev_record_pid.object_uuid
                )
            else:
                prev_record = None
            if current_record:
                list_file = [file for file in current_record.files]
                current_checksum = [
                    file.info().get('checksum') for file in current_record.files
                ]
                prev_checksum = []
                if prev_record:
                    list_file.extend([file for file in prev_record.files])
                    prev_checksum = [
                        file.info().get('checksum') for file in
                        prev_record.files
                    ]
                for file in list_file:
                    file_info = file.info()
                    change = None
                    if file_info.get('checksum') in prev_checksum:
                        if file_info.get('checksum') in current_checksum:
                            change = None
                        if file_info.get('checksum') not in current_checksum:
                            change = 'deleted'
                    else:
                        if file_info.get('checksum') in current_checksum:
                            change = 'created'
                    path = 'recid_{}/{}'.format(
                        current_record.get('recid'),
                        file_info.get('key'))
                    lastmod = str(datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc
                    ).isoformat())
                    if change:
                        re = Resource(
                            '{}record/{}/files/{}'.format(
                                request.url_root,
                                current_record.get('recid'),
                                file_info.get('key')),
                            lastmod=lastmod,
                            sha256=file_info.get('checksum').split(':')[1],
                            length=str(file_info.get('size')),
                            path=path if change != 'delete' else '',
                            change=change
                        )
                        cdm.add(re)
        return cdm.as_xml()

    @classmethod
    def delete(cls, change_list_id):
        """
        Delete the change_list.

        :param change_list_id: identifier of change_list
        :return:
        """
        try:
            with db.session.begin_nested():
                change_list = cls.get_change_list(change_list_id, 'modal')
                if not change_list:
                    return
                db.session.delete(change_list)
            db.session.commit()
            return True
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return False

    def get_index(self):
        """Get Index obj by repository_id."""
        if self.repository_id:
            return Indexes.get_index(self.repository_id)
        else:
            return None

    def to_dict(self):
        """Convert obj to dict."""
        repository_name = self.index.index_name_english if str(
            self.repository_id
        ) != "0" \
            else "Root Index",
        return dict(**{
            'id': self.id,
            'status': self.status,
            'repository_id': self.repository_id,
            'change_dump_manifest': self.change_dump_manifest,
            'max_changes_size': self.max_changes_size,
            'change_tracking_state': self.change_tracking_state,
            'url_path': self.url_path,
            'created': self.created,
            'updated': self.updated,
            'repository_name': repository_name,
            'publish_date': str(self.publish_date),
            'interval_by_date': self.interval_by_date
        })

    @classmethod
    def get_change_list(cls, changelist_id, type_result='obj'):
        """
        Get change list.

        :param changelist_id: Identifier of changelist
        :param type_result: result of function 'obj' or 'modal'
        :return: Updated Change List info
        """
        try:
            with db.session.begin_nested():
                result = db.session.query(ChangeListIndexes).filter(
                    ChangeListIndexes.id == changelist_id
                ).one_or_none()
                if result:
                    if type_result == 'modal':
                        return result
                    return cls.convert_modal_to_obj(result)
                else:
                    return None
        except Exception as ex:
            current_app.logger.debug(ex)
            return None

    @classmethod
    def get_all(cls, user=None):
        """
        Get change list.

        :return: Updated Change List info
        """
        try:
            with db.session.begin_nested():
                if not user:
                    result = db.session.query(ChangeListIndexes).all()
                else:
                    is_super = any(role.name in current_app.config['WEKO_PERMISSION_SUPER_ROLE_USER'] for role in user.roles)
                    if is_super:
                        result = db.session.query(ChangeListIndexes).all()
                    else:
                        index_list = []
                        repositories = Community.get_repositories_by_user(user)
                        for repository in repositories:
                            index = Indexes.get_child_list_recursive(repository.root_node_id)
                            index_list.extend(index)
                        result = db.session.query(ChangeListIndexes).filter(
                            ChangeListIndexes.repository_id.in_(index_list)).all()

                if result:
                    parse_result = [
                        cls.convert_modal_to_obj(r) for r in result
                    ]
                    return parse_result
                else:
                    return []
        except Exception as ex:
            current_app.logger.debug(ex)
            return None

    @classmethod
    def convert_modal_to_obj(cls, model=ChangeListIndexes()):
        """Convert nodal changelistindexes database to obj ChangeListHandler."""
        return ChangeListHandler(
            id=model.id,
            status=model.status,
            repository_id=model.repository_id,
            change_dump_manifest=model.change_dump_manifest,
            max_changes_size=model.max_changes_size,
            change_tracking_state=str(model.change_tracking_state).split("&"),
            url_path=model.url_path,
            created=model.created,
            updated=model.updated,
            publish_date=model.publish_date,
            interval_by_date=model.interval_by_date
        )

    @classmethod
    def get_change_list_by_repo_id(cls, repo_id, type_result='obj'):
        """
        Get change list.

        :param repo_id: Identifier of index
        :param type_result: result of function 'obj' or 'modal'
        :return: Updated Change List info
        """
        try:
            with db.session.begin_nested():
                result = db.session.query(ChangeListIndexes).filter(
                    ChangeListIndexes.repository_id == repo_id
                ).one_or_none()
                if result:
                    if type_result == 'modal':
                        return result
                    return cls.convert_modal_to_obj(result)
                else:
                    return None
        except Exception as ex:
            current_app.logger.debug(ex)
            return None

    def _is_record_in_index(self, record_id):
        """
        Check record has register index.

        :param record_id: Identifier of record
        :return: True if record has register index_id
        """
        from .utils import get_pid, get_real_path
        if self.repository_id == current_app.config.get(
            "WEKO_ROOT_INDEX",
            WEKO_ROOT_INDEX
        ):
            return True
        if self.status:

            record_pid = get_pid(record_id)
            if record_pid:
                record = WekoRecord.get_record(record_pid.object_uuid)
                if record and record.get("path"):
                    list_path = get_real_path(record.get("path"))
                    if str(self.repository_id) in list_path:
                        return True
        return False

    def get_record_content_file(self, record_id):
        """
        Get content record.

        :param record_id: Identifier of record
        :return: Zip file
        """
        include_contents = True
        result = {'items': []}
        temp_path = tempfile.TemporaryDirectory(
            prefix=current_app.config['INVENIO_RESOURCESYNCSERVER_TMP_PREFIX'])
        item_types_data = {}
        if not self._is_record_in_index(record_id):
            return None
        try:
            # Set export folder
            export_path = temp_path.name + '/' + datetime.datetime.utcnow()\
                .strftime(
                "%Y%m%d%H%M%S")
            # Double check for limits
            record_path = export_path + '/recid_' + str(record_id)
            os.makedirs(record_path, exist_ok=True)
            exported_item, list_item_role = _export_item(
                record_id,
                None,
                include_contents,
                record_path,
            )

            result['items'].append(exported_item)

            item_type_id = exported_item.get('item_type_id')
            item_type = ItemTypes.get_by_id(item_type_id)
            if not item_types_data.get(item_type_id):
                item_type_name = check_item_type_name(
                    item_type.item_type_name.name)
                item_types_data[item_type_id] = {
                    'item_type_id': item_type_id,
                    'name': '{}({})'.format(
                        item_type_name,
                        item_type_id),
                    'root_url': request.url_root,
                    'jsonschema': 'items/jsonschema/' + item_type_id,
                    'keys': [],
                    'labels': [],
                    'recids': [],
                    'data': {},
                }
            item_types_data[item_type_id]['recids'].append(record_id)

            # Create export info file
            for item_type_id in item_types_data:
                headers, records = make_stats_file(
                    item_type_id,
                    item_types_data[item_type_id]['recids'],
                    list_item_role)
                keys, labels, is_systems, options = headers
                item_types_data[item_type_id]['recids'].sort()
                item_types_data[item_type_id]['keys'] = keys
                item_types_data[item_type_id]['labels'] = labels
                item_types_data[item_type_id]['is_systems'] = is_systems
                item_types_data[item_type_id]['options'] = options
                item_types_data[item_type_id]['data'] = records
                item_type_data = item_types_data[item_type_id]

                with open('{}/{}.{}'.format(export_path,
                                            item_type_data.get('name'),
                                            current_app.config.get(
                                                'WEKO_ADMIN_OUTPUT_FORMAT', 'tsv')
                                                .lower()),
                          'w') as file:
                    output_file = package_export_file(item_type_data)
                    file.write(output_file.getvalue())

            # Create bag
            if self.change_dump_manifest:
                with open('{}/{}.xml'.format(export_path,
                                             'manifest'),
                          'w') as file:
                    xml_output = self.get_change_dump_manifest_xml(
                        record_id
                    )
                    file.write(xml_output)

            # Create download file
            shutil.make_archive(export_path, 'zip', export_path)
        except Exception:
            current_app.logger.error('-' * 60)
            traceback.print_exc(file=sys.stdout)
            current_app.logger.error('-' * 60)
            return None
        return send_file(export_path + '.zip')

    @classmethod
    def get_capability_content(cls):
        """
        Get capability list content.

        :return: (Resource Obj) list resource dump and resource list
        """
        list_change = cls.get_all()
        caplist = []
        for change in list_change:
            if change._validation():
                caplist.append(Resource(
                    '{}/changelist.xml'.format(change.url_path),
                    capability='changelist'))
                caplist.append(Resource(
                    '{}/changedump.xml'.format(change.url_path),
                    capability='changedump'))
        return caplist

    def _date_validation(self, date_from: str):
        """
        Delete unregister bucket by pid.

        Arguments:
            date_from       -- record uuid link to checking bucket.
        Returns:
            from_date in in isoformat or None.

        """
        try:
            ret = datetime.datetime.strptime(date_from, r"%Y%m%d")

            if self.publish_date <= ret < datetime.datetime.utcnow():
                return ret
        except ValueError:
            current_app.logger.debug("Incorrect datetime format, should be "
                                     "YYYYMMDD")
        return None

    def _next_change(self, data, changes):
        """
        Get change list xml.

        :param data     :
        :param changes  :
        :return: Updated Change List info
        """
        for change in changes:
            if data.get('record_id') == change.get('record_id') and \
                data.get('record_version') + 1 == \
                    change.get('record_version'):
                return change

        return None

    def _get_record_changes_with_interval(self, from_date):
        """
        Get change list xml.

        :param data     :
        :param changes  :
        :return: Updated Change List info
        """
        _from = self._date_validation(from_date)
        if not _from:
            return []
        _util = _from + datetime.timedelta(days=self.interval_by_date)

        if _util > datetime.datetime.utcnow():
            _util = datetime.datetime.utcnow()

        record_changes = self._get_record_changes(
            self.repository_id,
            _from.isoformat(),
            _util.isoformat()
        )

        return record_changes

    def _get_record_changes(self, repo_id, from_date, until_date):
        """
        Get change list xml.

        :param data     :
        :param changes  :
        :return: Updated Change List info
        """
        from .utils import query_record_changes

        try:
            return query_record_changes(
                repo_id,
                from_date,
                until_date,
                self.max_changes_size,
                self.change_tracking_state
            )
        except BaseException as ex:
            current_app.logger.debug(ex)
            return []
