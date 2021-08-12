const SPECIFIC_INDEX_VALUE = '1';
(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function() {
    angular.module('searchManagement.controllers', []);
    function searchManagementCtrl($scope, $rootScope,$http,$location){
      $scope.initData = function (data) {
        $scope.dataJson = angular.fromJson(data);
        $scope.clearNullDataInSortOption();
        $scope.initDispSettingOpt = {}
        $scope.treeData = [];
        $scope.rowspanNum = $scope.dataJson.detail_condition.length+1;
        // Set Data
        $scope.setData();
//        $scope.setSearchKeyOptions();
      }
      // set selected data to allow
      $scope.setAllow=function(data){
        if (data && $scope.dataJson.sort_options.deny.length > data){
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
        if (data && $scope.dataJson.sort_options.allow.length > data){
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

        var cnt = 0;
        const contants_lang = document.getElementById("label_contents_0").lang

        for (cnt; cnt < $scope.dataJson.detail_condition.length; cnt++) {
          let labelname = $("#label_contents_" + cnt).val();
          let labelsubname = $("#hidden_contents_" + cnt).val();

          $scope.dataJson['detail_condition'][cnt]['contents'] = '';
          if(contants_lang == 'ja') {
            $scope.dataJson['detail_condition'][cnt]['contents_value']['ja'] = labelname;
            $scope.dataJson['detail_condition'][cnt]['contents_value']['en'] = labelsubname;
          }
          else {
            $scope.dataJson['detail_condition'][cnt]['contents_value']['en'] = labelname;
            $scope.dataJson['detail_condition'][cnt]['contents_value']['ja'] = labelsubname;
          }
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
          },
          worker: false
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
        $scope.specificIndexText();
        $scope.getInitDisplayIndex();
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
        this.setDefaultInitDisplayIndex();
      }

      $scope.setDefaultInitDisplayIndex = function () {
        if (this.isSpecificIndex()) {
          // Reset tree data to default
          if (this.treeInstance && this.treeInstance.jstree) {
            let nodeChecked = this.treeInstance.jstree(true).get_checked([true]);
            if (nodeChecked.length === 0 && this.treeData.length > 0) {
              this.treeInstance.jstree(true).select_node({id: "0"});
              $("#init_disp_index_text").val("Root Index");
              $("#init_disp_index").val("0");
            } else {
              let node = nodeChecked[0];
              if (node !== undefined) {
                $scope.setInitDisplayIndex(node)
              }
            }
          }
        }
      }

      $scope.setInitDisplayIndex = function (node) {
        $("#init_disp_index_text").val(node.text);
        $("#init_disp_index").val(node.id);
      }

      $scope.selectInitDisplayIndex = function (node, selected, event) {
        $scope.setInitDisplayIndex(selected.node);
      }

      $scope.disSelectInitDisplayIndex = function (node, selected, event) {
        if ($scope.treeInstance && $scope.treeInstance.jstree) {
            $scope.treeInstance.jstree(true).select_node(selected.node);
        }
      }

      $scope.getInitDisplayIndex = function () {
        let initDispIndex = $scope.dataJson['init_disp_setting']['init_disp_index']
        if (!initDispIndex) {
          initDispIndex = "0";
        }
        const currentTime = new Date().getTime();
        let url = "/api/admin/search/init_display_index/" + initDispIndex + "?timestamp=" + currentTime;
        $.get(url)
          .done(function (data) {
            let jstree = $scope.treeInstance.jstree(true);
            jstree.settings.core.data = data.indexes;
            jstree.refresh();
            let currentNode = jstree.get_node({"id": initDispIndex});
            jstree.select_node(currentNode);
            $scope.setInitDisplayIndex(currentNode);
          })
          .fail(function () {
            alert("Fail to get index list.");
          })
      }

      $scope.clearNullDataInSortOption = function () {
        if ($scope.dataJson) {
          $scope.dataJson.sort_options.deny = $scope.dataJson.sort_options.deny.filter(function (element) {
            return element !== null;
          });
          $scope.dataJson.sort_options.allow = $scope.dataJson.sort_options.allow.filter(function (element) {
            return element !== null;
          });
        }
      }
     
      $("#save_button").click(function(){
        $('#search_contents_chg').trigger('click');
        let mainvalues = $("#labelname_text1").val();
        let subvalues = $("#labelname_text2").val();
        let index = $("#labelname_id").val();
        let lang = $("#labelname_lang").val();
        let select1 = $("#sel_lang1").val();
        let select2 = $("#sel_lang2").val();

        if ( select1 == lang ) {
          document.getElementById("label_contents_" + index).value = mainvalues;
        }
        else if ( select2 == lang ) {
          document.getElementById("label_contents_" + index).value = subvalues;
        }
        if ( select1 != lang ) {
          document.getElementById("hidden_contents_" + index).value = mainvalues;
        }
        else if ( select2 != lang ) {
          document.getElementById("hidden_contents_" + index).value = subvalues;
        }
      });

      $('#search_contents_chg').on('show.bs.modal', function (event) {
        var subGmn = $(event.relatedTarget);
        var contents = subGmn.data('contents');
        var subcontents = subGmn.data('subcontents');
        var index = subGmn.data('index');
        var language = subGmn.data('lang');

        let contvalues = $("#" + contents).val();
        let subvalues = $("#" + subcontents).val();

        document.getElementById("labelname_text1").value = contvalues;
        document.getElementById("labelname_text2").value = subvalues;

        document.getElementById("labelname_id").value = index;
        document.getElementById("labelname_lang").value = language;

        var select1 = document.getElementById("sel_lang1");
        var select2 = document.getElementById("sel_lang2");

        if( language == 'ja') {
          select1.options[1].selected = true;  
          select2.options[0].selected = true;  
        }
        else {
          select1.options[0].selected = true;  
          select2.options[1].selected = true;  
        }
        
      });
   
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
