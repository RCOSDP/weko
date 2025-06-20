# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Storage tests."""

from __future__ import absolute_import, print_function

import errno
import os
import io
import shutil
import tempfile
from io import BytesIO

import pytest
import requests
from flask import url_for
from invenio_files_rest.errors import FileSizeError, StorageError, \
    UnexpectedFileSizeError
from invenio_files_rest.limiters import FileSizeLimit
from invenio_files_rest.models import Location
from invenio_files_rest.storage import PyFSFileStorage
from mock import patch
from s3fs import S3File, S3FileSystem
from unittest.mock import MagicMock, patch
from invenio_s3 import S3FSFileStorage, config, s3fs_storage_factory


def test_factory(location, file_instance_mock):
    """Test factory creation."""
    assert isinstance(
        s3fs_storage_factory(fileinstance=file_instance_mock), S3FSFileStorage)

    s3fs = s3fs_storage_factory(fileinstance=file_instance_mock)
    assert s3fs.fileurl == file_instance_mock.uri

    file_instance_mock.uri = None
    s3fs = s3fs_storage_factory(
        fileinstance=file_instance_mock, default_location='s3://test')
    assert s3fs.fileurl == \
        's3://test/de/ad/beef-65bd-4d9b-93e2-ec88cc59aec5/data'

@pytest.mark.parametrize('file_size', (
    1,
    S3FileSystem.default_block_size,
    S3FileSystem.default_block_size + 1,
    S3FileSystem.default_block_size * 2,
    (S3FileSystem.default_block_size * 2) + 1,
))
def test_initialize(location, s3_bucket, s3fs, file_size):
    """Test init of files."""
    uri, size, checksum = s3fs.initialize(size=file_size)

    assert size == file_size
    assert checksum is None

    objs = list(s3_bucket.objects.all())
    assert len(objs) == 1
    assert objs[0].size == size

    uri, size, checksum = s3fs.initialize()
    assert size == 0

    objs = list(s3_bucket.objects.all())
    assert len(objs) == 1
    assert objs[0].size == size


def test_initialize_failcleanup(location, monkeypatch, s3_bucket, s3fs):
    """Test basic cleanup on fail."""
    monkeypatch.setattr(S3File, 'write', lambda x: x, raising=True)
    pytest.raises(Exception, s3fs.initialize, size=100)

    fs, path = s3fs._get_fs()
    assert not fs.exists(path)

    objs = list(s3_bucket.objects.all())
    assert len(objs) == 0


def test_delete(location, s3_bucket, s3fs_testpath, s3fs):
    """Test delete."""
    s3_bucket.upload_fileobj(BytesIO(b'test'), 'path/to/data')

    objs = list(s3_bucket.objects.all())
    assert len(objs) == 1

    assert s3fs.delete()
    fs, path = s3fs._get_fs()
    assert not fs.exists(path)
    assert not fs.exists(s3fs_testpath)

    objs = list(s3_bucket.objects.all())
    assert len(objs) == 0


@pytest.mark.parametrize('data', (
    b'test',
    os.urandom((S3FileSystem.default_block_size)),
    os.urandom((S3FileSystem.default_block_size + 1)),
    os.urandom((S3FileSystem.default_block_size * 2)),
    os.urandom(((S3FileSystem.default_block_size * 2) + 1)),
))
def test_save(location, s3_bucket, s3fs_testpath, s3fs, get_md5, data):
    """Test save."""
    uri, size, checksum = s3fs.save(BytesIO(data))
    assert uri == s3fs_testpath
    assert size == len(data)
    # assert checksum == get_md5(data)

    objs = list(s3_bucket.objects.all())
    assert len(objs) == 1
    # assert objs[0].key == 'path/to/data'
    # assert objs[0].size == size

    fs, path = s3fs._get_fs()
    # assert fs.exists(path)
    # assert fs.exists(s3fs_testpath)
    # assert fs.open(path).read() == data


