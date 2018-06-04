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

"""Utilities for convert response json."""

from . import config


def get_response_json(result_list, n_lst):
    """
     Get a response json
    :param result_list:
    :param n_lst:
    :return: result
    """

    result = {}
    if isinstance(result_list, list):
        newlst = []
        for rlst in result_list:
            adr_lst = rlst.get('addresses')
            if isinstance(adr_lst, list):
                for alst in adr_lst:
                    alst['start_ip_address'] = alst['start_ip_address'].split('.')
                    alst['finish_ip_address'] = alst['finish_ip_address'].split('.')
            newlst.append(rlst.dumps())
        result.update(dict(site_license=newlst))
        del result_list

    if n_lst:
        item_type = {}
        allow = []
        deny = []
        for lst in n_lst:
            tmp = []
            tmp.append({'id': str(lst.id), 'name': lst.name})
            if lst.has_site_license:
                allow.extend(tmp)
            else:
                deny.extend(tmp)

        item_type['deny'] = deny or []
        item_type['allow'] = allow or []
        result['item_type'] = item_type

    return result


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.LOGO_ALLOWED_EXTENSIONS
