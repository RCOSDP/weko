from __future__ import annotations

import functools
import io
import json
import logging
import typing

import celery
from flask import url_for
from invenio_db import db
from sqlalchemy import true
from werkzeug.exceptions import Conflict
from werkzeug.http import parse_options_header

from invenio_deposit.api import Deposit
from invenio_deposit.api import has_status
from invenio_files_rest.models import ObjectVersion
from invenio_files_rest.models import ObjectVersionTag
from invenio_pidstore.resolver import Resolver
from invenio_records_files.api import FileObject, Record
from invenio_records_files.api import FilesIterator
from invenio_sword.enum import FileState
from invenio_sword.enum import ObjectTagKey
from invenio_sword.metadata import SWORDMetadata
from invenio_sword.typing import BytesReader
from sword3common.constants import DepositState
from sword3common.constants import Rel
from .metadata import Metadata
from .packaging import Packaging
from .schemas import ByReferenceFileDefinition
from .utils import TagManager

logger = logging.getLogger(__name__)


class SWORDFileObject(FileObject):
    def __init__(self, *args, pid, **kwargs):
        self.pid = pid
        return super().__init__(*args, **kwargs)

    @property
    def rest_file_url(self):
        return url_for(
            "invenio_sword.{}_file".format(self.pid.pid_type),
            pid_value=self.pid.pid_value,
            key=self.key,
            _external=True,
        )


class SWORDFilesIterator(FilesIterator):
    def _query(self):
        return ObjectVersion.query.outerjoin(ObjectVersionTag).filter(
            ObjectVersion.bucket == self.bucket,
            ObjectVersion.is_head == true(),
            ObjectVersion.file_id.isnot(None)
            | (
                (ObjectVersionTag.key == ObjectTagKey.ByReferenceNotDeleted.value)
                & (ObjectVersionTag.value == "true")
            ),
        )

    def __len__(self):
        return self._query().count()

    def __iter__(self):
        """Get iterator."""
        self._it = iter(self._query())
        return self


