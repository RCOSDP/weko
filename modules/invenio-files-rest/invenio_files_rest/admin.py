# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin model views for PersistentIdentifier."""

from __future__ import absolute_import, print_function

import os
import uuid

from flask import current_app, flash, url_for
from flask_admin.actions import action
from flask_admin import expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import SecureForm
from flask_babelex import gettext as _
from flask_security import current_user
from flask_wtf import FlaskForm
from invenio_admin.filters import FilterConverter
from invenio_admin.forms import LazyChoices
from invenio_db import db
from markupsafe import Markup
from sqlalchemy.exc import SQLAlchemyError
from wtforms.fields import PasswordField
from wtforms.fields import StringField, SelectField, IntegerField
from wtforms.fields import BooleanField
from wtforms.validators import ValidationError, NumberRange, Length, Optional
from wtforms.widgets import PasswordInput

from .models import Bucket, FileInstance, Location, MultipartObject, \
    ObjectVersion, slug_pattern
from .tasks import verify_checksum


def require_slug(form, field):
    """Validate location name."""
    if not slug_pattern.match(field.data):
        raise ValidationError(_("Invalid location name."))

def validate_uri(form, field):
    """
    Validate the URI field based on the value of the 'type' field.

    This function checks if the 'type' field in the form is set to
    'FILES_REST_LOCATION_TYPE_S3_VIRTUAL_HOST_VALUE'. If so, it ensures
    that the URI field starts with 'https://'. If the condition is not
    met, a ValidationError is raised.

    Args:
        form (wtforms.Form): The form object containing the fields.
        field (wtforms.Field): The field being validated (URI field).

    Raises:
        ValidationError: If the URI does not start with 'https://' when
        the 'type' field is set to 'FILES_REST_LOCATION_TYPE_S3_VIRTUAL_HOST_VALUE'.
    """
    if form.type.data == \
            current_app.config['FILES_REST_LOCATION_TYPE_S3_VIRTUAL_HOST_VALUE'] and \
            not field.data.startswith('https://'):
        raise ValidationError(_("Invalid URL. It should start with https://"))

def link(text, link_func):
    """Generate a object formatter for links.."""
    def object_formatter(v, c, m, p):
        """Format object view link."""
        return Markup('<a href="{0}">{1}</a>'.format(
            link_func(m), text))
    return object_formatter


