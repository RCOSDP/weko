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
        for(let i=0;i < $scope.dbJson.site_license.length;i++){
          $scope.ipCheckFlgArry[i] =[];
          for(let j=0;j < $scope.dbJson.site_license[i].addresses.length; j++){
            const b = {ipCheckFlg:false,ipRangeCheck:false};
            $scope.ipCheckFlgArry[i][j]=b;
          }
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
         const subCheckFlg = {ipCheckFlg:false,ipRangeCheck:false};
         $scope.ipCheckFlgArry[ipIndex].push(subCheckFlg);
      }

      $scope.removeIpAddress = function(ipIndex,index,index2) {
        index.addresses.splice(ipIndex,1);
        $scope.ipCheckFlgArry[index2].splice(ipIndex,1);
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
        $scope.ipCheckFlgArry.push([subCheckFlg]);
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
        rangeCheck($scope);
        let isError = false;

        outerLoop:
        for(let i=0;i < $scope.dbJson.site_license.length;i++){
          for(let j=0;j < $scope.dbJson.site_license[i].addresses.length; j++){
            if($scope.ipCheckFlgArry[i][j].ipCheckFlg === true || $scope.ipCheckFlgArry[i][j].ipRangeCheck === true ){
                isError = true;
                break outerLoop;
            }
          }
        }

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
      $scope.checkStr=function(str,p_index,index){
        var checkStr1 = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/; //正整数
        var flg = checkStr1.test(str);
        if(!flg){
          $scope.ipCheckFlgArry[p_index][index].ipCheckFlg = true;
        }else{
          $scope.ipCheckFlgArry[p_index][index].ipCheckFlg = false;
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

function rangeCheck($scope){
  const dbjosn = $scope.dbJson;
    for(let chk1=0;chk1<dbjosn.site_license.length;chk1++){
      for(let chk2=0;chk2<dbjosn.site_license[chk1].addresses.length;chk2++){
        let saddr = "";
        let faddr = "";
        for(let i=0; i<4; i++){
          let tmp_s=dbjosn.site_license[chk1].addresses[chk2].start_ip_address[i];
          if (typeof tmp_s!=='undefined' && tmp_s.length > 0) {
              saddr += ("00" + tmp_s).slice(-3);
            }
          let tmp_f=dbjosn.site_license[chk1].addresses[chk2].finish_ip_address[i]
          if (typeof tmp_f!=='undefined' && tmp_f.length > 0) {
              faddr += ("00" + tmp_f).slice(-3);
            }
        }
             
        if (!saddr || !faddr){
          $scope.ipCheckFlgArry[chk1][chk2].ipCheckFlg = true;
        }
        else if (parseInt(saddr) > parseInt(faddr)){
          $scope.ipCheckFlgArry[chk1][chk2].ipRangeCheck = true;
        }
        else{
          $scope.ipCheckFlgArry[chk1][chk2].ipRangeCheck = false;
        }
      }
    }
}