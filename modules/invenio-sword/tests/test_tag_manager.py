import pytest
from invenio_db import db
from invenio_files_rest.models import Bucket
from invenio_files_rest.models import ObjectVersion
from invenio_files_rest.models import ObjectVersionTag

from invenio_sword.enum import ObjectTagKey
from invenio_sword.utils import TagManager


def test_tag_manager_setitem(api, users, location, es):
    value = "http://example.org/"

    with api.test_request_context():
        bucket = Bucket.create()
        object_version = ObjectVersion.create(bucket=bucket, key="hello")
        tags = TagManager(object_version)

        assert (
            ObjectVersionTag.query.filter_by(object_version=object_version).count() == 0
        )
        tags[ObjectTagKey.Packaging] = value

        # It's updated the TagManager
        assert tags[ObjectTagKey.Packaging] == value

        # We've created a tag
        tag = ObjectVersionTag.query.filter_by(object_version=object_version).one()
        assert tag.key == ObjectTagKey.Packaging.value
        assert tag.value == value


def test_tag_manager_delitem(api, users, location, es):
    value = "http://example.org/"

    with api.test_request_context():
        bucket = Bucket.create()
        object_version = ObjectVersion.create(bucket=bucket, key="hello")
        ObjectVersionTag.create(
            object_version=object_version, key=ObjectTagKey.Packaging.value, value=value
        )
        tags = TagManager(object_version)

        assert tags == {ObjectTagKey.Packaging: value}
        assert tags[ObjectTagKey.Packaging] == value

        del tags[ObjectTagKey.Packaging]

        assert tags == {}
        with pytest.raises(KeyError):
            _ = tags[ObjectTagKey.Packaging]

        # We've deleted the database object
        assert (
            ObjectVersionTag.query.filter_by(object_version=object_version).count() == 0
        )


@pytest.mark.parametrize("update_style", ["dict", "kwargs"])
def test_tag_manager_update(api, users, location, es, update_style):
    with api.test_request_context():
        bucket = Bucket.create()
        object_version = ObjectVersion.create(bucket=bucket, key="hello")
        ObjectVersionTag.create(
            object_version=object_version,
            key=ObjectTagKey.Packaging.value,
            value="old-packaging",
        )
        ObjectVersionTag.create(
            object_version=object_version,
            key=ObjectTagKey.MetadataFormat.value,
            value="old-metadata",
        )
        tags = TagManager(object_version)

        assert (
            ObjectVersionTag.query.filter_by(object_version=object_version).count() == 2
        )

        assert tags == {
            ObjectTagKey.Packaging: "old-packaging",
            ObjectTagKey.MetadataFormat: "old-metadata",
        }

        if update_style == "dict":
            tags.update(
                {
                    ObjectTagKey.MetadataFormat: "new-metadata",
                    ObjectTagKey.DerivedFrom: "new-derived-from",
                }
            )
        elif update_style == "kwargs":
            tags.update(
                **{
                    ObjectTagKey.MetadataFormat.value: "new-metadata",
                    ObjectTagKey.DerivedFrom.value: "new-derived-from",
                }
            )

        assert tags == {
            ObjectTagKey.Packaging: "old-packaging",
            ObjectTagKey.MetadataFormat: "new-metadata",
            ObjectTagKey.DerivedFrom: "new-derived-from",
        }

        assert (
            ObjectVersionTag.query.filter_by(object_version=object_version).count() == 3
        )

        db.session.refresh(object_version)
        assert object_version.get_tags() == {
            ObjectTagKey.Packaging.value: "old-packaging",
            ObjectTagKey.MetadataFormat.value: "new-metadata",
            ObjectTagKey.DerivedFrom.value: "new-derived-from",
        }
