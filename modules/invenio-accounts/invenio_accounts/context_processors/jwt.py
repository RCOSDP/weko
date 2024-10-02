# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""JWT context processors."""

from flask import current_app, render_template
from markupsafe import Markup

from ..proxies import current_accounts


def jwt_proccessor():
    """Context processor for jwt."""

    def jwt():
        """Context processor function to generate jwt."""
        token = current_accounts.jwt_creation_factory()
        return Markup(
            render_template(
                current_app.config["ACCOUNTS_JWT_DOM_TOKEN_TEMPLATE"], token=token
            )
        )

    def jwt_token():
        """Context processor function to generate jwt."""
        return current_accounts.jwt_creation_factory()

    return {
        "jwt": jwt,
        "jwt_token": jwt_token,
    }
