const SPECIFIC_INDEX_VALUE = '1';
(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function() {
    angular.module('searchManagement.controllers', []);
    function searchManagementCtrl($scope, $rootScope,$http,$location){
      $scope.initData = function (data, searchManagementOptions, initDispIndex) {
        $scope.dataJson = angular.fromJson(data);
        $scope.searchMgtOptsJson = angular.fromJson(searchManagementOptions);
        $scope.initDispSettingOpt = {}
        if ($scope.searchMgtOptsJson) {
          $scope.initDispSettingOpt = $scope.searchMgtOptsJson.init_disp_setting_options;
        }
        $scope.treeData = angular.fromJson(initDispIndex);
        $scope.rowspanNum = $scope.dataJson.detail_condition.length+1;
        // Set Da
        $scope.setData();
//        $scope.setSearchKeyOptions();
      }
      // set selected data to allow
      $scope.setAllow=function(data){
        if (data){
          if (data.length==1){
            obj = $scope.dataJson.sort_options.deny[data[0]]
            $scope.dataJson.sort_options.allow.push(obj)
            $scope.dataJson.sort_options.deny.splice(data[0],1)
          }else{
            for(var i=data.length-1;i>=0;i--){
              obj = $scope.dataJson.sort_options.deny[data[i]]
              $scope.dataJson.sort_options.allow.push(obj)
              $scope.dataJson.sort_options.deny.splice(data[i],1)
            }
          }
          $scope.setSearchKeyOptions();
        }
        $scope.setDefaultSortKey();
      }
      // set selected data to deny
      $scope.setDeny=function(data){
        if (data){
          if (data.length==1){
            obj = $scope.dataJson.sort_options.allow[data[0]]
            $scope.dataJson.sort_options.deny.push(obj)
            $scope.dataJson.sort_options.allow.splice(data[0],1)
          }else{
            for(var i=data.length-1;i>=0;i--){
              obj = $scope.dataJson.sort_options.allow[data[i]]
              $scope.dataJson.sort_options.deny.push(obj)
              $scope.dataJson.sort_options.allow.splice(data[i],1)
            }
          }
          $scope.setSearchKeyOptions();
        }
        $scope.setDefaultSortKey();
      }
      //
        function addAlert(message) {
                $('#alerts').append(
                    '<div class="alert alert-light" id="alert-style">' +
                    '<button type="button" class="close" data-dismiss="alert">' +
                    '&times;</button>' + message + '</div>');
        }

      $scope.saveData=function(){
        var url = $location.path();
        let initialDisplayIndex = $("#init_disp_index").val();
        if (initialDisplayIndex && this.isSpecificIndex()) {
          $scope.dataJson['init_disp_setting']['init_disp_index'] = initialDisplayIndex;
        } else {
          $scope.dataJson['init_disp_setting']['init_disp_index'] = '';
        }
        let dbJson = $scope.dataJson;

        $http.post(url, dbJson).then(function successCallback(response) {
            // alert(response.data.message);
            $('html,body').scrollTop(0);
            addAlert(response.data.message);
            // Move to top
           }, function errorCallback(response) {
           alert(response.data.message);
        });
      }
      // search key setting
      $scope.setSearchKeyOptions = function(){
        // init
        var deny_flg = 0;
        angular.forEach($scope.dataJson.dlt_index_sort_options,function(item_sort_index,sort_index,sort_array){
          deny_flg = 0;
          angular.forEach($scope.dataJson.sort_options.deny,function(item_deny,deny_index,deny_array){
            if(item_sort_index.id.split('_')[0] ==item_deny.id.split('_')[0]){
              deny_flg = 1;
            }
          })
          if(deny_flg == 0){
            item_sort_index.disableFlg = false;
          }else{
            item_sort_index.disableFlg = true;
          }
        })
        $scope.dataJson.dlt_keyword_sort_options = angular.copy($scope.dataJson.dlt_index_sort_options);
      }
      // setting default sort key
      $scope.setDefaultSortKey= function(){
        var loop_flg = 0;
        var sort_key = '';
        angular.forEach($scope.dataJson.dlt_index_sort_options,function(item,index,array){
          if(loop_flg ==0 && !item.disableFlg){
            sort_key = item.id;
            loop_flg = 1;
          }
        })
        angular.forEach($scope.dataJson.dlt_index_sort_options,function(item,index,array){
          if($scope.dataJson.dlt_index_sort_selected == item.id && item.disableFlg){
            $scope.dataJson.dlt_index_sort_selected = sort_key;
          }
          if($scope.dataJson.dlt_keyword_sort_selected == item.id && item.disableFlg){
            $scope.dataJson.dlt_keyword_sort_selected = sort_key;
          }
        })
      }

      $scope.treeConfig = {
        core: {
          multiple: false,
          animation: false,
          error: function (error) {
            console.error('treeCtrl: error from js tree - ' + angular.toJson(error));
          },
          check_callback: true,
          themes: {
            dots: false,
            icons: false,
          }
        },
        checkbox: {
          three_state: false,
          whole_node: false
        },
        version: 1,
        plugins: ['checkbox']
      };

      $scope.setDefaultDataForInitDisplaySetting = function () {
        if (!$scope.dataJson.hasOwnProperty('init_disp_setting')) {
          $scope.dataJson['init_disp_setting'] = {
            'init_disp_screen_setting': '0',
            'init_disp_index_disp_method': '0',
            'init_disp_index': ''
          }
        }
      }

      $scope.setData = function () {
        $scope.setDefaultDataForInitDisplaySetting();
        $scope.specificIndex();
        $scope.specificIndexText();
      }

      $scope.specificIndexText = function () {
        if (this.isSpecificIndex()) {
          $scope.treeData.forEach(function (nodeData) {
            if (nodeData.hasOwnProperty('state')) {
                if (nodeData.state['selected']) {
                  $("#init_disp_index_text").val(nodeData.text);
                  $("#init_disp_index").val(nodeData.id);
                  return null;
                }
            }
          });
        }
      }

      $scope.isSpecificIndex = function () {
        const dispIndexDispMethod = $scope.dataJson['init_disp_setting']['init_disp_index_disp_method'];
        return dispIndexDispMethod === SPECIFIC_INDEX_VALUE
      }

      $scope.specificIndex = function () {
        if (!this.isSpecificIndex()) {
          // Reset
          $scope.treeInstance.jstree(true).uncheck_all();
          this.clearInitDisplayIndex();
        }
      }

      $scope.clearInitDisplayIndex = function () {
        $("#init_disp_index_text").val("");
        $("#init_disp_index").val("");
      }

      $scope.selectInitDisplayIndex = function (node, selected, event) {
        $("#init_disp_index_text").val(selected.node.text);
        $("#init_disp_index").val(selected.node.id);
      }

      $scope.disSelectInitDisplayIndex = function (node, selected, event) {
        this.clearInitDisplayIndex();
      }

    }
    // Inject depedencies
    searchManagementCtrl.$inject = [
      '$scope',
      '$rootScope',
      '$http',
      '$location'
    ];
    angular.module('searchManagement.controllers')
      .controller('searchManagementCtrl', searchManagementCtrl);

    angular.module('searchSettingModule', ['searchManagement.controllers']);

    angular.module('searchSettingModule', ['searchManagement.controllers']).config(['$interpolateProvider', function($interpolateProvider) {
      $interpolateProvider.startSymbol('[[');
      $interpolateProvider.endSymbol(']]');
    }]);

    angular.bootstrap(
      document.getElementById('search_management'), ['searchSettingModule', 'ngJsTree']);
  });
})(angular);
