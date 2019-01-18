angular.module('myApp', ['ui.bootstrap'])
 .controller("ItemController",
  function($scope, $modal, $http, $window) {
   $scope.openConfirm = function(message, url, rdt) {
    var modalInstance = $modal.open({
     templateUrl: "confirm-modal.html",
     controller: "ConfirmController",
     resolve: {
      msg: function() {
       return message;
      }
     }
    });
    modalInstance.result.then(function() {
     $http.delete(url).then(
      function(response) {
       // success callback
       $window.location.href = rdt;
      },
      function(response) {
       // failure call back
       console.log(response);
      }
     );
    });
   };
  }
 ).controller('ConfirmController',
  function($scope, $modalInstance, msg) {
   $scope.message = msg;

   $scope.ok = function() {
    $modalInstance.close();
   };
   $scope.cancel = function() {
    $modalInstance.dismiss();
   };
  });
