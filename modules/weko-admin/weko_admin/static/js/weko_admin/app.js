(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function() {
    angular.module('siteLicense.controllers', []);
    function siteLicenseCtrl($scope, $rootScope,$http,$location){

      // data of page to json
      var ipAddressRange = {start_ip_address:[],finish_ip_address:[]};
      var siteLicenseJson = {
                            organization_name:"",
                            mail_address:"",
                            domain_name:"",
                            addresses:[ipAddressRange]
                            };
      var itemTypeDetail = {allow:[{id:"",name:""},{id:"",name:""}],deny:[]};
      var dbJson = {site_license:[siteLicenseJson],item_type:itemTypeDetail};


//      var dbJson = {site_license:[{
//                            organization_name:"",
//                            mail_address:"",
//                            domain_name:"",
//                            addresses:[{start_ip_address:[],finish_ip_address:[]}]
//                            }],
//                     item_type:{
//                             allow:[],
//                             deny:[]
//                             }
//                     };
//

      $scope.fetch=function(result){
        console.log(result);
        dbJson = angular.fromJson(result.slice(2,-2));
        $scope.dbJson = angular.fromJson(result.slice(2,-2));
        console.log($scope.sl_lst);
      };
      // set data of page
      $scope.dbJson = dbJson;

      $scope.moveSiteLicenseUp= function(arrayIndex){
        var a = dbJson.site_license[arrayIndex];
        dbJson.site_license[arrayIndex] = dbJson.site_license[arrayIndex-1];
        dbJson.site_license[arrayIndex-1]= a;
        $scope.dbJson = dbJson;
      }

      $scope.moveSiteLicenseDown= function(arrayIndex){
        var a = dbJson.site_license[arrayIndex];
        dbJson.site_license[arrayIndex] = dbJson.site_license[arrayIndex+1];
        dbJson.site_license[arrayIndex+1]= a;
        $scope.dbJson = dbJson;
      }

      //add a new IP Address Range
      $scope.addNewRowRange = function(ipIndex) {
         var ipAddressRange = {start_ip_address:[],finish_ip_address:[]};
         dbJson.site_license[ipIndex].addresses.push(ipAddressRange);
         $scope.dbJson = dbJson;
      }
      //add a new site License
      $scope.addNewRowSiteLicense = function() {
         var siteLicenseJson = {
                            organization_name:"",
                            mail_address:"",
                            domain_name:"",
                            addresses:[{start_ip_address:[],finish_ip_address:[]}]
                            };
         dbJson.site_license.push(siteLicenseJson);
         $scope.dbJson = dbJson;
      }
      // delete selected site License
      $scope.deleteSiteLicense = function(ipIndex){
        dbJson.site_license.splice(ipIndex,1);
        $scope.dbJson = dbJson;
      }
      // set deny to allow
      $scope.setDenyToAllow= function(index){
        var a = {id:"",name:""};
        for(var i=0; i< dbJson.item_type.deny.length;i++){
          if(dbJson.item_type.deny[i].id == index){
            a.id = dbJson.item_type.deny[i].id;
            a.name = dbJson.item_type.deny[i].name;
            dbJson.item_type.allow.push(a);
            dbJson.item_type.deny.splice(i,1);
            return;
          }
        }
      }
      // set allow to deny
      $scope.setAllowToDeny= function(index){
        var a = {id:"",name:""};
        for(var i=0; i< dbJson.item_type.allow.length;i++){
          if(dbJson.item_type.allow[i].id == index){
            a.id = dbJson.item_type.allow[i].id;
            a.name = dbJson.item_type.allow[i].name;
            dbJson.item_type.deny.push(a);
            dbJson.item_type.allow.splice(i,1);
            return;
          }
        }
      }
      //commit
      $scope.commitData=function(){
        var url = $location.path();
        dbJson = $scope.dbJson;
        $http.post(url, dbJson).then(successCallback, errorCallback);
      }
    }
    // Inject depedencies
    siteLicenseCtrl.$inject = [
      '$scope',
      '$rootScope',
      '$http',
      '$location'
    ];
    angular.module('siteLicense.controllers')
      .controller('siteLicenseCtrl', siteLicenseCtrl);

    angular.module('siteLicenseModule', ['siteLicense.controllers']);

     angular.module('siteLicenseModule', ['siteLicense.controllers']).config(['$interpolateProvider', function($interpolateProvider) {
  　　$interpolateProvider.startSymbol('{[');
  　　$interpolateProvider.endSymbol(']}');
　　}]);

    angular.bootstrap(
      document.getElementById('siteLicense'), ['siteLicenseModule']);
  });
})(angular);