class LocationModelView(ModelView):
    """ModelView for the locations."""

    filter_converter = FilterConverter()
    can_view_details = True
    column_formatters = dict(
        buckets=link('Buckets', lambda o: url_for(
            'bucket.index_view', flt2_2=o.name))
    )
    column_details_list = (
        'type', 'name', 'uri', 'default', 'size', 'quota_size',
        'created', 'updated', 'buckets')
    column_list = (
        'type', 'name', 'uri', 'default', 'size', 'quota_size',
        'created', 'updated', 'buckets')
    column_labels = dict(
        id=_('ID'),
        uri=_('URI'),
        size=_('Size'),
        quota_size=_('Quota Size'),
        access_key=_('Access Key'),
        secret_key=_('Secret Key'),
        s3_endpoint_url=_('S3_ENDPOINT_URL'),
        s3_send_file_directly=_('S3_SEND_FILE_DIRECTLY'),
        s3_default_block_size=_('S3_DEFAULT_BLOCK_SIZE'),
        s3_maximum_number_of_parts=_('S3_MAXIMUM_NUMBER_OF_PARTS'),
        s3_region_name=_('S3_REGION_NAME'),
        s3_signature_version=_('S3_SIGNATURE_VERSION'),
        s3_url_expiration=_('S3_URL_EXPIRATION'),
    )
    column_filters = ('default', 'created', 'updated', )
    column_searchable_list = ('uri', 'name')
    column_default_sort = 'name'
    form_base_class = SecureForm
    form_columns = (
        'name', 'uri', 'type', 'access_key', 'secret_key',
        's3_endpoint_url', 's3_send_file_directly',
        's3_default_block_size', 's3_maximum_number_of_parts',
        's3_region_name', 's3_signature_version', 's3_url_expiration',
        'quota_size', 'default')
    form_choices = {
        'type': LazyChoices(
            lambda: current_app.config['FILES_REST_LOCATION_TYPE_LIST'])
    }
    form_extra_fields = {
        'access_key': PasswordField('access_key',
                                    widget=PasswordInput(hide_value=False)),
        'secret_key': PasswordField('secret_key',
                                    widget=PasswordInput(hide_value=False)),
        's3_endpoint_url': StringField('endpoint_url'),
        's3_send_file_directly': BooleanField('send_file_directly'),
        's3_default_block_size': IntegerField('default_block_size', validators=[NumberRange(min=0), Optional()]),
        's3_maximum_number_of_parts': IntegerField('maximum_number_of_parts', validators=[NumberRange(min=0), Optional()]),
        's3_region_name': StringField('region_name', validators=[
            Length(max=120, message='max 120 characters')
        ]),
        's3_signature_version': SelectField('signature_version',
            choices=[
            ('s3', 's3'),
            ('s3v4', 's3v4'),
            ]),
        's3_url_expiration': IntegerField('url_expiration', validators=[NumberRange(min=0), Optional()]),
    }
    form_args = dict(
        name=dict(validators=[require_slug]),
        uri=dict(validators=[validate_uri]),
    )
    page_size = 25
    edit_template = 'admin/location_edit.html'
    create_template = 'admin/location_edit.html'

    _system_role = os.environ.get('INVENIO_ROLE_SYSTEM',
                                  'System Administrator')
    @expose('/')
    def index_view(self):
        """Override index view to add custom logic.

        This method checks the number of default locations and
        flashes messages based on the count.
        """
        try:
            count = Location.query.filter_by(default=True).count()
            if count < 1:
                flash(_("No default location is set. "
                        "Please configure one location as default."),
                      category="warning")
            elif count > 1:
                flash(_("Multiple locations are set as default. "
                        "Only one default location can be configured. "
                        "Please correct the settings."),
                      category="warning")
        except SQLAlchemyError as ex:
            current_app.logger.error(
                f"Error while checking default locations: {ex}"
            )
        except Exception as ex:
            current_app.logger.exception("unexpected error in index_view")
        return super().index_view()

    def on_model_change(self, form, model, is_created):
        """Perform some actions before a model is created or updated.

        Called from create_model and update_model in the same transaction

        Args:
            form(LocationForm): The form instance used to edit the model.
            model(Location): The Location model instance being created or updated.
            is_created (bool): True if the model is being created, False if it is being updated.

        Raises:
            ValidationError: If another location is already set as default.
        """
        if model.default:
            with db.session.no_autoflush:
                query = Location.query.filter_by(default=True)
                if model.id:
                    query = query.filter(Location.id != model.id)
                if query.first():
                    current_app.logger.error(
                        "ValidationError: Cannot save because another location is already set as default."
                    )
                    raise ValidationError(
                        _("Cannot save because another location is already set as default.")
                    )

        if is_created:
            model.s3_send_file_directly = True
            if (model.type ==
                current_app.config['FILES_REST_LOCATION_TYPE_S3_PATH_VALUE']):
                model.s3_signature_version = None
                if not model.uri.endswith('/'):
                    model.uri = model.uri + '/'
                if (model.s3_endpoint_url and
                    not model.s3_endpoint_url.endswith('/')):
                    model.s3_endpoint_url = model.s3_endpoint_url + '/'
            elif (model.type ==
                  current_app.config['FILES_REST_LOCATION_TYPE_S3_VIRTUAL_HOST_VALUE']):
                model.s3_signature_version = None
                if not model.uri.endswith('/'):
                    model.uri = model.uri + '/'
                model.s3_endpoint_url = model.uri
            else:
                model.s3_default_block_size = None
                model.s3_maximum_number_of_parts = None
                model.s3_region_name = None
                model.s3_signature_version = None
                model.s3_url_expiration = None
        else:
            if (model.type ==
                current_app.config['FILES_REST_LOCATION_TYPE_S3_PATH_VALUE']):
                if not model.uri.endswith('/'):
                    model.uri = model.uri + '/'
                if not model.s3_endpoint_url.endswith('/'):
                    model.s3_endpoint_url = model.s3_endpoint_url + '/'
            elif (model.type ==
                  current_app.config['FILES_REST_LOCATION_TYPE_S3_VIRTUAL_HOST_VALUE']):
                if not model.uri.endswith('/'):
                    model.uri = model.uri + '/'
                model.s3_endpoint_url = model.uri
            else:
                # local
                model.s3_default_block_size = None
                model.s3_maximum_number_of_parts = None
                model.s3_url_expiration = None
                model.s3_region_name = None
                model.s3_signature_version = None

    def _handle_default_checkbox(self, form, obj=None):
        """Disable the 'default' checkbox in the form if another default Location exists.

        Args:
            form (wtforms.Form): The form instance being created or edited.
            obj (Location, optional): The Location object being edited. None if creating a new object.

        Raises:
            Exception: Any exception is logged but not re-raised.
        """
        try:
            if obj and obj.default:
                return

            query = Location.query.filter_by(default=True)
            if obj:
                query = query.filter(Location.id != obj.id)

            if query.first() and not form.default.data:
                form.default.render_kw = (form.default.render_kw or {})
                form.default.render_kw['disabled'] = True

        except Exception as e:
            current_app.logger.exception("Error in _handle_default_checkbox")

    def create_form(self, obj=None):
        """Instantiate model creation form and return it.

        Args:
            obj: The object being created.
        """
        form = super().create_form(obj)
        self._handle_default_checkbox(form, obj)
        return form

    def edit_form(self, obj=None):
        """
        Instantiate model editing form and return it.

        Args:
            obj: The object being edited.
        """
        form = super().edit_form(obj)
        self._handle_default_checkbox(form, obj)
        return form

    @property
    def can_create(self):
        """Check permission for creating."""
        return self._system_role in [role.name for role in current_user.roles]

    @property
    def can_edit(self):
        """Check permission for Editing."""
        return self._system_role in [role.name for role in current_user.roles]

    @property
    def can_delete(self):
        """Check permission for Deleting."""
        return self._system_role in [role.name for role in current_user.roles]


