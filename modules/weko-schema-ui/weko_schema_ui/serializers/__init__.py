# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 National Institute of Informatics.
#
# WEKO3 is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record serialization."""

from pkg_resources import resource_filename

from .WekoBibTexSerializer import WekoBibTexSerializer
from .wekoxml import WekoXMLSerializer

xslt_dublincore_oai = resource_filename(
    'weko_records', 'xslts/toDc_oai_v2.xsl')
xslt_junii2 = resource_filename(
    'weko_records', 'xslts/toJunii2_v2.xsl')
xslt_jpcoar = resource_filename(
    'weko_records', 'xslts/toJpcoar_v1.xsl')
xslt_ddi = resource_filename(
    'weko_records', 'xslts/toDdi_v1.xsl')

#: Junii2 serializer.
Junii2_v2 = WekoXMLSerializer(xslt_filename=xslt_junii2)

#: Jpcoar serializer.
Jpcoar_v1 = WekoXMLSerializer(xslt_filename=xslt_jpcoar)

#: dublincore serializer.
dublincore_v2 = WekoXMLSerializer(xslt_filename=xslt_dublincore_oai)

#: DDI serializer.
ddi_v1 = WekoXMLSerializer(xslt_filename=xslt_dublincore_oai)

# OAI-PMH record serializers.
# ===========================
oaipmh_junii2_v2 = Junii2_v2.serialize_oaipmh
oaipmh_jpcoar_v1 = Jpcoar_v1.serialize_oaipmh
oaipmh_dublincore_v2 = dublincore_v2.serialize_oaipmh
oaipmh_ddi_v1 = ddi_v1.serialize_oaipmh

WekoCommonSchema = WekoXMLSerializer()

BibTexSerializer = WekoBibTexSerializer()
