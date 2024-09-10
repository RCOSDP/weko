// This file is part of Zenodo.
// Copyright (C) 2016 CERN.
//
// Zenodo is free software; you can redistribute it
// and/or modify it under the terms of the GNU General Public License as
// published by the Free Software Foundation; either version 2 of the
// License, or (at your option) any later version.
//
// Zenodo is distributed in the hope that it will be
// useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
// General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Zenodo; if not, write to the
// Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
// MA 02111-1307, USA.
//
// In applying this license, CERN does not
// waive the privileges and immunities granted to it by virtue of its status
// as an Intergovernmental Organization or submit itself to any jurisdiction.
require([
  "jquery",
  "node_modules/angular/angular",
  "node_modules/invenio-search-js/dist/invenio-search-js",
  "js/invenio_communities/module",
  ], function() {
    // loading all the jQuery modules for the not require.js ready scripts
    // everywhere.

    // On document ready bootstrap angular
    angular.element(document).ready(function() {
      angular.bootstrap(
        document.getElementById("invenio-communities-search"),
                                ['invenioSearch', 'invenioCommunities']
      );
      communityId = $('#community-id').text()
      $(".container-fluid").addClass(communityId + "-body");
      $(".panel").addClass(communityId + "-panel");
    });
  });