class BucketModelView(ModelView):
    """ModelView for the buckets."""

    filter_converter = FilterConverter()
    can_create = True
    can_delete = False
    can_edit = True
    can_view_details = True
    column_formatters = dict(
        objects=link('Objects', lambda o: url_for(
            'objectversion.index_view', flt0_0=o.id, flt1_37=1, sort=1)),
        object_versions=link('Object Versions', lambda o: url_for(
            'objectversion.index_view', flt0_0=o.id, flt1_29=1, sort=1)),
    )
    column_details_list = (
        'id', 'location', 'default_storage_class', 'deleted', 'locked', 'size',
        'quota_size', 'max_file_size', 'created', 'updated', 'objects',
        'object_versions',
    )
    column_list = (
        'id', 'location', 'default_storage_class', 'deleted', 'locked', 'size',
        'quota_size', 'created', 'updated', 'objects',
    )
    column_labels = dict(
        id=_('UUID'),
        default_location=_('Location'),
        pid_provider=_('Storage Class'),
    )
    column_filters = (
        # Change of order affects Location.column_formatters!
        'location.name', 'default_storage_class', 'deleted', 'locked', 'size',
        'created', 'updated',
    )
    column_default_sort = ('updated', True)
    form_base_class = FlaskForm
    form_columns = (
        'default_storage_class', 'locked', 'deleted', 'quota_size',
        'max_file_size'
    )
    form_choices = dict(
        default_storage_class=LazyChoices(lambda: current_app.config[
            'FILES_REST_STORAGE_CLASS_LIST'].items()))
    page_size = 25


