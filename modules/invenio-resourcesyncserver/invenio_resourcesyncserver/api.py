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

from flask import current_app, json, request
from invenio_db import db
from resync import Resource, ResourceList
from resync.capability_list import CapabilityList
from resync.resource_dump import ResourceDump
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.change_dump import ChangeDump
from resync.change_list import ChangeList
from resync.change_dump_manifest import ChangeDumpManifest
from sqlalchemy.exc import SQLAlchemyError
from weko_index_tree.models import Index
from weko_index_tree.api import Indexes
from weko_deposit.api import WekoRecord

from .models import ResourceListIndexes, ChangeListIndexes
from .query import get_items_by_index_tree


class ResourceListHandler(object):
    """Define API for ResourceListIndexes creation and update."""

    @classmethod
    def create(cls, data={}):
        """Create the ResourceListIndexes.

        :param data: the index information.
        :returns: The :class:`ResourceListIndexes`.
        """
        new_data = dict(**{
            'status': data.get('status', False),
            'repository_id': data.get('repository', ''),
            'resource_dump_manifest': data.get('resource_dump_manifest', False),
            'url_path': data.get('url_path', ''),
        })
        try:
            with db.session.begin_nested():
                resource = ResourceListIndexes(**new_data)
                db.session.add(resource)
            db.session.commit()
            # publish index
            return dict(**{
                'id': resource.id,
            }, **new_data)
        except SQLAlchemyError as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
            return {}

    @classmethod
    def update(cls, resource_id='', data={}):
        """
        Update the index detail info.

        :param resource_id: Identifier of the Resource.
        :param data: new Resource info for update.
        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                resource = cls.get_resource(resource_id)
                if not resource:
                    return
                resource.status = data.get('status', resource.status)
                resource.repository_id = data.get(
                    'repository',
                    resource.repository_id
                )
                resource.resource_dump_manifest = data.get(
                    'resource_dump_manifest',
                    resource.resource_dump_manifest)
                resource.url_path = data.get('url_path', resource.url_path)
                db.session.merge(resource)
            db.session.commit()
            return resource
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return

    @classmethod
    def delete(cls, resource_id=''):
        """
        Update the index detail info.

        :param resource_id: Identifier of the Resource.
        :param data: new Resource info for update.
        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                resource = cls.get_resource(resource_id)
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
    def get_list_resource(cls):
        """
        Update the index detail info.

        :param resource_id: Identifier of the Resource.
        :param data: new Resource info for update.
        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                list_result = db.session.query(ResourceListIndexes).join(
                    Index
                ).all()
                return list_result
        except Exception as ex:
            current_app.logger.debug(ex)
            return []

    @classmethod
    def get_resource(cls, resource_id=''):
        """
        Update the index detail info.

        :param resource_id: Identifier of the Resource.
        :param data: new Resource info for update.
        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                result = db.session.query(ResourceListIndexes).filter(
                    ResourceListIndexes.id == resource_id).one_or_none()
                return result
        except Exception as ex:
            current_app.logger.debug(ex)
            return

    @classmethod
    def get_resource_by_repository_id(cls, repository_id=''):
        """
        Update the index detail info.

        :param resource_id: Identifier of the Resource.
        :param data: new Resource info for update.
        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                result = db.session.query(ResourceListIndexes).filter_by(
                    repository_id=repository_id).one_or_none()
                return result
        except Exception as ex:
            current_app.logger.debug(ex)
            return

    @classmethod
    def get_resource_by_repository(cls, index_id=''):
        """
        Update the index detail info.

        :param index_id: new Resource info for update.
        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                result = db.session.query(ResourceListIndexes).filter_by(
                    repository_id=index_id).one_or_none()
                return result
        except Exception as ex:
            current_app.logger.debug(ex)
            return

    @classmethod
    def is_resync(cls, index_id=[]):
        """
        Update the index detail info.

        :param index_id: new Resource info for update.
        :return: Updated Resource info
        """
        try:
            with db.session.begin_nested():
                result = db.session.query(ResourceListIndexes).filter(
                    ResourceListIndexes.status).all()
                for re in result:
                    if str(re.repository_id) in index_id:
                        return result
                return None
        except Exception as ex:
            current_app.logger.debug(ex)
            return None

    @classmethod
    def get_content_resource_list(cls, repository=''):
        """
        Get content of resource list.

        :param repository: repository_id
        :return: (xml) resource list content
        """
        resource = cls.get_resource_by_repository(repository)
        if not resource or not resource.status:
            return None

        r = get_items_by_index_tree(resource.repository_id)
        current_app.logger.debug("====================")
        current_app.logger.debug(r)
        rl = ResourceList()
        rl.up = '{}resync/capability.xml'.format(request.url_root)
        for item in r:
            if item:
                id_item = item.get('_source').get('_item_metadata').get(
                    'control_number')
                url = '{}records/{}'.format(request.url_root, str(id_item))
                rl.add(Resource(url, lastmod=item.get('_source').get(
                    '_updated')))
        return rl.as_xml()

    @classmethod
    def get_content_resource_dump(cls, repository=''):
        """
        Get content of resource dump.

        :param repository: repository_id
        :return: (xml) resource dump content
        """
        resource = cls.get_resource_by_repository(repository)
        if not resource or not resource.status:
            return None
        r = get_items_by_index_tree(resource.repository_id)
        rd = ResourceDump()
        rd.up = '{}resync/capability.xml'.format(request.url_root)
        for item in r:
            if item:
                id_item = item.get('_source').get('_item_metadata').get(
                    'control_number')
                url = '{}resync/{}/{}/file_content.zip'.format(
                    request.url_root,
                    resource.repository_id,
                    str(id_item))
                rs = Resource(
                    url,
                    lastmod=item.get('_source').get('_updated'),
                    ln=[]
                )
                if resource.resource_dump_manifest:
                    href = '{}resync/{}/{}/resourcedump_manifest.xml'.format(
                        request.url_root,
                        resource.repository_id,
                        str(id_item)
                    )
                    rs.ln.append({
                        'rel': 'contents',
                        'href': href,
                        'type': 'application/xml'})
                rd.add(rs)
        return rd.as_xml()

    @classmethod
    def get_capability_list(cls):
        """
        Get capability_list.

        :return: (xml) list resource dump and resource list
        """
        list_resource = cls.get_list_resource()
        caplist = CapabilityList()
        for resource in list_resource:
            caplist.add(Resource(
                '{}/resourcelist.xml'.format(resource.url_path),
                capability='resourcelist'))
            caplist.add(Resource(
                '{}/resourcedump.xml'.format(resource.url_path),
                capability='resourcedump'))
        return caplist.as_xml()

    @classmethod
    def get_resourcedump_manifest(cls, index_id, record):
        """
        Get resource dump manifest.

        :param index_id: repository_id of resource.
        :param record: record object.
        :return: (xml) content of resourcedump
        """
        rdm = ResourceDumpManifest()
        rdm.up = '{}resync/{}/resourcedump.xml'.format(
            request.url_root,
            index_id
        )
        cur_resource = cls.get_resource_by_repository_id(index_id)
        if not cur_resource.resource_dump_manifest:
            return None
        for file in record.files:  # TODO: Temporary processing
            file_info = file.info()
            path = 'recid_{}/{}'.format(
                record.get('recid'),
                file_info.get('filename'))
            lastmod = str(datetime.datetime.utcnow().replace(
                tzinfo=datetime.timezone.utc
            ).isoformat())
            rdm.add(Resource(
                '{}record/{}/files/{}'.format(
                    request.url_root,
                    record.get('recid'),
                    file_info.get('filename')),
                lastmod=lastmod,
                sha256=file_info.get('checksum').split(':')[1],
                length=str(file_info.get('size')),
                path=path
            ))
        return rdm.as_xml()


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

    def __init__(self, **kwargs):
        """Add extra options."""
        self.id = kwargs.get('id')
        self.status = kwargs.get('status')
        self.repository_id = kwargs.get('repository_id')
        self.change_dump_manifest = kwargs.get('change_dump_manifest')
        self.max_changes_size = int(kwargs.get('max_changes_size', 10000))
        self.url_path = kwargs.get('url_path')
        self.created = kwargs.get('created')
        self.updated = kwargs.get('updated')
        self.index = kwargs.get('index') or self.get_index()
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
            old_obj = self.get_change_list(self.id, 'modal')
            if old_obj:
                try:
                    with db.session.begin_nested():
                        old_obj.status = self.status or old_obj.status
                        old_obj.repository_id = self.repository_id or \
                            old_obj.repository_id
                        old_obj.change_dump_manifest = \
                            self.change_dump_manifest or \
                            old_obj.change_dump_manifest
                        old_obj.max_changes_size = self.max_changes_size or \
                            old_obj.max_changes_size
                        old_obj.change_tracking_state = \
                            self.change_tracking_state \
                            or old_obj.change_tracking_state
                        old_obj.url_path = self.url_path or old_obj.url_path
                        db.session.merge(old_obj)
                    db.session.commit()
                    return self
                except Exception as ex:
                    current_app.logger.debug(ex)
                    db.session.rollback()
                    return None
            else:
                return None
        else:
            data = dict(**{
                'status': self.status,
                'repository_id': self.repository_id,
                'change_dump_manifest': self.change_dump_manifest,
                'max_changes_size': self.max_changes_size,
                'change_tracking_state': self.change_tracking_state,
                'url_path': self.url_path,
            })
            try:
                with db.session.begin_nested():
                    obj = ChangeListIndexes(**data)
                    db.session.add(obj)
                db.session.commit()
                self.id = obj.id
                return self
            except SQLAlchemyError as ex:
                current_app.logger.debug(ex)
                db.session.rollback()
                return None

    def get_change_list_xml(self):
        """
        Get change list xml.

        :return: Updated Change List info
        """
        change_list = ChangeList()
        from .config import DATA_FAKE

        def next_change(data):
            for d in DATA_FAKE:
                if data.get('record_id') == d.get('record_id'):
                    if data.get('version_id')+1 == d.get('version_id'):
                        return d
            return None

        for data in DATA_FAKE:
            if next_change(data):
                loc = '{}records/{}'.format(
                    request.url_root,
                    '{}.{}'.format(
                        data.get('record_id'),
                        data.get('version_id')
                    )
                )
            else:
                loc = '{}records/{}'.format(
                    request.url_root,
                    data.get('record_id')
                )
            lastmod = str(datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc
                ).isoformat())
            rc = Resource(
                loc,
                lastmod=lastmod,
                change=data.get('state'),
                md_at=str(datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc
                ).isoformat()),
            )
            change_list.add(rc)
        return change_list.as_xml()

    def get_change_dump_xml(self):
        """
        Get change list xml.

        :return: Updated Change List info
        """
        from .config import DATA_FAKE

        def next_change(data):
            for d in DATA_FAKE:
                if data.get('record_id') == d.get('record_id'):
                    if data.get('version_id')+1 == d.get('version_id'):
                        return d
            return None

        change_dump = ChangeDump()

        for data in DATA_FAKE:
            next_ch = next_change(data)
            loc = '{}resync/{}/{}/changedump.zip'.format(
                request.url_root,
                self.repository_id,
                '{}.{}'.format(
                    data.get('record_id'),
                    data.get('version_id')
                )
            )
            lastmod = str(datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc
                ).isoformat())
            rc = Resource(
                loc,
                lastmod=lastmod,
                mime_type='application/zip',
                md_from=data.get('updated'),
                md_until=str(datetime.datetime.utcnow().replace(
                    tzinfo=datetime.timezone.utc
                ).isoformat()),
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
                            data.get('version_id')
                        )
                    ),
                    'type': 'application/xml'
                }
                rc.ln.append(ln)
            change_dump.add(rc)
        return change_dump.as_xml()

    def get_change_dump_manifest_xml(self, record_id):
        cdm = ChangeDumpManifest()
        cdm.up = '{}resync/{}/changedump.xml'.format(
            request.url_root,
            self.repository_id
        )
        if self.change_dump_manifest:
            prev_id, prev_ver_id = record_id.split(".")
            current_record = WekoRecord.get_record_by_pid(record_id)
            prev_record_pid = WekoRecord.get_pid(
                '{}.{}'.format(
                    prev_id,
                    str(int(prev_ver_id)-1)
                )
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
                        file_info.get('filename'))
                    lastmod = str(datetime.datetime.utcnow().replace(
                        tzinfo=datetime.timezone.utc
                    ).isoformat())
                    if change:
                        re = Resource(
                            '{}record/{}/files/{}'.format(
                                request.url_root,
                                current_record.get('recid'),
                                file_info.get('filename')),
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
        if self.repository_id:
            return Indexes.get_index(self.repository_id)
        else:
            return None

    def to_dict(self):
        change_dump_manifest = self.change_dump_manifest  \
            if self.change_dump_manifest else None
        max_changes_size = self.max_changes_size if self.max_changes_size \
            else None
        change_tracking_state = self.change_tracking_state if \
            self.change_tracking_state else None
        change_tracking_state = change_tracking_state.split("&") if \
            change_tracking_state else []
        return dict(**{
            'id': self.id if self.id else None,
            'status': self.status if self.status else None,
            'repository_id': self.repository_id if self.repository_id else None,
            'change_dump_manifest': change_dump_manifest,
            'max_changes_size': max_changes_size,
            'change_tracking_state': change_tracking_state,
            'url_path': self.url_path if self.url_path else None,
            'created': self.created if self.created else None,
            'updated': self.updated if self.updated else None,
            'repository_name': self.index.index_name,
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
                ).join(
                    Index
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
    def get_all(cls):
        """
        Get change list.

        :return: Updated Change List info
                """
        try:
            with db.session.begin_nested():
                result = db.session.query(ChangeListIndexes).join(
                    Index
                ).all()
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
            index=model.index
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
                ).join(
                    Index
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
