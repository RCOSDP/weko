# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Link Factory weko-deposit."""
# from flask import current_app, request
from invenio_deposit.links import deposit_links_factory


def links_factory(pid, **kwargs):
    """Deposit links factory."""
    links = deposit_links_factory(pid)

    links.update(base_factory(pid, **kwargs))
    return links


def base_factory(pid, **kwargs):
    """Deposit links factory."""
    links = dict()
    links['index'] = "/api/deposits/redirect/" + pid.pid_value
    links['r'] = "/items/index/" + pid.pid_value
    links['iframe_tree'] = "/items/iframe/index/" + pid.pid_value

    return links
