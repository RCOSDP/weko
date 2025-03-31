# -*- coding: utf-8 -*-
#
# Copyright (C) 2018, 2019, 2020 Esteban J. G. Gabancho.
#
# Invenio-S3 is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Storage tests."""

from __future__ import absolute_import, print_function

import errno
import os
import shutil
import tempfile
from io import BytesIO

import pytest
from invenio_files_rest.errors import FileSizeError, StorageError, \
    UnexpectedFileSizeError
from invenio_files_rest.limiters import FileSizeLimit
from invenio_files_rest.storage import PyFSFileStorage
from mock import patch
from s3fs import S3File, S3FileSystem

from invenio_s3 import S3FSFileStorage, s3fs_storage_factory


def test_factory(file_instance_mock):
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


def test_non_s3_path(tmpdir):
    non_s3_path = os.path.join(tmpdir.dirname, 'test.txt')
    s3fs = S3FSFileStorage(non_s3_path)
    fs, path = s3fs._get_fs()
    assert not isinstance(fs, S3FileSystem)


@pytest.mark.parametrize('file_size', (
    1,
    S3FileSystem.default_block_size,
    S3FileSystem.default_block_size + 1,
    S3FileSystem.default_block_size * 2,
    (S3FileSystem.default_block_size * 2) + 1,
))
def test_initialize(s3_bucket, s3fs, file_size):
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


def test_initialize_failcleanup(monkeypatch, s3_bucket, s3fs):
    """Test basic cleanup on fail."""
    monkeypatch.setattr(S3File, 'write', lambda x: x, raising=True)
    pytest.raises(Exception, s3fs.initialize, size=100)

    fs, path = s3fs._get_fs()
    assert not fs.exists(path)

    objs = list(s3_bucket.objects.all())
    assert len(objs) == 0


def test_delete(s3_bucket, s3fs_testpath, s3fs):
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
def test_save(s3_bucket, s3fs_testpath, s3fs, get_md5, data):
    """Test save."""
    uri, size, checksum = s3fs.save(BytesIO(data))
    assert uri == s3fs_testpath
    assert size == len(data)
    assert checksum == get_md5(data)

    objs = list(s3_bucket.objects.all())
    assert len(objs) == 1
    assert objs[0].key == 'path/to/data'
    assert objs[0].size == size

    fs, path = s3fs._get_fs()
    assert fs.exists(path)
    assert fs.exists(s3fs_testpath)
    assert fs.open(path).read() == data


def test_save_failcleanup(s3fs, s3fs_testpath, get_md5):
    """Test basic cleanup on fail."""
    data = b'somedata'

    def fail_callback(total, size):
        assert fs.exists(s3fs_testpath)
        raise Exception('Something bad happened')

    pytest.raises(
        Exception,
        s3fs.save,
        BytesIO(data),
        chunk_size=4,
        progress_callback=fail_callback)
    fs, path = s3fs._get_fs()
    assert not fs.exists(path)
    assert not fs.exists(s3fs_testpath)


def test_save_callback(s3fs):
    """Test save progress callback."""
    data = b'somedata'

    counter = dict(size=0)

    def callback(total, size):
        counter['size'] = size

    uri, size, checksum = s3fs.save(BytesIO(data), progress_callback=callback)

    assert counter['size'] == len(data)


def test_save_limits(s3fs):
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
def test_update(s3fs, get_md5, file_size):
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
    assert get_md5(b'ef') == checksum


def test_update_fail(s3fs, s3fs_testpath, get_md5):
    """Test update of file."""
    def fail_callback(total, size):
        assert fs.exists(s3fs_testpath)
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


