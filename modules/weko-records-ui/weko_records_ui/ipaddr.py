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

"""Utilities for site license check."""

import ipaddress
from flask import request, current_app
from weko_records.api import SiteLicense


def check_site_license_permission():
    """
    Check Site License Permission
    :return: True or False
    """
    http_f = 'HTTP_X_FORWARDED_FOR'
    if request.environ.get(http_f) is None:
        ip_addr = request.environ['REMOTE_ADDR']
    else:
        ip_addr = request.environ[http_f]

    current_app.logger. \
        debug('-->>>>>>>>>>>>>>>>>>>>>>------------------ip address : {ip_adr}'.
              format(ip_adr=ip_addr))

    sl_lst = SiteLicense.get_records()
    if ip_addr:
        for lst in sl_lst:
            addresses = lst.get('addresses')
            for adr in addresses:
                if match_ip_addr(adr, ip_addr):
                    return True
    return False


def match_ip_addr(addr, ip_addr):
    """
    Check Ip Address Range
    :param addr:
    :param ip_addr:
    :return: True or False
    """

    s_ddr = addr.get('start_ip_address')
    f_ddr = addr.get('finish_ip_address')
    ipaddress.ip_address(s_ddr)
    ipaddress.ip_address(f_ddr)

    ip_addr = ip_addr.split('.')
    s_ddr = s_ddr.split('.')
    f_ddr = f_ddr.split('.')

    str0 = ""
    str1 = ""
    str2 = ""

    for i in range(4):
        str0 += '{:0>3}'.format(ip_addr[i])
        str1 += '{:0>3}'.format(s_ddr[i])
        str2 += '{:0>3}'.format(f_ddr[i])

    if (int(str1) <= int(str0)) and (int(str0) <= int(str2)):
        return True

    return False


