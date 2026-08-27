
# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Storage module tests."""

from __future__ import absolute_import, print_function

import errno
import os
from os.path import dirname, exists, getsize, join

import pytest
from fs.errors import DirectoryNotEmptyError, ResourceNotFoundError
from unittest.mock import patch
from six import BytesIO
from sqlalchemy import event

from invenio_files_rest.errors import FileSizeError, StorageError, \
    UnexpectedFileSizeError
from invenio_files_rest.limiters import FileSizeLimit
from invenio_files_rest.models import Location
from invenio_files_rest.storage import FileStorage, PyFSFileStorage, \
    pyfs_storage_factory


def test_storage_interface():
    """Test storage interface."""
    s = FileStorage()
    pytest.raises(NotImplementedError, s.open)
    pytest.raises(NotImplementedError, s.initialize)
    pytest.raises(NotImplementedError, s.delete)
    pytest.raises(NotImplementedError, s.save, None)
    pytest.raises(NotImplementedError, s.update, None)
    pytest.raises(NotImplementedError, s.checksum)


def test_pyfs_initialize(pyfs, pyfs_testpath):
    """Test init of files."""
    # Create file object.
    assert not exists(pyfs_testpath)
    uri, size, checksum = pyfs.initialize(size=100)

    assert size == 100
    assert checksum is None
    assert os.stat(pyfs_testpath).st_size == size

    uri, size, checksum = pyfs.initialize()
    assert size == 0
    assert size == os.stat(pyfs_testpath).st_size


def test_pyfs_delete(app, db, dummy_location):
    """Test init of files."""
    testurl = join(dummy_location.uri, 'subpath/data')
    s = PyFSFileStorage(testurl)
    s.initialize(size=100)
    assert exists(testurl)

    s.delete()
    assert not exists(testurl)

    s = PyFSFileStorage(join(dummy_location.uri, 'anotherpath/data'))
    pytest.raises(ResourceNotFoundError, s.delete)


def test_pyfs_delete_fail(pyfs, pyfs_testpath):
    """Test init of files."""
    pyfs.save(BytesIO(b'somedata'))
    os.rename(pyfs_testpath, join(dirname(pyfs_testpath), 'newname'))
    pytest.raises(DirectoryNotEmptyError, pyfs.delete)


def test_pyfs_save(pyfs, pyfs_testpath, get_sha256):
    """Test basic save operation."""
    data = b'somedata'
    uri, size, checksum = pyfs.save(BytesIO(data))

    assert uri == pyfs_testpath
    assert size == len(data)
    assert checksum == get_sha256(data)
    assert exists(pyfs_testpath)
    assert open(pyfs_testpath, 'rb').read() == data


def test_pyfs_save_failcleanup(pyfs, pyfs_testpath):
    """Test basic save operation."""
    data = b'somedata'

    def fail_callback(total, size):
        assert exists(pyfs_testpath)
        raise Exception('Something bad happened')

    pytest.raises(
        Exception,
        pyfs.save,
        BytesIO(data), chunk_size=4, progress_callback=fail_callback
    )
    assert not exists(pyfs_testpath)
    assert not exists(dirname(pyfs_testpath))


def test_pyfs_save_callback(pyfs):
    """Test progress callback."""
    data = b'somedata'

    counter = dict(size=0)

    def callback(total, size):
        counter['size'] = size

    uri, size, checksum = pyfs.save(
        BytesIO(data), progress_callback=callback)

    assert counter['size'] == len(data)


def test_pyfs_save_limits(pyfs):
    """Test progress callback."""
    data = b'somedata'
    uri, size, checksum = pyfs.save(BytesIO(data), size=len(data))
    assert size == len(data)

    uri, size, checksum = pyfs.save(BytesIO(data), size_limit=len(data))
    assert size == len(data)

    # Size doesn't match
    pytest.raises(
        UnexpectedFileSizeError, pyfs.save, BytesIO(data), size=len(data) - 1)
    pytest.raises(
        UnexpectedFileSizeError, pyfs.save, BytesIO(data), size=len(data) + 1)

    # Exceeds size limits
    pytest.raises(
        FileSizeError, pyfs.save, BytesIO(data),
        size_limit=FileSizeLimit(len(data) - 1, 'bla'))


def test_pyfs_update(pyfs, pyfs_testpath, get_sha256):
    """Test update of file."""
    pyfs.initialize(size=100)
    pyfs.update(BytesIO(b'cd'), seek=2, size=2)
    pyfs.update(BytesIO(b'ab'), seek=0, size=2)

    with open(pyfs_testpath) as fp:
        content = fp.read()
    assert content[0:4] == 'abcd'
    assert len(content) == 100

    # Assert return parameters from update.
    size, checksum = pyfs.update(BytesIO(b'ef'), seek=4, size=2)
    assert size == 2
    assert get_sha256(b'ef') == checksum


