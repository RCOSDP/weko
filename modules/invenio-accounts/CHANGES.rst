..
    This file is part of Invenio.
    Copyright (C) 2015-2024 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 5.0.1 (released 2024-03-22)

- models: fix username case-insensitive comparator

Version 5.0.0 (released 2024-03-21)

- fix: before_first_request deprecation
- change module blueprint to callable

Version 4.0.2 (released 2024-02-19)

- add change history tracking of domains
- add task to calculate domain statistics
- add methods to verify, block and deactivate users in datastore

Version 4.0.1 (released 2024-02-01)

- models: fix column type for domain status

Version 4.0.0 (released 2024-01-29)

- sessions: check for request before accessing session
- global: new domain list feature

Version 3.5.1 (released 2023-12-10)

- views: disable registering of `settings.change_password` menu
  if `ACCOUNTS_REGISTER_BLUEPRINT` is False

Version 3.5.0 (released 2023-11-10)

- datastore: override put method to add changes to db history

Version 3.4.4 (released 2023-11-10)

models: do not set value in user preference getter

Version 3.4.3 (released 2023-10-20)

- email: force lowercase

Version 3.4.2 (released 2023-10-17)

- Adds support for user impersonation

Version 3.4.1 (released 2023-10-14)

- datastore: prevent autoflush on db

Version 3.4.0 (released 2023-08-30)

- templates: refactor send confirmation template

Version 3.3.1 (released 2023-08-23)

- config: set `ACCOUNTS_DEFAULT_USERS_VERIFIED` to False by default

Version 3.3.0 (released 2023-08-21)

- models: add `verified_at` column in User model. The default value is controlled by
  a new config variable called `ACCOUNTS_DEFAULT_USERS_VERIFIED`. If True, then a date
  is generated, otherwise is set to `None`.

Version 3.2.1 (released 2023-08-17)

- alembic: fix sqlalchemy op.execute statements due to latest sqlalchamy-continuum

Version 3.2.0 (released 2023-08-02)

- users: add blocket_at and verified_at data model fields

Version 3.1.0 (released 2023-07-31)

- templates: Improve accessibility and layout
- pulled translations

Version 3.0.3 (released 2023-06-15)

- models: fix autogeneration of role id

Version 3.0.2 (released 2023-06-14)

- alembic: adapt recipe to mysql

Version 3.0.1 (released 2023-06-14)

- alembic: fix upgrade recipes

Version 3.0.0 (released 2023-06-14)

- models: add managed field to groups
- models: alter primary key type of group (id)
- cli: pass id on create role action

Version 2.2.0 (released 2023-04-25)

- models: add support for locale in user preferences

Version 2.1.0 (released 2023-03-01)

- global: replace deprecated babelex imports
- update invenio-i18n

Version 2.0.2 (released 2022-12-14)

- cli: add `--confirm` flag when creating a user
- new config variables to set the default user and email visibility
- register_user: method accepts new argument, `send_register_msg`, to control
  programmatically the send of registration email independently of the global
  configuration.

Version 2.0.1 (released 2022-11-18)

- Add translation workflow
- Add pulled translations
- Add black
- Fix icons not appearing

Version 2.0.0 (released 2022-05-23)

- Adds customizable user profiles and user preferences fields to the user
  data model.

- Adds version counter to the user table to enable optimistic concurrency
  control on the user table.

- Moves login information fields from user table to a separate login
  information table.

- Moves the external user identity table from Invenio-OAuthclient to
  Invenio-Accounts.

- Adds support for tracking changed users within a transaction to allow for
  updating the related indexes.

- Changes from using Flask-Security to using a private fork named
  Flask-Security-Invenio. Flask-Security-Too was evaluated but was found to
  have significantly increased scope with features not needed.

Version 1.4.9 (released 2021-12-04)

- Fixed issue with account creation via CLI due to issue with changed API in
  Flask-WTF.

Version 1.4.8 (released 2021-10-18)

- Unpin Flask requirement.

Version 1.4.7 (released 2021-10-06)

- Adds celery task to remove IP addresses from user table after a specified
  retention period (defaults to 30 days).

Version 1.4.6 (released 2021-07-12)

- Adds german translations

Version 1.4.5 (released 2021-05-21)

- Removes config entrypoint.
- Bump module versions.

Version 1.4.4 (released 2021-05-11)

- Enables login view function overridability.
- Allows to disable local login via configuration variable.

Version 1.4.3 (released 2020-12-17)

- Adds theme dependent icons.

Version 1.4.2 (released 2020-12-11)

- Fixes logout from security view.

Version 1.4.1 (released 2020-12-10)

- Fixes styling of forgot password form in semantic ui theme.

Version 1.4.0 (released 2020-12-09)

- Major: adds new Semantic UI theme.
- Adds Turkish translations.
- Fixes ``next`` parameter being used in the sign-up form.
- Fixes issue with translation files causing translations not to be picked up.
- Fixes wording from sign in to log in.
- Removes password length validation during login.

Version 1.3.0 (released 2020-05-15)

- Refreshes the CSRF token on login and logout.
- Removes the example app.
- Migrate from `Flask-KVSession` to `Flask-KVSession-Invenio`, fork of
  the former.

Version 1.2.2 (released 2020-05-13)

*This release was removed from PyPI on 2020-05-15 due to issues with the
release.*

Version 1.2.1 (released 2020-04-28)

- Fixes issue with the latest WTForms v2.3.x release which now requires an
  extra library for email validation.

Version 1.2.0 (released 2020-03-09)

- Replaces Flask dependency with centrally managed invenio-base

Version 1.1.4 (released 2020-04-28)

- Fixes issue with the latest WTForms v2.3.x release which now requires an
  extra library for email validation.

Version 1.1.3 (released 2020-02-19)

- Replaces Flask-CeleryExt to invenio-celery due to version incompatibilities
  with celery, kombu. Removes Flask-BabelExt already provided by invenio-i18n

Version 1.1.2 (released 2020-02-12)

- Fixes requirements for Flask, Werkzeug and Flask-Login due to
  incompatibilities of latest released modules.

Version 1.1.1 (released 2019-03-10)

- Fixes an issue where the HTTP headers X-Session-ID and X-User-ID are added
  even if the value is not known. This causes 'None' to be logged in Nginx,
  instead of simply '-'.

Version 1.1.0 (released 2019-02-15)

- Added support for for adding the user id and session id of the current user
  into the HTTP headers (``X-User-ID`` and ``X-Session-ID``) for upstream
  servers to use. For instance, this way current user/session ids can be logged
  by Nginx into the web server access logs. The feature is off by default and
  can be enabled via the ``ACCOUNTS_USERINFO_HEADERS`` configuration variable.
  Note: The upstream server should strip the two headers from the response
  returned to the client. The purpose is purely to allow upstream proxies like
  Nginx to log the user/session id for a specific request.

- Changed token expiration from 5 days to 30 minutes for the password reset
  token and email confirmation token. Using the tokens will as a side-effect
  login in the user, which means that if the link is leaked (e.g. forwarded by
  the users themselves), then another person can use the link to access the
  account. Flask-Security v3.1.0 addresses this issue, but has not yet been
  released.

- Fixes issue that could rehash the user password in the adminstration
  interface.

Version 1.0.2 (released 2018-10-31)

- Added AnonymousIdentity loader to app initialisation to fix the ``any_user``
  Need in Invenio-Access.

Version 1.0.1 (released 2018-05-25)

- Bumped Flask-CeleryExt from v0.3.0 to v0.3.1 to fix issue with Celery version
  string not being parsable and thus causing problems with installing Celery.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
