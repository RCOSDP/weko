..
    This file is part of Invenio.
    Copyright (C) 2015-2018 CERN.

    Invenio is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version 1.0.1 (released 2018-04-12)

- Fixes issue with task running in request context, when only the app context
  is needed. This causes issues when e.g host header injection protection is
  turned on.

Version 1.0.0 (released 2018-03-23)

- Initial public release.
