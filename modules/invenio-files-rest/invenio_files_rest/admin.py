# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Admin model views for PersistentIdentifier."""

import uuid

from flask import current_app, flash, url_for
from flask_admin.actions import action
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from invenio_admin.filters import FilterConverter
from invenio_admin.forms import LazyChoices
from markupsafe import Markup
from wtforms.validators import ValidationError

from .models import (
    Bucket,
    FileInstance,
    Location,
    MultipartObject,
    ObjectVersion,
    slug_pattern,
)
from .tasks import verify_checksum


def _(x):
    """Identity function for string extraction."""
    return x


def require_slug(form, field):
    """Validate location name."""
    if not slug_pattern.match(field.data):
        raise ValidationError(_("Invalid location name."))


def link(text, link_func):
    """Generate a object formatter for links.."""

    def object_formatter(v, c, m, p):
        """Format object view link."""
        return Markup('<a href="{0}">{1}</a>'.format(link_func(m), text))

    return object_formatter


class LocationModelView(ModelView):
    """ModelView for the locations."""

    filter_converter = FilterConverter()
    can_create = True
    can_edit = False
    can_delete = True
    can_view_details = True
    column_formatters = dict(
        buckets=link("Buckets", lambda o: url_for("bucket.index_view", flt2_2=o.name))
    )
    column_details_list = ("name", "uri", "default", "created", "updated", "buckets")
    column_list = ("name", "uri", "default", "created", "updated", "buckets")
    column_labels = dict(
        id=_("ID"),
        uri=_("URI"),
    )
    column_filters = (
        "default",
        "created",
        "updated",
    )
    column_searchable_list = ("uri", "name")
    column_default_sort = "name"
    form_base_class = FlaskForm
    form_columns = ("name", "uri", "default")
    form_args = dict(name=dict(validators=[require_slug]))
    page_size = 25


class BucketModelView(ModelView):
    """ModelView for the buckets."""

    filter_converter = FilterConverter()
    can_create = True
    can_delete = False
    can_edit = True
    can_view_details = True
    column_formatters = dict(
        objects=link(
            "Objects",
            lambda o: url_for(
                "objectversion.index_view", flt0_0=o.id, flt1_37=1, sort=1
            ),
        ),
        object_versions=link(
            "Object Versions",
            lambda o: url_for(
                "objectversion.index_view", flt0_0=o.id, flt1_29=1, sort=1
            ),
        ),
    )
    column_details_list = (
        "id",
        "location",
        "default_storage_class",
        "deleted",
        "locked",
        "size",
        "quota_size",
        "max_file_size",
        "created",
        "updated",
        "objects",
        "object_versions",
    )
    column_list = (
        "id",
        "location",
        "default_storage_class",
        "deleted",
        "locked",
        "size",
        "quota_size",
        "created",
        "updated",
        "objects",
    )
    column_labels = dict(
        id=_("UUID"),
        default_location=_("Location"),
        pid_provider=_("Storage Class"),
    )
    column_filters = (
        # Change of order affects Location.column_formatters!
        "location.name",
        "default_storage_class",
        "deleted",
        "locked",
        "size",
        "created",
        "updated",
    )
    column_default_sort = ("updated", True)
    form_base_class = FlaskForm
    form_columns = (
        "default_storage_class",
        "locked",
        "deleted",
        "quota_size",
        "max_file_size",
    )
    form_choices = dict(
        default_storage_class=LazyChoices(
            lambda: current_app.config["FILES_REST_STORAGE_CLASS_LIST"].items()
        )
    )
    page_size = 25


