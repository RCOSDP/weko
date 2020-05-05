..
    This file is part of Invenio.
    Copyright (C) 2017-2019 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 1.2.4 (released 2019-11-20)

- Disable ratelimit for celery.

Version 1.2.3 (released 2019-10-10)

- Make `static_url_path` configurable through environment variable.

Version 1.2.2 (released 2019-08-29)

- Unpins Invenio packages versions.

Version 1.2.1 (released 2019-08-21)

- Exempts the "/ping" view from rate limiting.

Version 1.2.0 (released 2019-07-29)

- Fixes issue with instance_path and static_folder being globals. Depends on
  change in Invenio-Base v1.1.0

- Improves rate limiting function to have limits per guest and per
  authenticated users.

Version 1.1.1 (released 2019-07-15)

- Fixes a security issue where APP_ALLOWED_HOSTS was not always being checked,
  and thus could allow host header injection attacks.

  NOTE: you should never route requests to your application with a wrong host
  header. The APP_ALLOWED_HOSTS exists as an extra protective measure, because
  it is easy to misconfigure your web server.

  The root cause was that Werkzeug's trusted host feature only works when
  request.host is being evaluated. This means that for instance when only
  url_for (part of the routing system) is used, then the host header check is
  not performed.

Version 1.1.0 (released 2018-12-14)

- The Flask-DebugToolbar extension is now automatically registered if
  installed.

Version 1.0.5 (released 2018-12-05)

- Add health check view

- Fix response headers assertion in tests

Version 1.0.4 (released 2018-10-11)

- Fix Content Security Policy headers when set empty in DEBUG mode.

Version 1.0.3 (released 2018-10-08)

- Fix Content Security Policy headers when running in DEBUG mode.

Version 1.0.2 (released 2018-08-24)

- Allows use of Flask-DebugToolbar when running in DEBUG mode.

Version 1.0.1 (released 2018-06-29)

- Pin Flask-Talisman.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
