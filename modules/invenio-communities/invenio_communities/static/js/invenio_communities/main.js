/*
 * This file is part of Invenio.
 * Copyright (C) 2016-2019 CERN.
 *
 * Invenio is free software; you can redistribute it and/or modify it
 * under the terms of the MIT License; see LICENSE file for more details.
 */
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