def test_save_failcleanup(location, s3fs, s3fs_testpath, get_md5):
    """Test basic cleanup on fail."""
    data = b'somedata'

    def fail_callback(total, size):
        # assert exists(s3fs_testpath)
        raise Exception('Something bad happened')

    pytest.raises(
        Exception,
        s3fs.save,
        BytesIO(data),
        chunk_size=4,
        progress_callback=fail_callback)
    fs, path = s3fs._get_fs()
    # assert not fs.exists(path)
    # assert not fs.exists(s3fs_testpath)


def test_save_callback(location, s3fs):
    """Test save progress callback."""
    data = b'somedata'

    counter = dict(size=0)

    def callback(total, size):
        counter['size'] = size

    uri, size, checksum = s3fs.save(BytesIO(data), progress_callback=callback)

    assert counter['size'] == len(data)


def test_save_limits(location, s3fs):
    """Test save limits."""
    data = b'somedata'
    uri, size, checksum = s3fs.save(BytesIO(data), size=len(data))
    assert size == len(data)

    uri, size, checksum = s3fs.save(BytesIO(data), size_limit=len(data))
    assert size == len(data)

    # Size doesn't match
    pytest.raises(
        UnexpectedFileSizeError, s3fs.save, BytesIO(data), size=len(data) - 1)
    pytest.raises(
        UnexpectedFileSizeError, s3fs.save, BytesIO(data), size=len(data) + 1)

    # Exceeds size limits
    pytest.raises(
        FileSizeError,
        s3fs.save,
        BytesIO(data),
        size_limit=FileSizeLimit(len(data) - 1, 'bla'))


@pytest.mark.parametrize('file_size', (
    100,
    S3FileSystem.default_block_size,
    S3FileSystem.default_block_size + 1,
    S3FileSystem.default_block_size * 2,
    (S3FileSystem.default_block_size * 2) + 1,
))
def test_update(location, s3fs, get_md5, file_size):
    """Test update file."""
    s3fs.initialize(size=file_size)

    # Write at the beginning of the file
    s3fs.update(BytesIO(b'cd'), seek=2, size=2)
    s3fs.update(BytesIO(b'ab'), seek=0, size=2)

    fs, path = s3fs._get_fs()
    content = fs.open(path).read()
    assert content[0:4] == b'abcd'
    assert len(content) == file_size

    # Write at the middle of the file
    init_position = int(file_size / 2)
    s3fs.update(BytesIO(b'cd'), seek=(init_position + 2), size=2)
    s3fs.update(BytesIO(b'ab'), seek=init_position, size=2)

    fs, path = s3fs._get_fs()
    content = fs.open(path).read(file_size)
    assert content[init_position:(init_position + 4)] == b'abcd'
    assert len(content) == file_size

    # Write at the end of the file
    init_position = file_size - 4
    s3fs.update(BytesIO(b'cd'), seek=(init_position + 2), size=2)
    s3fs.update(BytesIO(b'ab'), seek=init_position, size=2)

    fs, path = s3fs._get_fs()
    content = fs.open(path).read()
    assert content[init_position:(init_position + 4)] == b'abcd'
    assert len(content) == file_size

    # Assert return parameters from update.
    size, checksum = s3fs.update(BytesIO(b'ef'), seek=4, size=2)
    assert size == 2
    # assert get_md5(b'ef') == checksum


def test_update_fail(location, s3fs, s3fs_testpath, get_md5):
    """Test update of file."""

    def fail_callback(total, size):
        assert exists(s3fs_testpath)
        raise Exception('Something bad happened')

    s3fs.initialize(size=100)
    s3fs.update(BytesIO(b'ab'), seek=0, size=2)
    pytest.raises(
        Exception,
        s3fs.update,
        BytesIO(b'cdef'),
        seek=2,
        size=4,
        chunk_size=2,
        progress_callback=fail_callback,
    )

    # Partial file can be written to disk!
    fs, path = s3fs._get_fs()
    content = fs.open(path).read()
    assert content[0:4] == b'abcd'
    assert content[4:6] != b'ef'


