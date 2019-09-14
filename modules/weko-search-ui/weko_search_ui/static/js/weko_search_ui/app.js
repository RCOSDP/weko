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
    let urlVars = getUrlVars();
    if (urlVars !== {} && urlVars.hasOwnProperty("q") && urlVars.hasOwnProperty("search_type") && urlVars["search_type"] !== "2") {
      document.getElementById("q").value = url.parse(urlVars["q"], true);
    } else {
      document.getElementById("q").value = "";
    }
    $("#display_details").click(function(){
      $(".icon-right").toggle(50);
      $("#collapsed_details").collapse('toggle');
      $(".icon-down").toggle(50);
    });
  });
});


function getUrlVars() {
  let vars = {};
  let parts = decodeURI(window.location.href).replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {vars[key] = value;});
  return vars;
}

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
      url: '/admin/items/custom_sort/save',
      data: post_data,
      headers: {'Content-Type': 'application/json'},
    }).then(function successCallback(response) {
      window.location.href = '/admin/items/search?search_type=2&q='+$rootScope.index_id_q + "&item_management=sort&sort=custom_sort";
    }, function errorCallback(response) {
      window.location.href = '/admin/items/search?search_type=2&q='+$rootScope.index_id_q+ "&item_management=sort&sort=custom_sort";
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

// Item export controller
// Defined here because this feature is an extension of search
function itemExportCtrl($scope, $rootScope, $http, $location) {
  $rootScope.item_export_checkboxes = [];
  $rootScope.max_export_num=$("#max_export_num").val();
  $rootScope.items_with_restricted_content = [];
  $rootScope.check_all = false;


  // Check if current hits in selected array
  $scope.checkIfAllInArray = function() {
    all_in_array = true;
    angular.forEach($scope.vm.invenioSearchResults.hits.hits, function(record) {
      item_index = $rootScope.item_export_checkboxes.indexOf(record.id);
      if(item_index == -1) {
        all_in_array = false;
      }
    });
    return all_in_array;
  }

  $scope.checkAll = function() {
    angular.forEach($scope.vm.invenioSearchResults.hits.hits, function(record) {
      item_index = $rootScope.item_export_checkboxes.indexOf(record.id);
      if(item_index == -1){
        $rootScope.item_export_checkboxes.push(record.id);
      }
    });
  }

  $scope.checkAllExportItems = function(event) {
    if(event.target.checked) {
      $scope.checkAll();
      $rootScope.check_all = true;
    }
    else {
      $rootScope.item_export_checkboxes = [];
      $rootScope.check_all = false;
    }
  }

  $scope.checkExportItem = function(record_id) {
    item_index = $rootScope.item_export_checkboxes.indexOf(record_id);
    if(item_index == -1) {
      $rootScope.item_export_checkboxes.push(record_id);
      $rootScope.check_all = $scope.checkIfAllInArray() ? true : false;
    }
    else {
      $rootScope.item_export_checkboxes.splice(item_index, 1);
      $rootScope.check_all = false;
    }
  }

  $scope.exportItems = function() {
   if($rootScope.item_export_checkboxes.length <= $rootScope.max_export_num) {
     $('#record_ids').val(JSON.stringify($rootScope.item_export_checkboxes));
     $('#export_items_form').submit();  // Submit form and let controller handle file making
   }
  }

  $scope.checkForRestrictedContent = function(record_id) {
    record_ids = [];
    angular.forEach($scope.vm.invenioSearchResults.hits.hits, function(record) {
      record_ids.push(record.id);
    });

    $http({
      method: 'POST',
      url: '/api/items/check_restricted_content',
      data: {'record_ids': record_ids},
      headers: {'Content-Type': 'application/json'},
    }).then(function successCallback(response) {
      $rootScope.items_with_restricted_content = response.data.restricted_records;
    }, function errorCallback(response) {
      $rootScope.items_with_restricted_content = [];
      console.log('ERROR: Unable to check for restricted items.'); // TODO: Do something useful
    });
  }

  // Check all records for restricted content
  $scope.$on('invenio.search.finished', function(evt) {
    $scope.checkForRestrictedContent();
    if($scope.checkIfAllInArray()) {
      $rootScope.check_all = true;
    }
    else {
      $rootScope.check_all = false;
    }
  });
}

angular.module('invenioSearch')
  .controller('searchResCtrl', searchResCtrl)
  .controller('itemExportCtrl', itemExportCtrl);

// add by ryuu. at 20181129 end
