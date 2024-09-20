/*
 * This file is part of Invenio.
 * Copyright (C) 2016-2019 CERN.
 *
 * Invenio is free software; you can redistribute it and/or modify it
 * under the terms of the MIT License; see LICENSE file for more details.
 */

define(['js/invenio_communities/directives/module'], function(directives){
  var app = angular.module('invenioCommunities',
                           ['invenioCommunities.directives', ]);
  return app;
});