def test_checksum_fail(location, s3fs):
    """Test fixity problems."""

    # Raise an error during checksum calculation
    def callback(total, size):
        raise OSError(errno.EPERM, "Permission")

    s3fs.save(open('LICENSE', 'rb'), size=os.path.getsize('LICENSE'))

    pytest.raises(StorageError, s3fs.checksum, progress_callback=callback)


def test_send_file(base_app, location, s3fs, database):
    """Test send file."""
    default_location = Location.query.filter_by(default=True).first()
    default_location.type = ''
    database.session.commit()

    data = b'sendthis'
    uri, size, checksum = s3fs.save(BytesIO(data))

    def test_send_directly():
        res = s3fs.send_file(
        'test.txt', mimetype='text/plain', checksum=checksum)
        assert res.status_code == 200
        h = res.headers
        assert h['Content-Type'] == 'text/plain; charset=utf-8'
        assert h['Content-Length'] == str(size)
        # assert h['Content-MD5'] == checksum[4:]
        # assert h['ETag'] == '"{0}"'.format(checksum)

        # Content-Type: application/octet-stream
        # ETag: "b234ee4d69f5fce4486a80fdaf4a4263"
        # Last-Modified: Sat, 23 Jan 2016 06:21:04 GMT
        # Cache-Control: max-age=43200, public
        # Expires: Sat, 23 Jan 2016 19:21:04 GMT
        # Date: Sat, 23 Jan 2016 07:21:04 GMT

        res = s3fs.send_file(
            'myfilename.txt', mimetype='text/plain', checksum='crc32:test')
        assert res.status_code == 200
        assert 'Content-MD5' not in dict(res.headers)

        # Test for absence of Content-Disposition header to make sure that
        # it's not present when as_attachment=False
        res = s3fs.send_file('myfilename.txt', mimetype='text/plain',
                                checksum=checksum, as_attachment=False)
        assert res.status_code == 200
        assert 'attachment' not in res.headers['Content-Disposition']

    def test_send_indirectly():
        res = s3fs.send_file(
        'test.txt', mimetype='text/plain', checksum=checksum)
        assert res.status_code == 302
        h = res.headers
        assert 'Location' in h
        assert h['Content-Type'] == 'text/plain; charset=utf-8'
        # FIXME: the lenght is modified somewhere somehow
        # assert h['Content-Length'] == str(size)
        # assert h['Content-MD5'] == checksum[4:]
        # assert h['ETag'] == '"{0}"'.format(checksum)

        res = s3fs.send_file(
            'myfilename.txt', mimetype='text/plain', checksum='crc32:test')
        assert res.status_code == 302
        assert 'Content-MD5' not in dict(res.headers)

    with base_app.test_request_context():

        base_app.config['S3_SEND_FILE_DIRECTLY'] = True
        test_send_directly()

        base_app.config['S3_SEND_FILE_DIRECTLY'] = False
        test_send_indirectly()

        default_location.type = 's3'
        database.session.commit()

        base_app.config['S3_SEND_FILE_DIRECTLY'] = True
        test_send_directly()

        base_app.config['S3_SEND_FILE_DIRECTLY'] = False
        test_send_directly()

        default_location.s3_send_file_directly = False
        database.session.commit()

        base_app.config['S3_SEND_FILE_DIRECTLY'] = True
        test_send_indirectly()

        base_app.config['S3_SEND_FILE_DIRECTLY'] = False
        test_send_indirectly()

        checksum = 'md5:value'
        test_send_indirectly()

        with patch('invenio_s3.storage.redirect_stream') as rs:
            rs.side_effect = Exception
            pytest.raises(StorageError, s3fs.send_file, 'test.txt')

        base_app.config['S3_SEND_FILE_DIRECTLY'] = True
        default_location.s3_send_file_directly = True
        database.session.commit()

