angular.module('myApp',[])
  .controller('mp', function ($scope, $http) {
    $scope.reqData = {};
    $scope.doDel = function (val) {
      $http({
        method: 'Delete',
        url: val
        // data: $scope.reqData
      }).then(function successCallback(response) {
        console.log(response);
      }, function (error) {
        console.log(error);
      });
    }
  })
