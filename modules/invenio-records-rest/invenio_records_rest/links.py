# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Default link factories for PID serialization into URLs.

Link factory can be specified as ``links_factory_impl`` in
:data:`invenio_records_rest.config.RECORDS_REST_ENDPOINTS` configuration.
"""

from flask import request, url_for

from .proxies import current_records_rest


def default_links_factory(pid, record=None, **kwargs):
    """Factory for record links generation.

    :param pid: A Persistent Identifier instance.
    :returns: Dictionary containing a list of useful links for the record.
    """
    endpoint = '.{0}_item'.format(
        current_records_rest.default_endpoint_prefixes[pid.pid_type])
    links = dict(self=url_for(endpoint, pid_value=pid.pid_value,
                 _external=True))
    return links


def default_links_factory_with_additional(additional_links):
    """Generate a links generation factory with the specified additional links.

    :param additional_links: A dict of link names to links to be added to the
           returned object.
    :returns: A link generation factory.
    """
    def factory(pid, **kwargs):
        links = default_links_factory(pid)
        for link in additional_links:
            links[link] = additional_links[link].format(pid=pid,
                                                        scheme=request.scheme,
                                                        host=request.host)
        return links

    return factory
