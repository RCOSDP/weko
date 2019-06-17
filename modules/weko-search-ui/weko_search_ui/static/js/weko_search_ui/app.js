  require([
    "jquery",
    "bootstrap",
    "node_modules/bootstrap-datepicker/dist/js/bootstrap-datepicker"
    ], function() {
    // loading all the jQuery modules for the not require.js ready scripts
    // everywhere.
    $(function(){
      $('#myModal').modal({
        show: false
      })
      page_global = {
        queryObj: null,
        display_list_flg: false
      }
      page_global.queryObj = query_to_hash();
      if (page_global.queryObj) {
        $('#page_count').val(page_global.queryObj['size'])
        $('#page_count').on('change', function(){
          if(page_global.queryObj['size'] != $('#page_count').val()) {
            page_global.queryObj['size'] = $('#page_count').val();
            queryStr = hash_to_query(page_global.queryObj);
            window.location.href = window.location.pathname + '?' + queryStr;
          }
        });
      }
      function query_to_hash(queryString) {
        var query = queryString || location.search.replace(/\?/, "");
        return query.split("&").reduce(function(obj, item, i) {
          if(item) {
            item = item.split('=');
            obj[item[0]] = item[1];
            return obj;
          }
        }, {});
      };
      function hash_to_query(queryObj) {
        var str = '';
        Object.keys(queryObj).forEach(function(key){
          if(str.length > 0) {
            str = str + '&' + key + '=' + queryObj[key];
          } else {
            str = key + '=' + queryObj[key];
          }
        });
        return str;
      }
    });
    function showJournalInfo() {
      var check = setInterval(show, 500);
      function show() {
        if($('#index_list_length').val() !== undefined && $('#index_list_length').val() !== '' && $('#index_list_length').val() !== null) {
          page_global.display_list_flg = $('#display_format').val() == 1;
          if($('#index_tree_list').length || !page_global.display_list_flg){
            $("#journal_info").remove();
          } else {
            $("#journal_info").css({ display: "block" });
          }
          clearInterval(check);
          // display image
          if($("#thumbnail_img").length > 0 && page_global.display_list_flg) {
            $("#journal_info_img").show();
            $("#journal_info_img").html($("#thumbnail_img").get(0));
          }
          $("#thumbnail_img").removeClass("ng-hide");
        }
      }
    }
    $(document).ready(function(){
      showJournalInfo();
      $("#display_details").click(function(){
        $(".icon-right").toggle(50);
        $("#collapsed_details").collapse('toggle');
        $(".icon-down").toggle(50);
      });
    });
});

//add controller to invenioSearch
// add by ryuu. at 20181129 start

function searchResCtrl($scope, $rootScope, $http, $location) {
    var commInfo=$("#community").val();
     if(commInfo != ""){
        $rootScope.commInfo="?community="+commInfo;
        $rootScope.commInfoIndex="&community="+commInfo;
     }else{
        $rootScope.commInfo="";
        $rootScope.commInfoIndex="";
     }
//   button setting
     $rootScope.disable_flg = true;
     $rootScope.display_flg = true;
     $rootScope.index_id_q = $location.search().q;
     $rootScope.journal_info = [];
     $rootScope.collapse_flg = true;
     $rootScope.journal_title = $("#journal_title_i18n").val();
     $rootScope.journal_details = $("#journal_details_i18n").val();

     $scope.itemManagementTabDisplay= function(){
        $rootScope.disable_flg = true;
        $rootScope.display_flg = true;
     }

     $scope.itemManagementEdit= function(){
        $rootScope.disable_flg = false;
        $rootScope.display_flg = false;
     }

     $scope.itemManagementSave= function(){
        var data = $scope.vm.invenioSearchResults.hits.hits
        var custom_sort_list =[]
        for(var x of data){
           var sub = {"id":"", "custom_sort":""}
           sub.id= x.id;
           sub.custom_sort=x.metadata.custom_sort;
           custom_sort_list.push(sub);
        }
        var post_data ={"q_id":$rootScope.index_id_q, "sort":custom_sort_list, "es_data":data}

        // request api
        $http({
            method: 'POST',
            url: '/item_management/save',
            data: post_data,
          headers: {'Content-Type': 'application/json'},
        }).then(function successCallback(response) {
          window.location.href = '/search?search_type=2&q='+$rootScope.index_id_q + "&item_management=sort&sort=custom_sort";
        }, function errorCallback(response) {
          window.location.href = '/search?search_type=2&q='+$rootScope.index_id_q+ "&item_management=sort&sort=custom_sort";
        });
     }

     $scope.itemManagementCancel= function(){
        $rootScope.disable_flg = true;
        $rootScope.display_flg = true;
        $("#tab_display").addClass("active")
     }
     $rootScope.confirmFunc=function(){
        if(!$rootScope.disable_flg){
          return confirm("Is the input contents discarded ?") ;
        }else{
          return true;
        }
     }

     $scope.getJournalInfo= function(){
        // request api
        $http({
            method: 'GET',
            url: '/journal_info/'+$rootScope.index_id_q,
            //data: post_data,
          headers: {'Content-Type': 'application/json'},
        }).then(function successCallback(response) {
          $rootScope.journal_info = response.data;
        }, function errorCallback(error) {
          console.log(error);
        });
     }

     $scope.getJournalInfo();
  }

angular.module('invenioSearch')
  .controller('searchResCtrl', searchResCtrl);

// add by ryuu. at 20181129 end


