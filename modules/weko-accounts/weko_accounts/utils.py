# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Utils for weko-accounts."""
from flask import request


def get_remote_addr():
    """
    Get remote ip address.

    # An 'X-Forwarded-For' header includes a comma separated list of the
    # addresses, the first address being the actual remote address.
    """
    address = request.headers.get('X-Real-IP', None)
    if address is None:
        address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if address is not None:
            address = address.encode('utf-8').split(b',')[0].strip()
    return address


def generate_random_str(length=128):
    """Generate secret key."""
    import string
    import random

    rng = random.SystemRandom()
    return ''.join(
        rng.choice(string.ascii_letters + string.digits)
        for dummy in range(0, length)
    )
