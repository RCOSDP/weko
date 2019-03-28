require([
    // "jquery",
    // "bootstrap",
    // "typeahead.js",
    "bloodhound",
    "node_modules/angular/angular",
    "node_modules/invenio-csl-js/dist/invenio-csl-js",
], function() {
    console.log("Hello World");
    angular.element(document).ready(function() {
        angular.bootstrap(document.getElementById("invenio-csl"), [
            'invenioCsl',
        ]);
    });  
});  