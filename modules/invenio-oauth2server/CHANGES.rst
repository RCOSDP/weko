..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 1.1.0 (released 2020-03-10)

- Provides compatibility with werkzeug 1.0.0 for flask_oauthlib

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
