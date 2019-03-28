require([
    "jquery",
    'typeahead.js',
    'bloodhound',
    "node_modules/angular/angular",
    "node_modules/invenio-csl-js/dist/invenio-csl-js",
    ], function(typeahead, Bloodhound) {
      angular.element(document).ready(function() {
        angular.bootstrap(document.getElementById("invenio-csl"), [
            'invenioCsl',
          ]
        );
      });
    }
);