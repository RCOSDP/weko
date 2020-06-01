(function (angular) {
 function addAlert(message) {
    $('#alerts').html(
        '<div class="alert alert-light" id="alert-style">' +
        '<button type="button" class="close" data-dismiss="alert">' +
        '&times;</button>' + message + '</div>');
         }
  // Bootstrap it!
  angular.element(document).ready(function() {
    angular.module('siteLicense.controllers', []);
    function siteLicenseCtrl($scope, $rootScope,$http,$location){
      $scope.dbJson = {site_license:[{
                            organization_name:"",
                            mail_address:"",
                            domain_name:"",
                            receive_mail_flag:"F",
                            addresses:[{start_ip_address:[],finish_ip_address:[]}]
                            }],
                     item_type:{
                             allow:[],
                             deny:[]
                             }
                     };

      $scope.ipCheckFlgArry =[];

      // set data of page on init
      $scope.fetch=function(result){
        $scope.dbJson = angular.fromJson(result.slice(2,-2).replace(/\n/g,'\\n'));
        console.log($scope.dbJson);
        for(var data in $scope.dbJson.site_license){
          var b = {ipCheckFlg:false,ipRangeCheck:false};
          $scope.ipCheckFlgArry.push(b);
        }
      };


      $scope.moveSiteLicenseUp= function(arrayIndex){
        var a = JSON.stringify($scope.dbJson.site_license[arrayIndex]);
        var b = JSON.stringify($scope.dbJson.site_license[arrayIndex-1]);
        $scope.dbJson.site_license[arrayIndex] = JSON.parse(b);
        $scope.dbJson.site_license[arrayIndex-1]= JSON.parse(a);

      }

      $scope.moveSiteLicenseDown= function(arrayIndex){
        var a = JSON.stringify($scope.dbJson.site_license[arrayIndex]);
        var b =  JSON.stringify($scope.dbJson.site_license[arrayIndex+1]);
        $scope.dbJson.site_license[arrayIndex] = JSON.parse(b);
        $scope.dbJson.site_license[arrayIndex+1]= JSON.parse(a);
      }

      //add a new IP Address Range
      $scope.addNewRowRange = function(ipIndex) {
         var ipAddressRange = {start_ip_address:[],finish_ip_address:[]};
         $scope.dbJson.site_license[ipIndex].addresses.push(ipAddressRange);
      }
      //add a new site License
      $scope.addNewRowSiteLicense = function() {
         var siteLicenseJson = {
                            organization_name:"",
                            mail_address:"",
                            domain_name:"",
                            receive_mail_flag:"F",
                            addresses:[{start_ip_address:[],finish_ip_address:[]}]
                            };
        $scope.dbJson.site_license.push(siteLicenseJson);

        var subCheckFlg = {ipCheckFlg:false,ipRangeCheck:false};
        $scope.ipCheckFlgArry.push(subCheckFlg);

      }
      // delete selected site License
      $scope.deleteSiteLicense = function(ipIndex){
        $scope.dbJson.site_license.splice(ipIndex,1);
        $scope.ipCheckFlgArry.splice(ipIndex,1);
      }
      // set deny to allow
      $scope.setDenyToAllow= function(index){
        for (let idx = 0; idx < index.length; idx++) {
          let i = index[idx];
          var a = {id:"",name:""};
          a.id = $scope.dbJson.item_type.deny[i].id;
          a.name = $scope.dbJson.item_type.deny[i].name;
          $scope.dbJson.item_type.allow.push(a);
          $scope.dbJson.item_type.deny.splice(i,1);
        }
      }
      // set allow to deny
      $scope.setAllowToDeny= function(index){
        for (let idx = 0; idx < index.length; idx++) {
          let i = index[idx];
          var a = {id:"",name:""};
          a.id = $scope.dbJson.item_type.allow[i].id;
          a.name = $scope.dbJson.item_type.allow[i].name;
          $scope.dbJson.item_type.deny.push(a);
          $scope.dbJson.item_type.allow.splice(i,1);
        }
      }
      //commit
      $scope.commitData=function(){
        var dbjosn = $scope.dbJson;
        for(var chk1 in dbjosn.site_license){
           for(var chk2 in dbjosn.site_license[chk1].addresses){
             var saddr = "";
             var faddr = "";
             for(var i=0; i<4; i++){
                tmp_s=dbjosn.site_license[chk1].addresses[chk2].start_ip_address[i];
                if (typeof tmp_s!=='undefined' && tmp_s.length > 0) {
                  saddr += ("00" + tmp_s).slice(-3);
                }
                tmp_f=dbjosn.site_license[chk1].addresses[chk2].finish_ip_address[i]
                if (typeof tmp_f!=='undefined' && tmp_f.length > 0) {
                  faddr += ("00" + tmp_f).slice(-3);
                }
             }

             if (!saddr || !faddr){
                $scope.ipCheckFlgArry[chk1].ipCheckFlg = true;
             }
             else if (parseInt(saddr) > parseInt(faddr)){
                $scope.ipCheckFlgArry[chk1].ipRangeCheck = true;
                return;
             }
           }
           $scope.ipCheckFlgArry[chk1].ipRangeCheck = false;
        }
        isError = $scope.ipCheckFlgArry.filter(function(item){ return item.ipCheckFlg === true || item.ipRangeCheck === true })[0];
        if (!isError) {
          var url = $location.path();
          dbJson = $scope.dbJson;
          $http.post(url, dbJson).then(function successCallback(response) {
             $('html,body').scrollTop(0);
             addAlert(response.data.message);
          }, function errorCallback(response) {
             alert(response.data.message);
          });
        }
      }

      //入力チェック
      $scope.chcckStr=function(str,p_index){
        var checkStr1 = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/; //正整数
        var flg = checkStr1.test(str);
        if(!flg){
          $scope.ipCheckFlgArry[p_index].ipCheckFlg = true;
        }else{
          $scope.ipCheckFlgArry[p_index].ipCheckFlg = false;
        }
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
      $interpolateProvider.startSymbol('[[');
      $interpolateProvider.endSymbol(']]');
    }]);

    angular.bootstrap(
      document.getElementById('siteLicense'), ['siteLicenseModule']);
  });
})(angular);
