const SPECIFIC_INDEX_VALUE = '1';
(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function() {
    angular.module('searchManagement.controllers', []);
    function searchManagementCtrl($scope, $rootScope,$http,$location){
      var disp = [];
      var frm_cnt = 0;
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
        let url = "/api/admin/search/init_display_index/" + initDispIndex;

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

        if ( lang === 'en' ) {
          document.getElementById("label_contents_" + index).value = mainvalues;
          document.getElementById("hidden_contents_" + index).value = subvalues;
        }
        else if ( lang === 'ja' ) {
          document.getElementById("label_contents_" + index).value = subvalues;
          document.getElementById("hidden_contents_" + index).value = mainvalues;
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

        document.getElementById("labelname_id").value = index;
        document.getElementById("labelname_lang").value = language;
        document.getElementById("editHeader").textContent = contvalues;

        if( language == 'en') {
          document.getElementById("labelname_text1").value = contvalues;
          document.getElementById("labelname_text2").value = subvalues;
        }
        else {
          document.getElementById("labelname_text1").value = subvalues;
          document.getElementById("labelname_text2").value = contvalues;
        }

      });

      $('#item-type-lists').change(function () {
        frm_cnt = 0;
        $(".tr_lists[id^='tr_lists']").each(function(index, formObj) {
          if ($(formObj).attr('id') != 'tr_lists' && $(formObj).attr('id') != 'tr_lists0') {
            $(formObj).remove();
          }
        });

        $scope.setItemTypeInfo();

        $("#tr_lists0 > #item_id > #search_item option[value='0']").prop('selected', true);
        var select_inputType = $("#tr_lists0 > #item_id > #search_item").val();
        $scope.setTextLabel('tr_lists0');
      });

      $('#search_item_chg').on('show.bs.modal', function (event) {

        var subGmn = $(event.relatedTarget);
        var contents = subGmn.data('contents');
        var index = subGmn.data('index');
        let contvalues = $("#" + contents).val();
        document.getElementById("contents_word").value = contents;
        document.getElementById("editHeader2").textContent = contvalues;

        $("#tr_lists0").find("#button_remove").prop('disabled', true);
        $('#search_item_chg').data('index', index);
        $scope.setItemTypeInfo();

        $("#tr_lists0 > #item_id > #search_item option[value='0']").prop('selected', true);
        frm_cnt = 0;
        $(".tr_lists[id^='tr_lists']").each(function(index, formObj) {
          if ($(formObj).attr('id') != 'tr_lists' && $(formObj).attr('id') != 'tr_lists0') {
            $(formObj).remove();
          }
        });

        $scope.setTextLabel('tr_lists0');
      });

      $('button[type="button"]').on('click', function(ev){
        action = this.dataset.action;

        if('save' == action) {
          $('#search_item_chg').trigger('click');
          var count = 0;
          var item_type_id = $("#item-type-lists").val();

          $(".tr_lists[id^='tr_lists']").each(function(index, formObj) {
            if ( count <= frm_cnt ) {
              if( $(formObj).attr('id', 'tr_lists' + count) ) {
                var path1 = $('#tr_lists' + count + ' > #setting_label > #setting_label1 > #path_text1').val();
                var path2 = $('#tr_lists' + count + ' > #setting_label > #setting_label2 > #path_text2').val();
                var conditionpath = $('#tr_lists' + count + ' > #setting_label > #setting_label3 > #condition_path_text').val();
                var conditionvalue = $('#tr_lists' + count + ' > #setting_label > #setting_label4 > #condition_value_text').val();

                var formshape = {path:{type:'',coordinates:''},path_type:{type:'json',coordinates:'json'}}
                var formrange = {path:{gte:'',lte:''},path_type:{gte:'json',lte:'json'}}
                var formpoint = {path:{lat:'',lon:''},path_type:{lat:'json',lon:'json'}}
                var formtext = {path:'', path_type:'json'}

                var index = $('#search_item_chg').data('index');
                var item_input_type = $scope.dataJson.detail_condition[index].input_Type;

                if( item_input_type === 'text' ) {
                  if (!$scope.dataJson['detail_condition'][index]['item_value'][item_type_id]) {
                    $scope.dataJson['detail_condition'][index]['item_value'][item_type_id] = JSON.parse(JSON.stringify(formtext));
                  }
                  $scope.dataJson['detail_condition'][index]['item_value'][item_type_id]['path'] = path1;
                  $scope.dataJson['detail_condition'][index]['item_value'][item_type_id]['condition_path'] = conditionpath;
                  $scope.dataJson['detail_condition'][index]['item_value'][item_type_id]['condition_value'] = conditionvalue;
                }

                if( item_input_type === 'range' ) {
                  if (!$scope.dataJson['detail_condition'][index]['item_value'][item_type_id]) {
                    $scope.dataJson['detail_condition'][index]['item_value'][item_type_id] = JSON.parse(JSON.stringify(formrange));
                  }
                  $scope.dataJson['detail_condition'][index]['item_value'][item_type_id]['path']['gte'] = path1;
                  $scope.dataJson['detail_condition'][index]['item_value'][item_type_id]['path']['lte'] = path2;
                }
                if( item_input_type === 'geo_point' ) {
                  if (!$scope.dataJson['detail_condition'][index]['item_value'][item_type_id]) {
                    $scope.dataJson['detail_condition'][index]['item_value'][item_type_id] = JSON.parse(JSON.stringify(formpoint));
                  }
                  $scope.dataJson['detail_condition'][index]['item_value'][item_type_id]['path']['lat'] = path1;
                  $scope.dataJson['detail_condition'][index]['item_value'][item_type_id]['path']['lon'] = path2;
                }
                if( item_input_type === 'geo_shape' ) {
                  if (!$scope.dataJson['detail_condition'][index]['item_value'][item_type_id]) {
                    $scope.dataJson['detail_condition'][index]['item_value'][item_type_id] = JSON.parse(JSON.stringify(formshape));
                  }
                  $scope.dataJson['detail_condition'][index]['item_value'][item_type_id]['path']['type'] = path1;
                  $scope.dataJson['detail_condition'][index]['item_value'][item_type_id]['path']['coordinates'] = path2;
                }
              }
            }
            count++;
          });
        }
      });

      $scope.setTextLabel = function(tr_id){
        var cnt = 0;
        const idx = $('#search_item_chg').data('index');
        const select_inputType = $scope.dataJson.detail_condition[idx].input_Type;
        var obj = document.getElementById(tr_id);

        var path_label = $("#search_settings_mapping_path").val();
        if ( select_inputType == 'text' ){
          $('#' + tr_id + ' > #setting_label > #setting_label1 > #label_id1').text(path_label + ':');
          $('#' + tr_id + ' > #setting_label > #setting_label2 > #label_id2').text("");
          $('#' + tr_id + ' > #setting_label > #setting_label2').hide();
          $('#' + tr_id + ' > #setting_label > #setting_label3').show();
          $('#' + tr_id + ' > #setting_label > #setting_label4').show();
        }

        if ( select_inputType == 'range' ){
          $('#' + tr_id + ' > #setting_label > #setting_label1 > #label_id1').text(path_label + ' ' + $("#gte").val() + ':');
          $('#' + tr_id + ' > #setting_label > #setting_label2 > #label_id2').text(path_label + ' ' + $("#lte").val() + ':');
          $('#' + tr_id + ' > #setting_label > #setting_label2').show();
          $('#' + tr_id + ' > #setting_label > #setting_label3').hide();
          $('#' + tr_id + ' > #setting_label > #setting_label4').hide();
        }

        if ( select_inputType == 'geo_point' ){
          $('#' + tr_id + ' > #setting_label > #setting_label1 > #label_id1').text(path_label + ' ' + $("#lat").val() + ':');
          $('#' + tr_id + ' > #setting_label > #setting_label2 > #label_id2').text(path_label + ' ' + $("#lon").val() + ':');
          $('#' + tr_id + ' > #setting_label > #setting_label2').show();
          $('#' + tr_id + ' > #setting_label > #setting_label3').hide();
          $('#' + tr_id + ' > #setting_label > #setting_label4').hide();
        }

        if ( select_inputType == 'geo_shape' ){
          $('#' + tr_id + ' > #setting_label > #setting_label1 > #label_id1').text(path_label + ' ' + $("#type").val() + ':');
          $('#' + tr_id + ' > #setting_label > #setting_label2 > #label_id2').text(path_label + ' ' + $("#coordinates").val() + ':');
          $('#' + tr_id + ' > #setting_label > #setting_label2').show();
          $('#' + tr_id + ' > #setting_label > #setting_label3').hide();
          $('#' + tr_id + ' > #setting_label > #setting_label4').hide();
        }

        var flg = false;
        var item_type_id = $("#item-type-lists").val();
        for( cnt = 0; cnt < disp.length; cnt++ ) {
          if( disp[cnt].item_type_id == item_type_id ) {
            $('#' + tr_id + ' > #setting_label > #setting_label1 > #path_text1').val(disp[cnt].path1);
            $('#' + tr_id + ' > #setting_label > #setting_label2 > #path_text2').val(disp[cnt].path2);
            $('#' + tr_id + ' > #item_id > #contents_index').val(disp[cnt].index);
            $('#' + tr_id + ' > #setting_label > #setting_label3 > #condition_path_text').val(disp[cnt].conditionpath);
            $('#' + tr_id + ' > #setting_label > #setting_label4 > #condition_value_text').val(disp[cnt].conditionvalue);

            flg = true;
            break;
          }
        }
        if( !flg ) {
          $('#' + tr_id + ' > #setting_label > #setting_label1 > #path_text1').val("");
          $('#' + tr_id + ' > #setting_label > #setting_label2 > #path_text2').val("");
          $('#' + tr_id + ' > #setting_label > #setting_label3 > #condition_path_text').val("");
          $('#' + tr_id + ' > #setting_label > #setting_label4 > #condition_value_text').val("");
        }
      }

      $scope.setItemTypeInfo = function(){

        const index = $('#search_item_chg').data('index');
        var item_content;
        var item_content_id;
        var item_input_type = "";
        var item_val = "";
        var contents = $("#contents_word").val();
        disp = [];

        var item_type_id = $("#item-type-lists").val();

        if($scope.dataJson.detail_condition[index].item_value){
          item_val = $scope.dataJson.detail_condition[index].item_value;
          item_content_id = contents + index;
          item_content = $("#" + item_content_id).val();

          item_input_type = $scope.dataJson.detail_condition[index].input_Type;
          var item_path1 = "";
          var item_path2 = "";
          var item_pathtype1 = "";
          var item_pathtype2 = "";
          var item_conditionpath = "";
          var item_conditionvalue = "";

          var item_val_sel = "";
          if( item_val[item_type_id] ) {
            item_val_sel = item_val[item_type_id];
            if( item_input_type == 'text'){
              item_path1 = item_val_sel.path;
              item_pathtype1 = item_val_sel.path_type;
              item_conditionpath = item_val_sel.condition_path;
              item_conditionvalue = item_val_sel.condition_value;
            }

            if( item_input_type == 'range'){
              item_path1 = item_val_sel.path.gte;
              item_path2 = item_val_sel.path.lte;
              item_pathtype1 = item_val_sel.path_type.gte;
              item_pathtype2 = item_val_sel.path_type.lte;
            }

            if( item_input_type == 'geo_point'){
              item_path1 = item_val_sel.path.lat;
              item_path2 = item_val_sel.path.lon;
              item_pathtype1 = item_val_sel.path_type.lat;
              item_pathtype2 = item_val_sel.path_type.lon;
            }

            if( item_input_type == 'geo_shape'){
              item_path1 = item_val_sel.path.type;
              item_path2 = item_val_sel.path.coordinates;
              item_pathtype1 = item_val_sel.path_type.type;
              item_pathtype2 = item_val_sel.path_type.coordinates;
            }

            var match = {
              item_type_id : item_type_id,
              contents : item_content,
              input_type: item_input_type,
              path1: item_path1,
              path2: item_path2,
              conditionpath: item_conditionpath,
              conditionvalue: item_conditionvalue,
              pathtype1: item_pathtype1,
              pathtype2: item_pathtype2
            };

            disp.push(match);
          }
        }
      }

      $scope.getJoinedMapping = function(mapping) {
        if (!Array.isArray(mapping)) return '';
        let result = '';
        for (let i = 0; i < mapping.length; i++) {
          // 候補を生成（先頭以外にはカンマを付ける）
          const next = result ? result + ', ' + mapping[i] : mapping[i];

          // 追加しても40文字を超えないなら採用
          if (next.length <= 40) {
            result = next;
          } else {
            result += '...';
            break;
          }
       }
       return result;
      };
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