def test_send_file_fail(base_app, location, s3fs):
    """Test send file."""
    s3fs.save(BytesIO(b'content'))

    with patch('invenio_s3.storage.redirect_stream') as redirect_stream:
        redirect_stream.side_effect = OSError(errno.EPERM,
                                              "Permission problem")


def test_send_file_xss_prevention(base_app, location, s3fs):
    """Test send file."""
    data = b'<html><body><script>alert("xss");</script></body></html>'
    uri, size, checksum = s3fs.save(BytesIO(data))

    with base_app.test_request_context():
        res = s3fs.send_file(
            'myfilename.html', mimetype='text/html', checksum=checksum)
        # assert res.status_code == 302
        h = res.headers
        # assert 'Location' in h
        # assert h['Content-Type'] == 'text/plain; charset=utf-8'
        # # assert h['Content-Length'] == str(size)
        # assert h['Content-MD5'] == checksum[4:]
        # assert h['ETag'] == '"{0}"'.format(checksum)
        # # XSS prevention
        # assert h['Content-Security-Policy'] == 'default-src \'none\';'
        # assert h['X-Content-Type-Options'] == 'nosniff'
        # assert h['X-Download-Options'] == 'noopen'
        # assert h['X-Permitted-Cross-Domain-Policies'] == 'none'
        # assert h['X-Frame-Options'] == 'deny'
        # assert h['X-XSS-Protection'] == '1; mode=block'
        # assert h['Content-Disposition'] == 'inline'

        # Image
        h = s3fs.send_file('image.png', mimetype='image/png').headers
        assert h['Content-Type'] == 'image/png'
        assert h['Content-Disposition'] == 'inline'

        # README text file
        h = s3fs.send_file('README').headers
        assert h['Content-Type'] == 'text/plain; charset=utf-8'
        assert h['Content-Disposition'] == 'inline'

        # Zip
        h = s3fs.send_file('archive.zip').headers
        assert h['Content-Type'] == 'application/octet-stream'
        assert h['Content-Disposition'] == 'attachment; filename=archive.zip'

        # PDF
        h = s3fs.send_file('doc.pdf').headers
        assert h['Content-Type'] == 'application/octet-stream'
        assert h['Content-Disposition'] == 'attachment; filename=doc.pdf'


def test_non_unicode_filename(base_app, location, s3fs):
    """Test sending the non-unicode filename in the header."""
    data = b'HelloWorld'
    uri, size, checksum = s3fs.save(BytesIO(data))

    with base_app.test_request_context():
        res = s3fs.send_file(
            u'żółć.dat',
            mimetype='application/octet-stream',
            checksum=checksum)
        assert res.status_code == 200
        # assert set(res.headers['Content-Disposition'].split('; ')) == \
        #     set(["attachment", "filename=zoc.dat",
        #          "filename*=UTF-8''%C5%BC%C3%B3%C5%82%C4%87.dat"])

    with base_app.test_request_context():
        res = s3fs.send_file(
            'żółć.txt', mimetype='text/plain', checksum=checksum)
        assert res.status_code == 200
        assert res.headers['Content-Disposition'] == 'inline'

def test_get_fs_with_s3_virtual_host(location, s3fs):
    """Test _get_fs with S3 virtual host URL."""
    location.type = 's3_vh'
    s3fs.fileurl = 'https://bucket_name.s3.us-east-1.amazonaws.com/file_name'

    fs, url = s3fs._get_fs()

    assert isinstance(fs, S3FileSystem)
    assert url == 's3://bucket_name/file_name'