def test_pyfs_update_fail(pyfs, pyfs_testpath):
    """Test update of file."""
    def fail_callback(total, size):
        assert exists(pyfs_testpath)
        raise Exception('Something bad happened')

    pyfs.initialize(size=100)
    pyfs.update(BytesIO(b'ab'), seek=0, size=2)
    pytest.raises(
        Exception,
        pyfs.update,
        BytesIO(b'cdef'),
        seek=2,
        size=4,
        chunk_size=2,
        progress_callback=fail_callback,
    )

    # Partial file can be written to disk!
    with open(pyfs_testpath) as fp:
        content = fp.read()
    assert content[0:4] == 'abcd'
    assert content[4:6] != 'ef'


def test_pyfs_checksum(get_sha256):
    """Test fixity."""
    # Compute checksum of license file
    with open('LICENSE', 'rb') as fp:
        data = fp.read()
        checksum = get_sha256(data)

    counter = dict(size=0)

    def callback(total, size):
        counter['size'] = size

    # Now do it with storage interface
    s = PyFSFileStorage('LICENSE', size=getsize('LICENSE'))
    assert checksum == s.checksum(chunk_size=2, progress_callback=callback)
    assert counter['size'] == getsize('LICENSE')

    # No size provided, means progress callback isn't called
    counter['size'] = 0
    s = PyFSFileStorage('LICENSE')
    assert checksum == s.checksum(chunk_size=2, progress_callback=callback)
    assert counter['size'] == 0


def test_pyfs_checksum_fail():
    """Test fixity problems."""
    # Raise an error during checksum calculation
    def callback(total, size):
        raise OSError(errno.EPERM, "Permission")

    s = PyFSFileStorage('LICENSE', size=getsize('LICENSE'))

    pytest.raises(StorageError, s.checksum, progress_callback=callback)


def test_pyfs_send_file(app, pyfs):
    """Test send file."""
    data = b'sendthis'
    uri, size, checksum = pyfs.save(BytesIO(data))

    with app.test_request_context():
        res = pyfs.send_file(
            'myfilename.txt', mimetype='text/plain', checksum=checksum)
        assert res.status_code == 200
        h = res.headers
        assert h['Content-Type'] == 'text/plain; charset=utf-8'
        assert h['Content-Length'] == str(size)
#        assert h['Content-MD5'] == checksum[4:]
        assert h['ETag'] == '"{0}"'.format(checksum)

        # Content-Type: application/octet-stream
        # ETag: "b234ee4d69f5fce4486a80fdaf4a4263"
        # Last-Modified: Sat, 23 Jan 2016 06:21:04 GMT
        # Cache-Control: max-age=43200, public
        # Expires: Sat, 23 Jan 2016 19:21:04 GMT
        # Date: Sat, 23 Jan 2016 07:21:04 GMT

        res = pyfs.send_file(
            'myfilename.txt', mimetype='text/plain', checksum='md5:test')
        assert res.status_code == 200
        assert 'Content-MD5' in dict(res.headers)

        # Test for absence of Content-Disposition header to make sure that
        # it's not present when as_attachment=False
        res = pyfs.send_file('myfilename.txt', mimetype='text/plain',
                             checksum=checksum, as_attachment=False)
        assert res.status_code == 200
        assert 'attachment' not in res.headers['Content-Disposition']


def test_pyfs_send_file_for_download(app, pyfs):
    """Test send file."""
    data = b'sendthis'
    uri, size, checksum = pyfs.save(BytesIO(data))

    with app.test_request_context():
        # Test for presence of Content-Disposition header to make sure that
        # it's present when as_attachment=True
        res = pyfs.send_file('myfilename.txt', mimetype='text/plain',
                             checksum=checksum, as_attachment=True)
        assert res.status_code == 200
        assert (res.headers['Content-Disposition'] ==
                'attachment; filename=myfilename.txt')


def test_pyfs_send_file_xss_prevention(app, pyfs):
    """Test send file."""
    data = b'<html><body><script>alert("xss");</script></body></html>'
    uri, size, checksum = pyfs.save(BytesIO(data))

    with app.test_request_context():
        res = pyfs.send_file(
            'myfilename.html', mimetype='text/html', checksum=checksum)
        assert res.status_code == 200
        h = res.headers
        assert h['Content-Type'] == 'text/plain; charset=utf-8'
        assert h['Content-Length'] == str(size)
