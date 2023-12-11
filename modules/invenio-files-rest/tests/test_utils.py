# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

from invenio_files_rest.utils import delete_file_instance, get_hash


def test_delete_file_instance(multipart, objects):
    assert delete_file_instance(multipart.file_id)
    assert not delete_file_instance(objects[0].file_id)
    
def test_get_hash():
    assert get_hash(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"