class ObjectModelView(ModelView):
    """ModelView for the objects."""

    filter_converter = FilterConverter()
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_formatters = dict(
        file_instance=link(
            "File", lambda o: url_for("fileinstance.index_view", flt0_0=o.file_id)
        ),
        versions=link(
            "Versions",
            lambda o: url_for(
                "objectversion.index_view",
                sort=7,
                desc=1,
                flt0_0=o.bucket_id,
                flt1_29=o.key,
            ),
        ),
        bucket_objs=link(
            "Objects",
            lambda o: url_for(
                "objectversion.index_view", flt0_0=o.bucket_id, flt1_37=1, sort=1
            ),
        ),
    )
    column_labels = {
        "version_id": _("Version"),
        "file_id": _("File UUID"),
        "file.uri": _("URI"),
        "file.size": _("Size"),
        "is_deleted": _("Deleted"),
        "file.checksum": _("Checksum"),
        "file.readable": _("Readable"),
        "file.storage_class": _("Storage class"),
        "bucket_objs": _("Objects"),
        "file_instance": _("File"),
    }
    column_list = (
        "bucket",
        "key",
        "version_id",
        "file.uri",
        "is_head",
        "is_deleted",
        "file.size",
        "created",
        "updated",
        "versions",
        "bucket_objs",
        "file_instance",
    )
    column_searchable_list = ("key",)
    column_details_list = (
        "bucket",
        "key",
        "version_id",
        "file_id",
        "file.uri",
        "file.checksum",
        "file.size",
        "file.storage_class",
        "is_head",
        "is_deleted",
        "created",
        "updated",
        "file_instance",
        "versions",
    )
    column_filters = (
        # Order affects column_formatters in other model views.
        "bucket.id",
        "bucket.locked",
        "bucket.deleted",
        "bucket.location.name",
        "file_id",
        "file.checksum",
        "file.storage_class",
        "file.readable",
        "key",
        "version_id",
        "is_head",
        "file.size",
        "created",
        "updated",
    )
    column_sortable_list = (
        "key",
        "file.uri",
        "is_head",
        "file.size",
        "created",
        "updated",
    )
    column_default_sort = ("updated", True)
    page_size = 25


class FileInstanceModelView(ModelView):
    """ModelView for the objects."""

    filter_converter = FilterConverter()
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_formatters = dict(
        objects=link(
            "Objects", lambda o: url_for("objectversion.index_view", flt3_12=o.id)
        ),
    )
    column_labels = dict(
        id=_("ID"),
        uri=_("URI"),
        last_check=_("Fixity"),
        last_check_at=_("Checked"),
    )
    column_list = (
        "id",
        "uri",
        "storage_class",
        "size",
        "checksum",
        "readable",
        "writable",
        "last_check",
        "last_check_at",
        "created",
        "updated",
        "objects",
    )
    column_searchable_list = (
        "uri",
        "size",
        "checksum",
    )
    column_details_list = (
        "id",
        "uri",
        "storage_class",
        "size",
        "checksum",
        "readable",
        "writable",
        "last_check",
        "last_check_at",
        "created",
        "updated",
        "objects",
    )
    column_filters = (
        "id",
        "uri",
        "storage_class",
        "size",
        "checksum",
        "readable",
        "writable",
        "last_check",
        "last_check_at",
        "created",
        "updated",
        "objects",
    )
    column_default_sort = ("updated", True)
    page_size = 25

    @action("verify_checksum", _("Run fixity check"))
    def action_verify_checksum(self, ids):
        """Inactivate users."""
        try:
            count = 0
            for file_id in ids:
                f = FileInstance.query.filter_by(id=uuid.UUID(file_id)).one_or_none()
                if f is None:
                    raise ValueError(_("Cannot find file instance."))
                verify_checksum.delay(file_id)
                count += 1
            if count > 0:
                flash(_("Fixity check(s) sent to queue."), "success")
        except Exception as exc:
            if not self.handle_view_exception(exc):
                raise
            current_app.logger.exception(str(exc))  # pragma: no cover
            flash(_("Failed to run fixity checks."), "error")  # pragma: no cover


class MultipartObjectModelView(ModelView):
    """ModelView for the objects."""

    filter_converter = FilterConverter()
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_formatters = dict(
        file_instance=link(
            "File", lambda o: url_for("fileinstance.index_view", flt0_0=o.file_id)
        ),
    )
    column_labels = dict(
        id=_("ID"),
        completed=_("Complete"),
        file_instance=_("File"),
    )
    column_list = (
        "upload_id",
        "completed",
        "created",
        "updated",
        "file_instance",
    )
    column_details_list = (
        "upload_id",
        "completed",
        "created",
        "updated",
        "file_instance",
    )
    column_filters = (
        "upload_id",
        "completed",
        "created",
        "updated",
    )
    column_default_sort = ("upload_id", True)
    page_size = 25


location_adminview = dict(
    modelview=LocationModelView, model=Location, category=_("Files")
)
bucket_adminview = dict(modelview=BucketModelView, model=Bucket, category=_("Files"))
object_adminview = dict(
    modelview=ObjectModelView, model=ObjectVersion, category=_("Files")
)
fileinstance_adminview = dict(
    modelview=FileInstanceModelView, model=FileInstance, category=_("Files")
)
multipartobject_adminview = dict(
    modelview=MultipartObjectModelView, model=MultipartObject, category=_("Files")
)
