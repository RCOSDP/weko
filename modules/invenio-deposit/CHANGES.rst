..
    This file is part of Invenio.
    Copyright (C) 2015, 2016, 2017 CERN.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.


Changes
=======

Version 1.0.0a9 (release 2017-12-06)

- Refactoring for Invenio 3.

Version 0.2.0 (release 2015-09-08)

- Removes dependency on bibupload module.
- Removes dependency on legacy bibdocfile module.
- Implements optional JSONSchema-based deposit forms. One can install
  required dependencies using 'invenio_deposit[jsonschema]'.
- Allows panel headers in form groups to have an icon. Example usage
  {"icon": "fa fa-user"}.
- Adds missing `invenio_access` dependency and amends past upgrade
  recipes following its separation into standalone package.
- Adds missing dependency to invenio-knowledge package and fixes
  imports.
- Fixes MintedDOIValidator, so that it correctly checks if DOI was
  already minted for the specific upload.

Version 0.1.0 (release 2015-08-14)

- Initial public release.
