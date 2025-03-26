# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import pytest
from io import BytesIO
from hashlib import sha256,sha512
from zipfile import ZipFile
from unittest.mock import MagicMock, patch
from weko_swordserver.utils import (
    check_import_file_format,
    is_valid_file_hash
)
from .helpers import json_data
from weko_swordserver.errors import ErrorType, WekoSwordserverException


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# def check_import_file_format(file, packaging):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_check_import_file_format -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_check_import_file_format(app):
    # No 1
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/sword.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SWORDBagIt') == 'JSON'


    # No 2
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/invalid.json', '{}')
    file_content.seek(0)
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, 'SWORDBagIt')
    assert e.value.errorType == ErrorType.MetadataFormatNotAcceptable
    assert e.value.message == "SWORDBagIt requires metadate/sword.json."

    # No 3
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('ro-crate-metadata.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'JSON'

    # No 4
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('invalid.json', '{}')
    file_content.seek(0)
    assert check_import_file_format(file_content, 'SimpleZip') == 'OTHERS'

    # No 5
    file_content = BytesIO()
    with ZipFile(file_content, 'w') as zip_file:
        zip_file.writestr('metadata/sword.json', '{}')
    file_content.seek(0)
    packaging = 'InvalidPackaging'
    with pytest.raises(WekoSwordserverException) as e:
        check_import_file_format(file_content, packaging)
    assert e.value.errorType == ErrorType.PackagingFormatNotAcceptable
    assert e.value.message == f"Not accept packaging format: {packaging}"



# def is_valid_file_hash(expected_hash, file):
# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_utils.py::test_is_valid_file_hash -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_is_valid_file_hash():
    # No 1
    file_content = BytesIO(b'This is a test file content')
    file_content.seek(0)
    expected_hash = sha256(b'This is a test file content').hexdigest()
    result = is_valid_file_hash(expected_hash,file_content)
    assert result is True

    # No 2
    file_content.seek(0)
    invalid_hash = sha256(b'Invalid content').hexdigest()
    result = is_valid_file_hash(invalid_hash ,file_content)
    assert result is False

    # No 3:
    file_content = BytesIO(b'This is a test file content')
    file_content.seek(0)
    expected_hash = sha512(b'This is a test file content').hexdigest()
    result = is_valid_file_hash(expected_hash,file_content )
    assert result is False

    # No 4:
    file_content = BytesIO(b'This is a test file content')
    file_content.seek(0)
    expected_hash = sha256(b'This is a test file content')
    result = is_valid_file_hash(expected_hash,file_content )
    assert result is False
