# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Link for Index Search rest."""

from flask import request, url_for


def default_links_factory(pid, **kwargs):
    """Factory for record links generation.

    :param pid: A Persistent Identifier instance.
    :returns: Dictionary containing a list of useful links for the record.
    """
    links = dict(
        self=url_for(
            'invenio_records_rest.recid_item',
            pid_value=pid.pid_value,
            _external=True))
    return links
