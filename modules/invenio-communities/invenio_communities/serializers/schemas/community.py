# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Community JSON schema."""

from __future__ import absolute_import, print_function

from flask import current_app, url_for
from marshmallow import Schema, fields, post_dump

from invenio_communities.links import default_links_item_factory, \
    default_links_pagination_factory


class CommunitySchemaV1(Schema):
    """Schema for a community."""

    id = fields.String()
    title = fields.String()
    description = fields.String()
    page = fields.String()
    curation_policy = fields.String()
    last_record_accepted = fields.DateTime()
    created = fields.DateTime()
    updated = fields.DateTime()
    id_user = fields.Integer()
    logo_url = fields.Method('get_logo_url')

    def get_logo_url(self, obj):
        """Get the community logo URL."""
        if current_app and obj.logo_url:
            return u'{site_url}{path}'.format(
                site_url=current_app.config.get('THEME_SITEURL'),
                path=obj.logo_url,
            )

    @post_dump(pass_many=False)
    def item_links_addition(self, data):
        """Add the links for each community."""
        links_item_factory = self.context.get('links_item_factory',
                                              default_links_item_factory)
        data['links'] = links_item_factory(data)
        return data

    @post_dump(pass_many=True)
    def envelope(self, data, many):
        """Wrap result in envelope."""
        if not many:
            return data

        result = dict(
            hits=dict(
                hits=data,
                total=self.context.get('total', len(data))
            )
        )

        page = self.context.get('page')
        if page:
            links_pagination_factory = self.context.get(
                'links_pagination_factory',
                default_links_pagination_factory
            )

            urlkwargs = self.context.get('urlkwargs', {})

            result['links'] = links_pagination_factory(page, urlkwargs)

        return result
