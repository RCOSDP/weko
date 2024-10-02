# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""InvenioRefResolver."""

import urllib.parse

from jsonschema import RefResolutionError, RefResolver


class InvenioRefResolver(RefResolver):
    """Local Invenio JSONSchemas ref resolver class."""

    def resolve_remote(self, uri):
        """Block remote ref resolve."""
        raise RefResolutionError("{uri} not found in local registry.".format(uri=uri))


def urljoin_with_custom_scheme(*args, **kwargs):
    """Patch urljoin call when using local store with custom schemes.

    Allows using custom schemes by extending urllib.parse
    configuration (work-around suggested in
    https://bugs.python.org/issue18828). This patch won't
    be needed once https://github.com/Julian/jsonschema/issues/649
    gets fixed.
    """
    for arg in args:
        if isinstance(arg, str) and "://" in arg:
            scheme = arg.split("://")[0]
            if scheme not in urllib.parse.uses_relative:
                urllib.parse.uses_relative.append(scheme)
            if scheme not in urllib.parse.uses_netloc:
                urllib.parse.uses_netloc.append(scheme)

    return urllib.parse.urljoin(*args, **kwargs)
