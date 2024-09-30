/*
 * This file is part of Invenio.
 * Copyright (C) 2016-2019 CERN.
 *
 * Invenio is free software; you can redistribute it and/or modify it
 * under the terms of the MIT License; see LICENSE file for more details.
 */

define([], function(){
  function invenioSearchResultsProvisional($http, $q) {

    // Functions

    /**
     * Force apply the attributes to the scope
     * @memberof invenioSearchResults
     * @param {service} scope -  The scope of this element.
     * @param {service} element - Element that this direcive is assigned to.
     * @param {service} attrs - Attribute of this element.
     * @param {service} http - Angular HTTP requests service.
     * @param {invenioSearchController} vm - Invenio search controller.
     */
    function link(scope, element, attrs, vm) {
      scope.communityCurationEndpoint = attrs.communityCurationEndpoint;
      scope.recordTemplate = attrs.recordTemplate;
      scope.handleCommunityClick = function(action, recid) {
          // scope.isPressed=true;
          if(!scope.communitiesCurationResults) {
          scope.communitiesCurationResults = {};
        }

        $http({
          method: 'POST',
          url: scope.communityCurationEndpoint,
          data: {
            'recid': recid,
            'action': action,
          },
          headers: {'Content-Type': 'application/json'},
        }).then(function successCallback(result) {
          var successMsg;
          if(action == 'accept') {
            successMsg = "The record was successfully accepted.";
          }
          else if(action == 'reject') {
            successMsg = "The record was successfully rejected.";
          }
          scope.communitiesCurationResults[recid] = {success: successMsg};

          }, function errorCallback(result) {
            scope.communitiesCurationResults[recid] = {error: "An error occurred while processing your request."};
          });
      };
    }

    /**
     * Choose template for search loading
     * @memberof invenioSearchREsults
     * @param {service} element - Element that this direcive is assigned to.
     * @param {service} attrs - Attribute of this element.
     * @example
     *    Minimal template `template.html` usage
     *    <div ng-repeat="record in invenioSearchResults track by $index">
     *      <div ng-include="recordsTemplate"></div>
     *    </div>
     *
     *    Minimal `recordsTemplate`
     *    <h2>{{ record.title }}</h2>
     */
    function templateUrl(element, attrs) {
      return attrs.template;
    }

    ////////////
    return {
      restrict: 'AE',
      scope: false,
      templateUrl: templateUrl,
      link: link,
    };
  }
  invenioSearchResultsProvisional.$inject = ['$http', '$q'];
  return invenioSearchResultsProvisional;
});
