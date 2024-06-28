/*
 * This file is part of Invenio.
 * Copyright (C) 2016-2019 CERN.
 *
 * Invenio is free software; you can redistribute it and/or modify it
 * under the terms of the MIT License; see LICENSE file for more details.
 */

(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function() {
    angular.bootstrap(
      document.getElementById("invenio-records"), [
        'invenioRecords', 'schemaForm', 'mgcrea.ngStrap',
        'mgcrea.ngStrap.modal', 'pascalprecht.translate', 'ui.select',
        'mgcrea.ngStrap.select', 'invenioFiles'
      ]
    );
  });
})(angular);