class ObjectModelView(ModelView):
    """ModelView for the objects."""

    filter_converter = FilterConverter()
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_formatters = dict(
        file_instance=link('File', lambda o: url_for(
            'fileinstance.index_view', flt0_0=o.file_id)),
        versions=link('Versions', lambda o: url_for(
            'objectversion.index_view',
            sort=7, desc=1, flt0_0=o.bucket_id, flt1_29=o.key)),
        bucket_objs=link('Objects', lambda o: url_for(
            'objectversion.index_view',
            flt0_0=o.bucket_id, flt1_37=1, sort=1)),
    )
    column_labels = {
        'version_id': _('Version'),
        'file_id': _('File UUID'),
        'file.uri': _('URI'),
        'file.size': _('Size'),
        'is_deleted': _('Deleted'),
        'file.checksum': _('Checksum'),
        'file.readable': _('Readable'),
        'file.storage_class': _('Storage class'),
        'bucket_objs': _("Objects"),
        'file_instance': _("File"),
    }
    column_list = (
        'bucket', 'key', 'version_id', 'file.uri', 'is_head',
        'file.size', 'created', 'updated', 'versions', 'bucket_objs',
        'file_instance')
    column_searchable_list = ('key', )
    column_details_list = (
        'bucket', 'key', 'version_id', 'file_id', 'file.uri', 'file.checksum',
        'file.size', 'file.storage_class', 'is_head', 'is_deleted', 'created',
        'updated', 'file_instance', 'versions')
    column_filters = (
        # Order affects column_formatters in other model views.
        'bucket.id', 'bucket.locked', 'bucket.deleted', 'bucket.location.name',
        'file_id', 'file.checksum', 'file.storage_class', 'file.readable',
        'key', 'version_id', 'is_head', 'file.size', 'created', 'updated', )
    column_sortable_list = (
        'key', 'file.uri', 'is_head', 'file.size', 'created', 'updated')
    column_default_sort = ('updated', True)
    page_size = 25


class FileInstanceModelView(ModelView):
    """ModelView for the objects."""

    filter_converter = FilterConverter()
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_formatters = dict(
        objects=link('Objects', lambda o: url_for(
            'objectversion.index_view', flt3_12=o.id)),
    )
    column_labels = dict(
        id=_('ID'),
        uri=_('URI'),
        last_check=_('Fixity'),
        last_check_at=_('Checked'),
    )
    column_list = (
        'id', 'uri', 'storage_class', 'size', 'checksum', 'readable',
        'writable', 'last_check', 'last_check_at', 'created', 'updated',
        'objects')
    column_searchable_list = ('uri', 'size', 'checksum', )
    column_details_list = (
        'id', 'uri', 'storage_class', 'size', 'checksum', 'readable',
        'writable', 'last_check', 'last_check_at', 'created', 'updated',
        'objects')
    column_filters = (
        'id', 'uri', 'storage_class', 'size', 'checksum', 'readable',
        'writable', 'last_check', 'last_check_at', 'created', 'updated',
        'objects')
    column_default_sort = ('updated', True)
    page_size = 25

    @action('verify_checksum', _('Run fixity check'))
    def action_verify_checksum(self, ids):
        """Inactivate users."""
        try:
            count = 0
            for file_id in ids:
                f = FileInstance.query.filter_by(
                    id=uuid.UUID(file_id)).one_or_none()
                if f is None:
                    raise ValueError(_("Cannot find file instance."))
                verify_checksum.delay(file_id)
                count += 1
            if count > 0:
                flash(_('Fixity check(s) sent to queue.'), 'success')
        except Exception as exc:
            if not self.handle_view_exception(exc):
                raise
            current_app.logger.exception(str(exc))  # pragma: no cover
            flash(_('Failed to run fixity checks.'),
                  'error')  # pragma: no cover


class MultipartObjectModelView(ModelView):
    """ModelView for the objects."""

    filter_converter = FilterConverter()
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_formatters = dict(
        file_instance=link('File', lambda o: url_for(
            'fileinstance.index_view', flt0_0=o.file_id)),
    )
    column_labels = dict(
        id=_('ID'),
        completed=_('Complete'),
        file_instance=_('File'),
    )
    column_list = (
        'upload_id', 'completed', 'created', 'updated', 'file_instance', )
    column_details_list = (
        'upload_id', 'completed', 'created', 'updated', 'file_instance', )
    column_filters = (
        'upload_id', 'completed', 'created', 'updated', )
    column_default_sort = ('upload_id', True)
    page_size = 25


location_adminview = dict(
    modelview=LocationModelView,
    model=Location,
    category=_('Files'))
bucket_adminview = dict(
    modelview=BucketModelView,
    model=Bucket,
    category=_('Files'))
object_adminview = dict(
    modelview=ObjectModelView,
    model=ObjectVersion,
    category=_('Files'))
fileinstance_adminview = dict(
    modelview=FileInstanceModelView,
    model=FileInstance,
    category=_('Files'))
multipartobject_adminview = dict(
    modelview=MultipartObjectModelView,
    model=MultipartObject,
    category=_('Files'))