def test_checksum(s3fs, get_md5):
    """Test fixity."""
    # Compute checksum of license file
    with open('LICENSE', 'rb') as fp:
        data = fp.read()
        checksum = get_md5(data)

    counter = dict(size=0)

    def callback(total, size):
        counter['size'] = size

    # Now do it with storage interface
    with open('LICENSE', 'rb') as fp:
        uri, size, save_checksum = s3fs.save(
            fp, size=os.path.getsize('LICENSE'))
    assert checksum == save_checksum
    assert checksum == s3fs.checksum(chunk_size=2, progress_callback=callback)
    assert counter['size'] == size
    assert counter['size'] == os.path.getsize('LICENSE')

    # No size provided, means progress callback isn't called
    counter['size'] = 0
    s = S3FSFileStorage(s3fs.fileurl)
    assert checksum == s.checksum(chunk_size=2, progress_callback=callback)
    assert counter['size'] == 0


def test_checksum_fail(s3fs):
    """Test fixity problems."""

    # Raise an error during checksum calculation
    def callback(total, size):
        raise OSError(errno.EPERM, "Permission")

    s3fs.save(open('LICENSE', 'rb'), size=os.path.getsize('LICENSE'))

    pytest.raises(StorageError, s3fs.checksum, progress_callback=callback)


def test_copy(s3_bucket, s3fs):
    """Test copy file."""
    data = b'test'
    s3fs.save(BytesIO(data))

    s3_copy_path = 's3://{}/path/to/copy/data'.format(s3_bucket.name)
    s3fs_copy = S3FSFileStorage(s3_copy_path)
    s3fs_copy.copy(s3fs)

    assert s3fs_copy.open().read() == data

    tmppath = tempfile.mkdtemp()

    s = PyFSFileStorage(os.path.join(tmppath, 'anotherpath/data'))
    data = b'othertest'
    s.save(BytesIO(data))
    s3fs_copy.copy(s)
    assert s3fs_copy.open().read() == data

    shutil.rmtree(tmppath)


def test_send_file(base_app, s3fs):
    """Test send file."""
    data = b'sendthis'
    uri, size, checksum = s3fs.save(BytesIO(data))

    with base_app.test_request_context():
        res = s3fs.send_file(
            'test.txt', mimetype='text/plain')
        assert res.status_code == 302
        h = res.headers
        assert 'Location' in h

        res = s3fs.send_file(
            'myfilename.txt', mimetype='text/plain')
        assert res.status_code == 302


def test_send_file_fail(base_app, s3fs):
    """Test send file."""
    s3fs.save(BytesIO(b'content'))

    with patch('invenio_s3.storage.redirect_stream') as redirect_stream:
        redirect_stream.side_effect = OSError(errno.EPERM,
                                              "Permission problem")
        with base_app.test_request_context():
            pytest.raises(StorageError, s3fs.send_file, 'test.txt')


def test_non_unicode_filename(base_app, s3fs):
    """Test sending the non-unicode filename in the header."""
    data = b'HelloWorld'
    uri, size, checksum = s3fs.save(BytesIO(data))

    with base_app.test_request_context():
        res = s3fs.send_file(
            u'żółć.dat',
            mimetype='application/octet-stream',
            checksum=checksum)
        assert res.status_code == 302
        assert set(res.headers['Content-Disposition'].split('; ')) == \
            set(["attachment", "filename=zoc.dat",
                 "filename*=UTF-8''%C5%BC%C3%B3%C5%82%C4%87.dat"])

    with base_app.test_request_context():
        res = s3fs.send_file(
            'żółć.txt', mimetype='text/plain', checksum=checksum)
        assert res.status_code == 302
        assert res.headers['Content-Disposition'] == 'inline'


def test_block_size(appctx, s3_bucket, s3fs_testpath, s3fs, get_md5):
    """Test block size update on the S3FS client."""
    # Set file size to 4 times the default block size
    data = b'a' * appctx.config['S3_DEFAULT_BLOCK_SIZE'] * 4
    # Set the number of maximum parts to two
    appctx.config['S3_MAXIMUM_NUMBER_OF_PARTS'] = 2
    uri, size, checksum = s3fs.save(BytesIO(data),
                                    size=len(data))
    # The block size should be 2 times the default block size
    assert s3fs.block_size == appctx.config['S3_DEFAULT_BLOCK_SIZE'] * 2
    assert uri == s3fs_testpath
    assert size == len(data)
    assert checksum == get_md5(data)