def test_get_fs_with_s3_path_style(location, s3fs):
    """Test _get_fs with S3 path-style URL."""
    location.type = 's3_vh'
    s3fs.fileurl = 'https://s3.us-east-1.amazonaws.com/bucket_name/file_name'

    fs, url = s3fs._get_fs()

    assert isinstance(fs, S3FileSystem)
    assert url == 's3://bucket_name/file_name'


@pytest.mark.parametrize('initial_data, update_data, seek, expected_result', [
    (b'abcdefghij', b'XY', 4, b'abcdXYghij'),  # Update in the middle
    (b'abcdefghij', b'XY', 0, b'XYcdefghij'),  # Update at the beginning
    (b'abcdefghij', b'XY', 8, b'abcdefghXY'),  # Update at the end
    (b'abcdefghij', b'XY', 10, b'abcdefghijXY'),  # Append at the end
])
def test_update(location, s3fs, initial_data, update_data, seek, expected_result):
    """Test the update method."""
    # Initialize the file with initial data
    s3fs.save(BytesIO(initial_data))

    # Perform the update
    bytes_written, checksum = s3fs.update(
        BytesIO(update_data), seek=seek, size=len(update_data)
    )

    # Verify the updated content
    fs, path = s3fs._get_fs()
    content = fs.open(path).read()
    assert content == expected_result
    assert bytes_written == len(update_data)

def test_update_partial_write(location, s3fs):
    """Test update with partial write due to an exception."""
    s3fs.initialize(size=100)

    def fail_callback(total, size):
        raise Exception('Simulated failure during update')

    # Perform the update and expect an exception
    with pytest.raises(Exception):
        s3fs.update(
            BytesIO(b'partialdata'),
            seek=10,
            size=11,
            progress_callback=fail_callback,
        )

    # Verify that the file content is partially updated
    fs, path = s3fs._get_fs()
    content = fs.open(path).read()
    assert content[10:20] == b'partialdat'

def test_copy_s3_to_s3(s3_bucket, location, s3fs):
    """Test copying a file from one S3 location to another."""
    # Save initial data to the source file
    data = b's3_to_s3_test_data'
    s3fs.save(BytesIO(data))

    # Define the destination path
    s3_copy_path = 's3://{}/path/to/copy/data'.format(s3_bucket.name)

    # 修正: S3FSFileStorage のインスタンス生成時に必要な引数を渡す
    s3fs_copy = S3FSFileStorage(
        fileurl=s3_copy_path,
        size=0,
        modified=None,
        clean_dir=True,
        location=location
    )

    # Perform the copy
    s3fs_copy.copy(s3fs)

    # Verify the copied data
    fs, path = s3fs_copy._get_fs()
    with fs.open(path, 'rb') as f:
        copied_data = f.read()
    assert copied_data == data


def test_copy_s3_to_local(s3_bucket, location, s3fs):
    """Test copying a file from S3 to a local file system."""
    # Save initial data to the source file
    data = b's3_to_local_test_data'
    s3fs.save(BytesIO(data))

    # Define the local destination path
    tmppath = tempfile.mkdtemp()
    local_path = os.path.join(tmppath, 'local_copy_data')
    local_storage = PyFSFileStorage(local_path)

    # Perform the copy
    local_storage.copy(s3fs)

    # Verify the copied content
    with open(local_path, 'rb') as f:
        assert f.read() == data

    # Clean up
    shutil.rmtree(tmppath)

def test_copy_fail(location, s3fs):
    """Test copy failure handling."""
    # Simulate a failure during the copy process
    src = MagicMock()
    src.fileurl = 's3://invalid/source/path'

    with pytest.raises(Exception):
        s3fs.copy(src)

def test_remove_file(location, s3fs):
    """Test the remove method for deleting a file."""
    # Mock the file system and path
    fs_mock = MagicMock()
    path = 'path/to/file'

    fs_mock.exists.return_value = True
    fs_mock.rm = MagicMock()
    s3fs.remove(fs_mock, path)
    fs_mock.rm.assert_called_once_with(path)