class SWORDDeposit(Deposit):
    @property
    def file_cls(self):
        return functools.partial(SWORDFileObject, pid=self.pid)

    files_iter_cls = SWORDFilesIterator

    def get_status_as_jsonld(self):
        editable = self["_deposit"].get("status") == "draft"

        return {
            "@id": self.sword_status_url,
            "@type": "Status",
            "metadata": {"@id": self.sword_metadata_url,},
            "fileSet": {"@id": self.sword_fileset_url,},
            "service": url_for(
                "invenio_sword.{}_service_document".format(self.pid.pid_type)
            ),
            "state": self.sword_states,
            "actions": {
                "getMetadata": True,
                "getFiles": True,
                "appendMetadata": editable,
                "appendFiles": editable,
                "replaceMetadata": editable,
                "replaceFiles": editable,
                "deleteMetadata": editable,
                "deleteFiles": editable,
                "deleteObject": editable,
            },
            "links": self.links,
        }

    @property
    def links(self):

        links = []
        for file in self.files or ():
            tags = TagManager(file)

            link = {
                "@id": file.rest_file_url,
                "contentType": file.obj.mimetype,
                "status": tags.get(ObjectTagKey.FileState, FileState.Ingested).value,
            }

            rel = set()
            if tags.get(ObjectTagKey.OriginalDeposit) == "true":
                rel.add(Rel.OriginalDeposit)
            if tags.get(ObjectTagKey.FileSetFile) == "true":
                rel.add(Rel.FileSetFile)
            derived_from = tags.get(ObjectTagKey.DerivedFrom)
            if derived_from:
                rel.add(Rel.DerivedResource)
                link["derivedFrom"] = url_for(
                    "invenio_sword.{}_file".format(self.pid.pid_type),
                    pid_value=self.pid.pid_value,
                    key=derived_from,
                    _external=True,
                )
            if ObjectTagKey.Packaging in tags:
                link["packaging"] = tags[ObjectTagKey.Packaging]
            if ObjectTagKey.MetadataFormat in tags:
                rel.add(Rel.FormattedMetadata)
                link["metadataFormat"] = tags[ObjectTagKey.MetadataFormat]

            link["rel"] = sorted(rel)

            links.append(link)

        return links

    @property
    def sword_states(self):
        states = []
        if self["_deposit"].get("status") == "draft":
            states.append(
                {
                    "@id": DepositState.InProgress,
                    "description": "the item is currently inProgress",
                }
            )
        elif self["_deposit"].get("status") == "published":
            states.append(
                {"@id": DepositState.Ingested, "description": "the item is ingested",}
            )
        return states

    @property
    def sword_status_url(self):
        return url_for(
            "invenio_sword.{}_item".format(self.pid.pid_type),
            pid_value=self.pid.pid_value,
            _external=True,
        )

    @property
    def sword_metadata_url(self):
        return url_for(
            "invenio_sword.{}_metadata".format(self.pid.pid_type),
            pid_value=self.pid.pid_value,
            _external=True,
        )

    @property
    def sword_fileset_url(self):
        return url_for(
            "invenio_sword.{}_fileset".format(self.pid.pid_type),
            pid_value=self.pid.pid_value,
            _external=True,
        )

    @property
    def metadata_key_prefix(self):
        return ".metadata-{}/".format(self.pid.pid_value)

    @property
    def original_deposit_key_prefix(self):
        return ".original-deposit-{}/".format(self.pid.pid_value)

    @has_status(status="draft")
    def ingest_file(
        self,
        stream: typing.Optional[BytesReader],
        packaging_name: str,
        content_disposition: str = None,
        content_type: str = None,
        replace=True,
    ):
        from . import tasks

        if stream:
            packaging = Packaging.for_record_and_name(self, packaging_name)

            content_disposition, content_disposition_options = parse_options_header(
                content_disposition or ""
            )
            content_type, _ = parse_options_header(content_type or "")
            filename = packaging.get_original_deposit_filename(
                content_disposition_options.get("filename"), content_type
            )
            object_version = ObjectVersion.create(
                bucket=self.bucket, key=filename, stream=stream
            )
            TagManager(object_version).update(
                {
                    ObjectTagKey.Packaging: packaging_name,
                    ObjectTagKey.OriginalDeposit: "true",
                }
            )
            db.session.refresh(object_version)
            task = self.unpack_object(object_version)
            if replace:
                task |= tasks.delete_old_objects.s(bucket_id=self.bucket_id)
            task.delay()
        elif replace:
            # We can do this synchronously, because it'll be quick
            tasks.delete_old_objects(bucket_id=self.bucket_id)

    # @has_status(status="draft")
    def set_metadata(
        self,
        source: typing.Optional[typing.Union[BytesReader, dict]],
        metadata_class: typing.Type[Metadata],
        content_type: str = None,
        derived_from: str = None,
        replace: bool = True,
    ) -> typing.Optional[Metadata]:
        if isinstance(source, dict):
            source = io.BytesIO(json.dumps(source).encode("utf-8"))

        if not content_type:
            content_type = metadata_class.content_type

        existing_metadata_object = (
            ObjectVersion.query.join(ObjectVersion.tags)
            .filter(
                ObjectVersion.is_head == true(),
                ObjectVersion.file_id.isnot(None),
                ObjectVersion.bucket == self.bucket,
                ObjectVersionTag.key == ObjectTagKey.MetadataFormat.value,
                ObjectVersionTag.value == metadata_class.metadata_format,
            )
            .first()
        )

        if source is None:
            if replace and existing_metadata_object:
                ObjectVersion.delete(
                    bucket=existing_metadata_object.bucket,
                    key=existing_metadata_object.key,
                )

            if replace and (
                self.get("swordMetadataSourceFormat") == metadata_class.metadata_format
            ):
                self.pop("swordMetadata", None)
                self.pop("swordMetadataSourceFormat", None)

            return None
        else:
            content_type, content_type_options = parse_options_header(content_type)

            encoding = content_type_options.get("charset")
            if isinstance(encoding, str):
                metadata = metadata_class.from_document(
                    source, content_type=content_type, encoding=encoding,
                )
            else:
                metadata = metadata_class.from_document(
                    source, content_type=content_type,
                )

            if existing_metadata_object and not replace:
                with existing_metadata_object.file.storage().open() as existing_metadata_f:
                    existing_metadata = metadata_class.from_document(
                        existing_metadata_f, content_type=metadata_class.content_type,
                    )
                try:
                    metadata = existing_metadata + metadata
                except TypeError:
                    raise Conflict(
                        "Existing or new metadata is of wrong type for appending. Reconcile client-side and PUT instead"
                    )

            metadata_filename = self.metadata_key_prefix + metadata_class.filename

            if (
                isinstance(metadata, SWORDMetadata)
                or "swordMetadata" not in self
                or (
                    not isinstance(metadata, SWORDMetadata)
                    and self["swordMetadataSourceFormat"]
                    == metadata_class.metadata_format
                )
            ):
                metadata.update_record_metadata(self)
                self["swordMetadata"] = metadata.to_sword_metadata()
                self["swordMetadataSourceFormat"] = metadata_class.metadata_format

            object_version = ObjectVersion.create(
                bucket=self.bucket,
                key=metadata_filename,
                stream=io.BytesIO(bytes(metadata)),
            )

            tags = TagManager(object_version)
            tags[ObjectTagKey.MetadataFormat] = metadata_class.metadata_format
            if derived_from:
                tags[ObjectTagKey.DerivedFrom] = derived_from

            return metadata

    def set_by_reference_files(
        self,
        by_reference_files: typing.Collection[ByReferenceFileDefinition],
        dereference_policy,
        request_url,
        replace=True,
    ):
        from . import tasks

        task_group = []

        for by_reference_file in by_reference_files:
            content_disposition, content_disposition_options = parse_options_header(
                by_reference_file.content_disposition,
            )
            content_type, _ = parse_options_header(by_reference_file.content_type)
            filename = content_disposition_options["filename"]
            object_version = ObjectVersion.create(
                self.bucket, filename, mimetype=content_type
            )
            tags = TagManager(object_version)
            tags.update(
                {
                    ObjectTagKey.FileState: FileState.Pending,
                    ObjectTagKey.OriginalDeposit: "true",
                    ObjectTagKey.Packaging: by_reference_file.packaging,
                    ObjectTagKey.ByReferenceDereference: (
                        "true" if by_reference_file.dereference else "false"
                    ),
                    ObjectTagKey.ByReferenceNotDeleted: "true",
                }
            )
            if by_reference_file.url:
                tags[ObjectTagKey.ByReferenceURL] = by_reference_file.url
            elif by_reference_file.temporary_id:
                tags[ObjectTagKey.ByReferenceTemporaryID] = str(
                    by_reference_file.temporary_id
                )

            if by_reference_file.ttl:
                tags[ObjectTagKey.ByReferenceTTL] = by_reference_file.ttl.isoformat()
            if by_reference_file.content_length:
                tags[ObjectTagKey.ByReferenceContentLength] = str(
                    by_reference_file.content_length
                )

            if dereference_policy(object_version, by_reference_file):
                # Need to refresh so that self.dereference_object can see the tags
                db.session.refresh(object_version)
                task_group.append(self.dereference_object(object_version))

        if task_group:
            # Don't need to group if there's only one task, which avoids a chord
            task = celery.group(task_group) if len(task_group) > 1 else task_group[0]
            if replace:
                task |= tasks.delete_old_objects.s(bucket_id=self.bucket_id)
            task.delay()
        elif replace:
            tasks.delete_old_objects(bucket_id=self.bucket_id)

    def dereference_object(self, object_version: ObjectVersion):
        """Queues a task to dereference an object"""
        from . import tasks

        tags = TagManager(object_version)
        assert tags[ObjectTagKey.Packaging]
        assert tags.get(ObjectTagKey.ByReferenceURL) or tags.get(
            ObjectTagKey.ByReferenceTemporaryID
        )
        assert object_version.is_head

        tags[ObjectTagKey.FileState] = FileState.Pending

        task_signature = tasks.dereference_object.s(
            str(self.id), str(object_version.version_id)
        )
        task_signature |= tasks.unpack_object.si(
            str(self.id), str(object_version.version_id)
        )
        return task_signature

    def unpack_object(self, object_version: ObjectVersion):
        """Queues a task to unpack an object"""
        from . import tasks

        tags = TagManager(object_version)
        assert tags[ObjectTagKey.Packaging]
        assert object_version.is_head

        tags[ObjectTagKey.FileState] = FileState.Unpacking

        return tasks.unpack_object.s(str(self.id), str(object_version.version_id))


class SegmentedUploadRecord(Record):
    pass


pid_resolver = Resolver(
    pid_type="depid",
    object_type="rec",
    getter=functools.partial(SWORDDeposit.get_record, with_deleted=True),
)
