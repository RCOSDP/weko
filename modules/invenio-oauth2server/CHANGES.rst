..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 2.3.0 (released 2024-03-22)

- fix: before_first_request deprecation
  (add finalise app entrypoint)


Version 2.2.1 (released 2023-10-31)

- settings: simplify token query

Version 2.2.0 (released 2023-09-12)

- new-buttons: remove secondary class from buttons

Version 2.1.0 (released 2023-07-31)

- applications: Improve templates for UI and accessibility
- pulled translations

Version 2.0.0 (released 2023-03-02)

- drop python2.7 support
- remove deprecated flask-babelex dependency and imports
- upgrade invenio-i18n
- upgrade invenio-admin

Version 1.3.8 (released 2022-11-18)

- add translations

Version 1.3.7 (released 2022-08-04)

- save user in the flask global

Version 1.3.6 (released 2022-06-27)

- extract translation messages
- add German translations

Version 1.3.5 (released 2022-02-28)

- Replaces pkg_resources with importlib.
- Fix translation issue with fuzzy translations.
- Fix Flask 2 compatibility issue.

Version 1.3.4 (released 2021-07-15)

- Adds german translations

Version 1.3.3 (released 2021-06-01)

- Maximum version of WTForms set to <3.0.0 due to incompatibility issues.

Version 1.3.2 (released 2020-12-17)

- Adds theme dependent icons.
- Fixes layout and styling issues.
- Fixes UX issues related to button ordering.

Version 1.3.1 (released 2020-12-11)

- Fixes issue with form for application creation.
- Fixes problem with rendering errors in the form.

Version 1.3.0 (released 2020-12-09)

- Integrates Semantic-UI templates.
- Sets `cancel` button's color to Semantic-UI default.

Version 1.2.0 (released 2020-05-14)

- Allow bypassing CSRF checks when using bearer tokens.

Version 1.1.1 (released 2020-05-11)

- Deprecated Python versions lower than 3.6.0. Now supporting 3.6.0 and 3.7.0.
- Minimum version of Invenio-Accounts bumped to v1.2.1 due WTForms moving the
  email validation to an optional dependency.
- Maximum version of Sphinx set to 3 (lower than) due to an error with
  working outside the application context.
- Maximum version of SQLAlchemy-Utils set to 0.36 due to breaking changes
  with MySQL (VARCHAR length).

Version 1.1.0 (released 2020-03-10)

- Provides compatibility with werkzeug 1.0.0 for flask_oauthlib

Version 1.0.5 (released 2020-05-11)

- Deprecated Python versions lower than 3.6.0. Now supporting 3.6.0 and 3.7.0.
- Minimum version of Invenio-Accounts set to v1.1.4 due WTForms moving the
  email validation to an optional dependency.
- Minimum version of Flask-BableEx set to v0.9.4 due Werkzeug breaking imports.
- Minimum version of oauthlib set to v2.1.0.
- Maximum version of Sphinx set to 3 (lower than) due to an error with
  working outside the application context.
- Maximum version of SQLAlchemy-Utils set to 0.36 due to breaking changes
  with MySQL (VARCHAR length).

Version 1.0.4 (released 2019-12-05)

- Removes updating the ``expires`` for personal tokens.
- Removes ``OAUTH2_PROVIDER_TOKEN_EXPIRES_IN`` from configuration.

Version 1.0.3 (released 2019-01-15)

- Restrict oauthlib to latest v2.
- Restrict requests-oauthlib lower than 1.2.0 because of oauthlib 3.

Version 1.0.2 (released 2018-11-02)

- Fix incosistent OAuth2 state initialization between UI and REST applications.
- Basic token management CLI commands for creating/deleting personal access
  tokens.
- Better token creation warning messages.

Version 1.0.1 (released 2018-05-25)

- Flask v1.0 support.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