#        assert h['Content-MD5'] == checksum[4:]
        assert h['ETag'] == '"{0}"'.format(checksum)
        # XSS prevention
        assert h['Content-Security-Policy'] == 'default-src \'none\';'
        assert h['X-Content-Type-Options'] == 'nosniff'
        assert h['X-Download-Options'] == 'noopen'
        assert h['X-Permitted-Cross-Domain-Policies'] == 'none'
        assert h['X-Frame-Options'] == 'deny'
        assert h['X-XSS-Protection'] == '1; mode=block'
        assert h['Content-Disposition'] == 'inline'

        # Image
        h = pyfs.send_file('image.png', mimetype='image/png').headers
        assert h['Content-Type'] == 'image/png'
        assert h['Content-Disposition'] == 'inline'

        # README text file
        h = pyfs.send_file('README').headers
        assert h['Content-Type'] == 'text/plain; charset=utf-8'
        assert h['Content-Disposition'] == 'inline'

        # Zip
        h = pyfs.send_file('archive.zip').headers
        assert h['Content-Type'] == 'application/octet-stream'
        assert h['Content-Disposition'] == 'attachment; filename=archive.zip'

        # PDF
        h = pyfs.send_file('doc.pdf').headers
        assert h['Content-Type'] == 'application/octet-stream'
        assert h['Content-Disposition'] == 'attachment; filename=doc.pdf'


def test_pyfs_send_file_fail(app, pyfs):
    """Test send file."""
    pyfs.save(BytesIO(b'content'))

    with patch('invenio_files_rest.storage.base.send_stream') as send_stream:
        send_stream.side_effect = OSError(errno.EPERM, "Permission problem")
        with app.test_request_context():
            pytest.raises(StorageError, pyfs.send_file, 'test.txt')


def test_pyfs_copy(pyfs, dummy_location):
    """Test send file."""
    s = PyFSFileStorage(join(dummy_location.uri, 'anotherpath/data'))
    s.save(BytesIO(b'otherdata'))

    pyfs.copy(s)
    fp = pyfs.open()
    assert fp.read() == b'otherdata'


def test_non_unicode_filename(app, pyfs):
    """Test sending the non-unicode filename in the header."""
    data = b'HelloWorld'
    uri, size, checksum = pyfs.save(BytesIO(data))

    with app.test_request_context():
        res = pyfs.send_file(
            u'żółć.dat', mimetype='application/octet-stream',
            checksum=checksum)
        assert res.status_code == 200
        assert set(res.headers['Content-Disposition'].split('; ')) == \
            set(["attachment", "filename=zoc.dat",
                 "filename*=UTF-8''%C5%BC%C3%B3%C5%82%C4%87.dat"])

    with app.test_request_context():
        res = pyfs.send_file(
            'żółć.txt', mimetype='text/plain', checksum=checksum)
        assert res.status_code == 200
        assert res.headers['Content-Disposition'] == 'inline'


