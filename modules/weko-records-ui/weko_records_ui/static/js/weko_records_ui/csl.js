require.config({
    baseUrl: "/static/",
    paths: {
      jquery: "node_modules/jquery/jquery",
      bootstrap: "node_modules/bootstrap-sass/assets/javascripts/bootstrap",
      angular: "node_modules/angular/angular",
      typeahead: 'node_modules/typeahead.js/dist/typeahead.jquery',
      bloodhound: 'node_modules/typeahead.js/dist/bloodhound',
      clipboard: 'node_modules/clipboard/dist/clipboard',
    },
    shim: {
      angular: {
        exports: 'angular'
      },
      jquery: {
        exports: "$"
      },
      bootstrap: {
        deps: ["jquery"]
      },
      clipboard: {
        exports: "Clipboard"
      }
    }
  });
  
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