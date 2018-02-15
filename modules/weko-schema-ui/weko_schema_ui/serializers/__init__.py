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

"""Record serialization."""

from pkg_resources import resource_filename

from .wekoxml import WekoXMLSerializer

xslt_dublincore_oai = resource_filename(
    'weko_records', 'xslts/toDc_oai_v2.xsl')
xslt_junii2 = resource_filename(
    'weko_records', 'xslts/toJunii2_v2.xsl')
xslt_jpcoar = resource_filename(
    'weko_records', 'xslts/toJpcoar_v1.xsl')

#: Junii2 serializer.
Junii2_v2 = WekoXMLSerializer(xslt_filename=xslt_junii2)

#: Jpcoar serializer.
Jpcoar_v1 = WekoXMLSerializer(xslt_filename=xslt_jpcoar)

#: dublincore serializer.
dublincore_v2  = WekoXMLSerializer(xslt_filename=xslt_dublincore_oai)

# OAI-PMH record serializers.
# ===========================
oaipmh_junii2_v2 = Junii2_v2.serialize_oaipmh
oaipmh_jpcoar_v1 = Jpcoar_v1.serialize_oaipmh
oaipmh_dublincore_v2 = dublincore_v2.serialize_oaipmh

WekoCommonSchema = WekoXMLSerializer()