def _add_location(db, name, uri, default=False):
    """Add a location row and commit it.

    ``Location.name`` is validated against ``^[a-z][a-z0-9-]+$``
    (``invenio_files_rest/models.py``), so names must be two characters or
    longer, start with a lower-case letter and contain only lower-case
    alphanumerics and dashes.
    """
    loc = Location(name=name, uri=uri, default=default)
    db.session.add(loc)
    db.session.commit()
    return loc


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_prefix_match -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_prefix_match(app, db, dummy_location):
    """Test that a location whose URI prefixes the fileurl is selected."""
    _add_location(db, 'loc-a', 's3://bucket-a')

    storage = pyfs_storage_factory(fileurl='s3://bucket-a/ab/cd/ef/data', size=1)

    assert storage.location is not None
    assert storage.location.name == 'loc-a'


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_longest_prefix_wins -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_longest_prefix_wins(app, db, dummy_location):
    """Test that the longest matching location URI wins.

    The shorter URI is inserted first on purpose: without the
    ``ORDER BY length(uri) DESC`` clause PostgreSQL returns rows in physical
    (insert) order, so dropping the ordering makes this test fail.
    """
    _add_location(db, 'loc-a', 's3://bucket-a')
    _add_location(db, 'loc-b', 's3://bucket-a/sub')

    storage = pyfs_storage_factory(fileurl='s3://bucket-a/sub/ab/cd/data', size=1)

    assert storage.location is not None
    assert storage.location.name == 'loc-b'


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_no_partial_match -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_no_partial_match(app, db, dummy_location):
    """Test that a location URI matches only at the start of the fileurl.

    ``/mnt/other`` appears in the fileurl but not as a prefix, so it must not
    be selected and the default location must be used instead.
    """
    _add_location(db, 'loc-x', '/mnt/other')

    storage = pyfs_storage_factory(fileurl='/mnt/data/backup/mnt/other/ab/data', size=1)

    assert storage.location is not None
    assert storage.location.name != 'loc-x'
    assert storage.location.id == dummy_location.id


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_uri_underscore_not_wildcard -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_uri_underscore_not_wildcard(
        app, db, dummy_location):
    """Test that an underscore in a location URI is not a LIKE wildcard."""
    _add_location(db, 'loc-us', 's3://weko_bucket')

    storage = pyfs_storage_factory(fileurl='s3://wekoxbucket/ab/data', size=1)

    assert storage.location is not None
    assert storage.location.name != 'loc-us'
    assert storage.location.id == dummy_location.id


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_default_fallback -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_default_fallback(app, db, dummy_location):
    """Test the fallback to the default location when nothing matches."""
    storage = pyfs_storage_factory(fileurl='s3://nowhere/ab/data', size=1)

    assert storage.location is not None
    assert storage.location.id == dummy_location.id


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_no_location_logs_warning -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_no_location_logs_warning(app, db, mocker):
    """Test that a warning is logged when no location can be resolved.

    No location fixture is requested on purpose: with a default location
    present the fallback would succeed and no warning would be emitted.
    """
    warning_mock = mocker.patch.object(app.logger, 'warning')

    storage = pyfs_storage_factory(fileurl='s3://nowhere/ab/data', size=1)

    assert storage.location is None
    warning_mock.assert_called_once()
    assert 's3://nowhere/ab/data' in warning_mock.call_args[0][0]


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_default_location_match -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_default_location_match(
        app, db, dummy_location, mocker):
    """Test that an explicit default_location takes precedence.

    ``loc-a`` prefixes the fileurl and would win the prefix lookup, so it also
    proves that the prefix lookup is not executed once the URI of
    ``default_location`` has been resolved.
    """
    _add_location(db, 'loc-a', 's3://bucket-a')

    fileinstance = mocker.MagicMock()
    fileinstance.size = 1
    fileinstance.updated = None
    fileinstance.uri = 's3://bucket-a/ab/data'

    storage = pyfs_storage_factory(
        fileinstance=fileinstance, default_location=dummy_location.uri)

    assert storage.location is not None
    assert storage.location.name != 'loc-a'
    assert storage.location.id == dummy_location.id


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_skips_query_when_no_default_location -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_skips_query_when_no_default_location(
        app, db, mocker):
    """Test that no query is issued when default_location is not given.

    ``loc-none`` has the literal URI ``'None'``: without the guard the lookup
    would compare against ``str(None)`` and select it.
    """
    _add_location(db, 'loc-a', 's3://bucket-a')
    _add_location(db, 'loc-none', 'None')

    fileinstance = mocker.MagicMock()
    fileinstance.size = 1
    fileinstance.updated = None
    fileinstance.uri = 's3://bucket-a/ab/data'

    statements = []

    def _record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, 'before_cursor_execute', _record)
    try:
        storage = pyfs_storage_factory(fileinstance=fileinstance)
    finally:
        event.remove(db.engine, 'before_cursor_execute', _record)

    assert storage.location is not None
    assert storage.location.name != 'loc-none'
    assert storage.location.name == 'loc-a'
    assert len(statements) == 1
    assert 'substr' in statements[0].lower()


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_no_full_scan -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_no_full_scan(app, db, dummy_location, mocker):
    """Test that the whole location table is never loaded into memory."""
    _add_location(db, 'loc-a', 's3://bucket-a')
    mock_all = mocker.patch('invenio_files_rest.models.Location.all')

    storage = pyfs_storage_factory(fileurl='s3://bucket-a/ab/data', size=1)

    mock_all.assert_not_called()
    assert storage.location is not None
    assert storage.location.name == 'loc-a'


# .tox/c1/bin/pytest --cov=invenio_files_rest tests/test_storage.py::test_pyfs_storage_factory_passes_args_to_filestorage_class -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-files-rest/.tox/c1/tmp
def test_pyfs_storage_factory_passes_args_to_filestorage_class(app, db, dummy_location, mocker):
    """Test the arguments handed over to the file storage class."""
    loc_a = _add_location(db, 'loc-a', 's3://bucket-a')
    fake_class = mocker.MagicMock()

    storage = pyfs_storage_factory(fileurl='s3://bucket-a/ab/data', size=1, filestorage_class=fake_class)

    fake_class.assert_called_once_with('s3://bucket-a/ab/data', size=1, modified=None, clean_dir=True, location=loc_a)
    assert fake_class.call_args[1]['location'].name == 'loc-a'
    assert storage is fake_class.return_value
