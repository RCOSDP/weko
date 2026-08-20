# -*- coding: utf-8 -*-
#
# This file is part of WEKO3.
# Copyright (C) 2017 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# WEKO3 is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with WEKO3; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.

"""Resolve the registration agency an item's DOI belongs to."""

from flask import current_app
from werkzeug.utils import import_string

from .errors import AgencyNotSupportedError


def get_agency(doi_select):
    """Return the agency handling this identifier grant.

    The agency is looked up by ``doi_select`` and not by the DOI type stored
    in the metadata, because ``saving_doi_pidstore()`` writes ``JaLC`` for
    both JaLC (1) and NDL JaLC (4).

    :param doi_select: identifier grant value, ``1`` to ``4``
    :return: a :class:`~weko_workflow.doi.base.DoiRegistrationAgency`
    :raises AgencyNotSupportedError: when no agency is configured for it
    """
    agencies = current_app.config.get('WEKO_DOI_AGENCIES') or {}
    path = agencies.get(str(doi_select))
    if not path:
        raise AgencyNotSupportedError(
            'No DOI registration agency for doi_select={0}.'.format(
                doi_select))
    return import_string(path)()


def is_supported(doi_select):
    """Tell whether an agency is configured for this identifier grant.

    :param doi_select: identifier grant value
    :return: True when :func:`get_agency` can resolve it
    """
    agencies = current_app.config.get('WEKO_DOI_AGENCIES') or {}
    return bool(agencies.get(str(doi_select)))
