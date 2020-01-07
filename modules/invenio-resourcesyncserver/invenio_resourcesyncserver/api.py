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
from flask import current_app, json, request
from invenio_db import db
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import aliased
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.sql.expression import func, literal_column
from weko_search_ui.utils import get_items_by_index_tree
from resync import Resource, ResourceList
from resync.resource_dump import ResourceDump
from resync.resource_dump_manifest import ResourceDumpManifest
from resync.capability_list import CapabilityList
from .models import ResourceListIndexes
from weko_index_tree.api import Indexes
from weko_index_tree.models import Index
# from .utils import cached_index_tree_json, get_index_id_list, get_tree_json, \
#     get_user_roles, reset_tree


class ResourceSync(object):
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
                resource.repository_id = data.get('repository',
                                               resource.repository_id)
                resource.resource_dump_manifest = data.get(
                    'resource_dump_manifest',
                    resource.resource_dump_manifest)
                resource.url_path = data.get('url_path', resource.url_path)
                db.session.merge(resource)
            db.session.commit()
            # Indexes.update(index_id=resource.repository_id, **{'public_state': True})
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
            return resource
        except Exception as ex:
            current_app.logger.debug(ex)
            db.session.rollback()
        return

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
                list_result = db.session.query(ResourceListIndexes).join(Index).all()
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
                    if str(re.repository) in index_id:
                        return result
                return None
        except Exception as ex:
            current_app.logger.debug(ex)
            return None

    @classmethod
    def get_content_resource_list(cls, repository=''):
        resource = cls.get_resource_by_repository(repository)
        if not resource or not resource.status:
            return None

        r = get_items_by_index_tree(resource.repository_id)

        rl = ResourceList()
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
        resource = cls.get_resource_by_repository(repository)
        if not resource or not resource.status:
            return None
        r = get_items_by_index_tree(resource.repository_id)
        rd = ResourceDump()
        for item in r:
            if item:
                id_item = item.get('_source').get('_item_metadata').get(
                    'control_number')
                url = '{}resync/{}/file_content.zip'.format(
                    request.url_root,
                    str(id_item))
                rd.add(
                    Resource(url, lastmod=item.get('_source').get('_updated')))
        return rd.as_xml()

    @classmethod
    def get_capability_list(cls):
        list_resource = cls.get_list_resource()
        caplist = CapabilityList()
        for resource in list_resource:
            caplist.add(Resource(
                '{}/resourcelist.xml'.format(resource.url_path),
                capability='resourcelist'.format(resource.index.index_name)))
            caplist.add(Resource(
                '{}/resourcedump.xml'.format(resource.url_path),
                capability='resourcedump'.format(resource.index.index_name)))
        return caplist.as_xml()
