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

"""Configuration for weko-itemtypes-ui."""

from flask_babelex import lazy_gettext as _

# TODO: Delete if not being used
WEKO_ITEMTYPES_UI_BASE_TEMPLATE = 'weko_itemtypes_ui/base.html'
"""Default base template for the item type page."""

WEKO_ITEMTYPES_UI_ADMIN_REGISTER_TEMPLATE = \
    'weko_itemtypes_ui/admin/create_itemtype.html'
"""Register template for the item type page."""

WEKO_ITEMTYPES_UI_ADMIN_CREATE_PROPERTY = \
    'weko_itemtypes_ui/admin/create_property.html'
"""Create property template."""

WEKO_ITEMTYPES_UI_ADMIN_MAPPING_TEMPLATE = \
    'weko_itemtypes_ui/admin/create_mapping.html'
"""Mapping template for the item type page."""

WEKO_ITEMTYPES_UI_ADMIN_ERROR_TEMPLATE = 'weko_itemtypes_ui/admin/error.html'
"""Error template for the item type page."""

WEKO_ITEMTYPES_UI_SHOW_DEFAULT_PROPERTIES = True
"""Set to show or hide default properties on the item type page."""

WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES = {
    '1': {'name': _('Text Field'), 'value': 'text'},
    '2': {'name': _('Text Area'), 'value': 'textarea'},
    '3': {'name': _('Check Box'), 'value': 'checkboxes'},
    '4': {'name': _('Radio Button'), 'value': 'radios'},
    '5': {'name': _('List Box'), 'value': 'select'},
    '6': {'name': _('Date'), 'value': 'datetime'}
}
"""Default properties of the item type."""

WEKO_BILLING_FILE_ACCESS = 1
"""Show billing file property in list."""

WEKO_BILLING_FILE_PROP_ATT = 'billing_file_prop'
"""Attribute to detect billing file property."""

WEKO_ITEMTYPES_UI_DEFAULT_PROPERTIES_ATT = 'system_prop'
"""Attribute to detect property is default property which is not shown at properties screen."""

WEKO_ITEMTYPES_UI_UPGRADE_VERSION_ENABLED = True
"""Enable Upgrade Version."""

WEKO_ITEMTYPES_UI_FORCED_IMPORT_ENABLED = False
"""Enable Forced Import."""

DISABLE_DUPLICATION_CHECK = False

WEKO_ITEMTYPES_UI_ADMIN_ROCRATE_MAPPING_TEMPLATE = \
    'weko_itemtypes_ui/admin/create_rocrate_mapping.html'
"""RO-Crate Mapping template for the item type page."""

WEKO_ITEMTYPES_UI_DATASET_PROPERTIES = [
    'about',
    'abstract',
    'accessMode',
    'accessModeSufficient',
    'accessibilityAPI',
    'accessibilityControl',
    'accessibilityFeature',
    'accessibilityHazard',
    'accessibilitySummary',
    'accountablePerson',
    'acquireLicensePage',
    'additionalType',
    'aggregateRating',
    'alternateName',
    'alternativeHeadline',
    'archivedAt',
    'assesses',
    'associatedMedia',
    'audience',
    'audio',
    'author',
    'award',
    'awards',
    'catalog',
    'character',
    'citation',
    'comment',
    'commentCount',
    'conditionsOfAccess',
    'contentLocation',
    'contentRating',
    'contentReferenceTime',
    'contributor',
    'copyrightHolder',
    'copyrightNotice',
    'copyrightYear',
    'correction',
    'countryOfOrigin',
    'creativeWorkStatus',
    'creator',
    'creditText',
    'datasetTimeInterval',
    'dateCreated',
    'dateModified',
    'datePublished',
    'description',
    'disambiguatingDescription',
    'discussionUrl',
    'distribution',
    'editEIDR',
    'editor',
    'educationalAlignment',
    'educationalLevel',
    'educationalUse',
    'encoding',
    'encodingFormat',
    'encodings',
    'exampleOfWork',
    'expires',
    'fileFormat',
    'funder',
    'funding',
    'genre',
    'hasPart',
    'headline',
    'identifier',
    'image',
    'inLanguage',
    'includedDataCatalog',
    'includedInDataCatalog',
    'interactionStatistic',
    'interactivityType',
    'interpretedAsClaim',
    'isAccessibleForFree',
    'isBasedOn',
    'isBasedOnUrl',
    'isFamilyFriendly',
    'isPartOf',
    'issn',
    'keywords',
    'learningResourceType',
    'license',
    'locationCreated',
    'mainEntity',
    'mainEntityOfPage',
    'maintainer',
    'material',
    'materialExtent',
    'measurementMethod',
    'measurementTechnique',
    'mentions',
    'name',
    'offers',
    'pattern',
    'position',
    'potentialAction',
    'producer',
    'provider',
    'publication',
    'publisher',
    'publisherImprint',
    'publishingPrinciples',
    'recordedAt',
    'releasedEvent',
    'review',
    'reviews',
    'sameAs',
    'schemaVersion',
    'sdDatePublished',
    'sdLicense',
    'sdPublisher',
    'size',
    'sourceOrganization',
    'spatial',
    'spatialCoverage',
    'sponsor',
    'subjectOf',
    'teaches',
    'temporal',
    'temporalCoverage',
    'text',
    'thumbnail',
    'thumbnailUrl',
    'timeRequired',
    'translationOfWork',
    'translator',
    'typicalAgeRange',
    'url',
    'usageInfo',
    'variableMeasured',
    'variablesMeasured',
    'version',
    'video',
    'workExample',
    'workTranslation',
]
"""RO-Crate dataset properties. see here: https://schema.org/Dataset"""

