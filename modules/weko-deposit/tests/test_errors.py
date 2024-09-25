# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 National Institute of Informatics.
#
# WEKO-Deposit is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Test for weko deposit errors."""

import pytest

from weko_deposit.errors import WekoDepositError, WekoDepositIndexerError, WekoDepositRegistrationError, WekoDepositStorageError

@pytest.mark.parametrize("error_class, msg", [
    (WekoDepositError, "Some error has occurred in weko_deposit."),
    (WekoDepositIndexerError, "Some indexer error has occurred in weko_deposit."),
    (WekoDepositRegistrationError, "Some registration error has occurred in weko_deposit."),
    (WekoDepositStorageError, "Some storage error has occurred in weko_deposit."),
])
def test_weko_deposit_error(error_class , msg):
    # inisialize
    test_ex: WekoDepositError = error_class()
    assert test_ex is not None

    # ex is not None
    origin_ex = ValueError("test_error")
    test_ex = error_class(ex=origin_ex)
    assert test_ex is not None
    assert test_ex.exception == origin_ex
    assert test_ex.msg == msg

    # msg is not None
    test_ex = error_class(msg="test_error")
    assert test_ex is not None
    assert test_ex.msg == "test_error"

