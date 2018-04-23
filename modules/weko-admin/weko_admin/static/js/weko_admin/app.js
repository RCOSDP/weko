angular.element(document).ready(function() {

  var app = angular.module('siteLicense', []);
  app.controller('siteLicenseFormCtrl', function($scope) {
      $scope.master = {firstName:"John", lastName:"Doe"};
      $scope.reset = function() {
          $scope.user = angular.copy($scope.master);
      };
      $scope.reset();
  });

});