WEKO_ITEMTYPES_UI_FILE_PROPERTIES = [
    'about',
    'abstract',
    'accessMode',
    'accessModeSufficient',
    'accessibilityAPI',
    'accessibilityControl',
    'accessibilityFeature',
    'accessibilityHazard',
    'accessibilitySummary',
    'accountablePerson',
    'acquireLicensePage',
    'additionalType',
    'aggregateRating',
    'alternateName',
    'alternativeHeadline',
    'archivedAt',
    'assesses',
    'associatedArticle',
    'associatedMedia',
    'audience',
    'audio',
    'author',
    'award',
    'awards',
    'bitrate',
    'character',
    'citation',
    'comment',
    'commentCount',
    'conditionsOfAccess',
    'contentLocation',
    'contentRating',
    'contentReferenceTime',
    'contentSize',
    'contentUrl',
    'contributor',
    'copyrightHolder',
    'copyrightNotice',
    'copyrightYear',
    'correction',
    'countryOfOrigin',
    'creativeWorkStatus',
    'creator',
    'creditText',
    'dateCreated',
    'dateModified',
    'datePublished',
    'description',
    'disambiguatingDescription',
    'discussionUrl',
    'duration',
    'editEIDR',
    'editor',
    'educationalAlignment',
    'educationalLevel',
    'educationalUse',
    'embedUrl',
    'encodesCreativeWork',
    'encoding',
    'encodingFormat',
    'encodings',
    'endTime',
    'exampleOfWork',
    'expires',
    'fileFormat',
    'funder',
    'funding',
    'genre',
    'hasPart',
    'headline',
    'height',
    'identifier',
    'image',
    'inLanguage',
    'ineligibleRegion',
    'interactionStatistic',
    'interactivityType',
    'interpretedAsClaim',
    'isAccessibleForFree',
    'isBasedOn',
    'isBasedOnUrl',
    'isFamilyFriendly',
    'isPartOf',
    'keywords',
    'learningResourceType',
    'license',
    'locationCreated',
    'mainEntity',
    'mainEntityOfPage',
    'maintainer',
    'material',
    'materialExtent',
    'mentions',
    'name',
    'offers',
    'pattern',
    'playerType',
    'position',
    'potentialAction',
    'producer',
    'productionCompany',
    'provider',
    'publication',
    'publisher',
    'publisherImprint',
    'publishingPrinciples',
    'recordedAt',
    'regionsAllowed',
    'releasedEvent',
    'requiresSubscription',
    'review',
    'reviews',
    'sameAs',
    'schemaVersion',
    'sdDatePublished',
    'sdLicense',
    'sdPublisher',
    'sha256',
    'size',
    'sourceOrganization',
    'spatial',
    'spatialCoverage',
    'sponsor',
    'startTime',
    'subjectOf',
    'teaches',
    'temporal',
    'temporalCoverage',
    'text',
    'thumbnail',
    'thumbnailUrl',
    'timeRequired',
    'translationOfWork',
    'translator',
    'typicalAgeRange',
    'uploadDate',
    'url',
    'usageInfo',
    'version',
    'video',
    'width',
    'workExample',
    'workTranslation',
]
"""RO-Crate file properties. see here: https://schema.org/MediaObject"""
