const SPECIFIC_INDEX_VALUE = '1';
(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function() {
    angular.module('searchManagement.controllers', []);
    function searchManagementCtrl($scope, $rootScope,$http,$location){
      var regist = [];
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

        if ( regist.length != 0 ) {
          var formshape = {path:{type:'',coordinates:''},path_type:{type:'json',coordinates:'json'}}
          var formrange = {path:{gte:'',lte:''},path_type:{gte:'json',lte:'json'}}
          var formpoint = {path:{lat:'',lon:''},path_type:{lat:'json',lon:'json'}}
          var formtext = {path:'', path_type:'json'}

          for ( var count =0; count < $scope.dataJson['detail_condition'].length; count++ ) {
            for ( var cnt = 0; cnt < regist.length; cnt++ ) {
              if( count == regist[cnt].index ) {
                itemtype_id = regist[cnt].item_type_id

                if( regist[cnt].input_type == 'text' ) {
                  if (!$scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]) {
                    $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id] = JSON.parse(JSON.stringify(formtext));;
                  }
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path'] = regist[cnt].path1;
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path_type'] = regist[cnt].pathtype1;
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['condition_path'] = regist[cnt].conditionpath;
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['condition_value'] = regist[cnt].conditionvalue;
                }

                if( regist[cnt].input_type == 'range' ) {
                  if (!$scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]) {
                    $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id] = JSON.parse(JSON.stringify(formrange));;
                  }
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path']['gte'] = regist[cnt].path1;
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path_type']['gte'] = regist[cnt].pathtype1;
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path']['lte'] = regist[cnt].path2;
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path_type']['lte'] = regist[cnt].pathtype2;
                }
                if( regist[cnt].input_type == 'geo_point' ) {
                  if (!$scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]) {
                    $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id] = JSON.parse(JSON.stringify(formpoint));;
                  }
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path']['lat'] = regist[cnt].path1;
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path_type']['lat'] = regist[cnt].pathtype1;
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path']['lon'] = regist[cnt].path2;
                  $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]['path_type']['lon'] = regist[cnt].pathtype2;
                }
                if( regist[cnt].input_type == 'geo_shape' ) {
                  if (!$scope.dataJson['detail_condition'][count]['item_value'][itemtype_id]) {
                    $scope.dataJson['detail_condition'][count]['item_value'][itemtype_id] = JSON.parse(JSON.stringify(formshape));;
                  }
                  $scope.dataJson['detail_condition'][count]['item_value'][item_type_id]['path']['type'] = regist[cnt].path1;
                  $scope.dataJson['detail_condition'][count]['item_value'][item_type_id]['path_type']['type'] = regist[cnt].pathtype1;
                  $scope.dataJson['detail_condition'][count]['item_value'][item_type_id]['path']['coordinates'] = regist[cnt].path2;
                  $scope.dataJson['detail_condition'][count]['item_value'][item_type_id]['path_type']['coordinates'] = regist[cnt].pathtype2;
                }
                break;
              }
            }
          }
        }
        // Clear the registration target for advanced search items and allow registration to continue.
        regist.splice(0);
        
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
        $scope.setTextLabel(select_inputType, 'tr_lists0', true);
      });

      $('#search_item').change(function () {
        var select_inputType = $("#" + this.closest("tr").id).find("#search_item").val();
        $scope.setTextLabel(select_inputType, this.closest("tr").id, false);
      });


      $('#search_item_chg').on('show.bs.modal', function (event) {
        var subGmn = $(event.relatedTarget);
        var contents = subGmn.data('contents');
        document.getElementById("contents_word").value = contents;

        $("#tr_lists0").find("#button_remove").prop('disabled', true);
        $scope.setItemTypeInfo();

        $("#tr_lists0 > #item_id > #search_item option[value='0']").prop('selected', true);
        frm_cnt = 0;
        $(".tr_lists[id^='tr_lists']").each(function(index, formObj) {
          if ($(formObj).attr('id') != 'tr_lists' && $(formObj).attr('id') != 'tr_lists0') {
            $(formObj).remove();
          }
        });

        var select_inputType = $("#tr_lists0 > #item_id > #search_item").val();
        $scope.setTextLabel(select_inputType, 'tr_lists0', true);
      });

      $('button[type="button"]').on('click', function(ev){
        action = this.dataset.action;

        if('add' == action) {
          frm_cnt++;

          $('#tr_lists0').clone(true).appendTo($('#t_keyword > #tb_keyword')).attr('id', 'tr_lists' + frm_cnt ).end();
          $("#tr_lists" + frm_cnt).find("#button_remove").prop('disabled', false);
          $("#tr_lists" + frm_cnt + " > #item_id > #search_item option[value='0']").prop('selected', true);

          var select_inputType = $("#tr_lists" + frm_cnt + " > #item_id > #search_item").val();
          $scope.setTextLabel(select_inputType, 'tr_lists' + frm_cnt, true);
        }

        if('del' == action) {
          this.closest("tr").remove();

          frm_cnt = 0;
          $(".tr_lists[id^='tr_lists']").each(function(index, formObj) {
            if ($(formObj).attr('id') != 'tr_lists' && $(formObj).attr('id') != 'tr_lists0') {
                frm_cnt++;
                $(formObj).attr('id', 'tr_lists' + frm_cnt).end();
            }
          });

          if( frm_cnt == 0 ) {
            $("#tr_lists0").find("#button_remove").prop('disabled',true);
          }
        }

        if('save' == action) {
          $('#search_item_chg').trigger('click');
          var count = 0;
          var item_type_id = $("#item-type-lists").val();

          $(".tr_lists[id^='tr_lists']").each(function(index, formObj) {
            if ( count <= frm_cnt ) {
              if( $(formObj).attr('id', 'tr_lists' + count) ) {
                var pathtype1 = $('#tr_lists' + count + ' > #setting_label > #setting_label1 > #label_list1 option:selected').text();
                var pathtype2 = $('#tr_lists' + count + ' > #setting_label > #setting_label2 > #label_list2 option:selected').text();
                var path1 = $('#tr_lists' + count + ' > #setting_label > #setting_label1 > #path_text1').val();
                var path2 = $('#tr_lists' + count + ' > #setting_label > #setting_label2 > #path_text2').val();
                var conditionpath = $('#tr_lists' + count + ' > #setting_label > #setting_label3 > #condition_path_text').val();
                var conditionvalue = $('#tr_lists' + count + ' > #setting_label > #setting_label4 > #condition_value_text').val();
                var select_contents = $('#tr_lists' + count + ' > #item_id > #search_item option:selected').text();
                var item_content = $('#tr_lists' + count + ' > #item_id > #contents_index').val();
                var item_input_type = $('#tr_lists' + count + ' > #item_id > #search_item option:selected').val();

                reg_match = {
                  item_type_id : item_type_id,
                  contents : select_contents,
                  index: item_content,
                  input_type: item_input_type,
                  path1: path1,
                  path2: path2,
                  pathtype1: pathtype1,
                  pathtype2: pathtype2,
                  conditionpath: conditionpath,
                  conditionvalue: conditionvalue
                }
                regist.push(reg_match);
              }
            }
            count++;
          });
        }
      });

      $scope.setTextLabel = function(select_inputType, tr_id, initFlg){
        var cnt = 0;
        var idx = 0;
        var obj = document.getElementById(tr_id);
        var selectobj = obj.firstElementChild.firstElementChild;
        if (!initFlg) {
          idx = selectobj.selectedIndex;
        }

        var select_contents  = selectobj.options[idx].text;

        if ( select_inputType == 'text' ){
          $('#' + tr_id + ' > #label_id > div > #label_id1').text("");
          $('#' + tr_id + ' > #label_id > div > #label_id2').text("");
          $('#' + tr_id + ' > #setting_label > #setting_label2').hide();
          $('#' + tr_id + ' > #setting_label > #setting_label3').show();
          $('#' + tr_id + ' > #setting_label > #setting_label4').show();
        }

        if ( select_inputType == 'range' ){
          $('#' + tr_id + ' > #label_id > div > #label_id1').text($("#gte").val());
          $('#' + tr_id + ' > #label_id > div > #label_id2').text($("#lte").val());
          $('#' + tr_id + ' > #setting_label > #setting_label2').show();
          $('#' + tr_id + ' > #setting_label > #setting_label3').hide();
          $('#' + tr_id + ' > #setting_label > #setting_label4').hide();
        }

        if ( select_inputType == 'geo_point' ){
          $('#' + tr_id + ' > #label_id > div > #label_id1').text($("#lat").val());
          $('#' + tr_id + ' > #label_id > div > #label_id2').text($("#lon").val());
          $('#' + tr_id + ' > #setting_label > #setting_label2').show();
          $('#' + tr_id + ' > #setting_label > #setting_label3').hide();
          $('#' + tr_id + ' > #setting_label > #setting_label4').hide();
        }

        if ( select_inputType == 'geo_shape' ){
          $('#' + tr_id + ' > #label_id > div > #label_id1').text($("#type").val());
          $('#' + tr_id + ' > #label_id > div > #label_id2').text($("#coordinates").val());
          $('#' + tr_id + ' > #setting_label > #setting_label2').show();
          $('#' + tr_id + ' > #setting_label > #setting_label3').hide();
          $('#' + tr_id + ' > #setting_label > #setting_label4').hide();
        }

        var flg = false;
        for( cnt = 0; cnt < disp.length; cnt++ ) {
          if( disp[cnt].contents == select_contents ) {
            $('#' + tr_id + ' > #setting_label > #setting_label1 > #path_text1').val(disp[cnt].path1);
            $('#' + tr_id + ' > #setting_label > #setting_label2 > #path_text2').val(disp[cnt].path2);
            $('#' + tr_id + ' > #item_id > #contents_index').val(disp[cnt].index);
            $('#' + tr_id + ' > #setting_label > #setting_label3 > #condition_path_text').val(disp[cnt].conditionpath);
            $('#' + tr_id + ' > #setting_label > #setting_label4 > #condition_value_text').val(disp[cnt].conditionvalue);

            if( disp[cnt].pathtype1 == 'xml' ) {
              $("#" + tr_id + " > #setting_label > #setting_label1 > #label_list1 option[value='1']").prop('selected', true);
            } else {
              $("#" + tr_id + " > #setting_label > #setting_label1 > #label_list1 option[value='0']").prop('selected', true);
            }
            if( disp[cnt].pathtype2 == 'xml' ) {
              $("#" + tr_id + " > #setting_label > #setting_label2 > #label_list2 option[value='1']").prop('selected', true);
            } else {
              $("#" + tr_id + " > #setting_label > #setting_label2 > #label_list2 option[value='0']").prop('selected', true);
            }

            flg = true;
            break;
          }
        }
        if( !flg ) {
          $('#' + tr_id + ' > #setting_label > #setting_label1 > #path_text1').val("");
          $('#' + tr_id + ' > #setting_label > #setting_label2 > #path_text2').val("");
          $("#" + tr_id + " > #setting_label > #setting_label1 > #label_list1 option[value='0']").prop('selected', true);
          $("#" + tr_id + " > #setting_label > #setting_label2 > #label_list2 option[value='0']").prop('selected', true);
          $('#' + tr_id + ' > #setting_label > #setting_label3 > #condition_path_text').val("");
          $('#' + tr_id + ' > #setting_label > #setting_label4 > #condition_value_text').val("");
        }
      }

      $scope.setItemTypeInfo = function(){

        var item_content;
        var item_content_id;
        var item_input_type = "";
        var item_val = "";
        var contents = $("#contents_word").val();
        disp = [];

        var item_type_id = $("#item-type-lists").val();

        $('#tr_lists0 > #item_id > #search_item').empty()
        for (labelcnt = 0; labelcnt < $scope.dataJson.detail_condition.length; labelcnt++ ) {

          if($scope.dataJson.detail_condition[labelcnt].item_value){
            item_val = $scope.dataJson.detail_condition[labelcnt].item_value;
            item_content_id = contents + labelcnt;
            item_content = $("#" + item_content_id).val();

            item_input_type = $scope.dataJson.detail_condition[labelcnt].input_Type;

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
            }

            var match = {
              item_type_id : item_type_id,
              contents : item_content,
              input_type: item_input_type,
              index: labelcnt,
              path1: item_path1,
              path2: item_path2,
              conditionpath: item_conditionpath,
              conditionvalue: item_conditionvalue,
              pathtype1: item_pathtype1,
              pathtype2: item_pathtype2
            };

            disp.push(match);
            var select = $('#tr_lists0 > #item_id > #search_item').append($('<option>').html(item_content).val(item_input_type));
          }
        }
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
