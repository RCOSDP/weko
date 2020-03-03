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
      let q = urlVars["q"];
        if (q) {
          document.getElementById("q").value = urlVars["q"];
        }
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
  $rootScope.index_id_q = $location.search().q != undefined ? $location.search().q : '';
  $rootScope.journal_info = [];
  $rootScope.collapse_flg = true;
  $rootScope.journal_title = $("#journal_title_i18n").val();
  $rootScope.journal_details = $("#journal_details_i18n").val();
  $rootScope.typeIndexList = (function(){
    var url = new URL(window.location.href );
    var q = url.searchParams.get("q");
    let result = 'item'
    if (q === "0") {
        return 'root'
    }
    return result
  })()


  $rootScope.isCommunityRootIndex = (function(){
    let url = new URL(window.location.href );
    let community = url.searchParams.get("community");
    let rootIndexTree = url.searchParams.get("root_index");
    return !!community && !!rootIndexTree;
  })();

  $rootScope.display_comment = function(comment) {

    return format_comment(comment)
  };
  $rootScope.is_permission = $("#is_permission").val() === 'True' ? true : false
  $rootScope.is_login = $("#is_login").val() === 'True' ? true : false

  $rootScope.display_comment_jounal= function(){
    if ($rootScope.vm.invenioSearchResults.aggregations.path) {
        $('#index_comment').append(format_comment($rootScope.vm.invenioSearchResults.aggregations.path.buckets[0][0].comment))

    }
  }


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
    if (!$rootScope.index_id_q) {
      return;
    }
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

  // Get child id list.
  let child_list = []
  $scope.getChildList = function() {
    if (!$rootScope.index_id_q) {
      return;
    }
    $http({
      method: 'GET',
      url: '/get_child_list/' + $rootScope.index_id_q,
      headers: {'Content-Type': 'application/json'},
    }).then(function successCallback(response) {
      child_list = response.data;
    }, function errorCallback(error) {
      console.log(error);
    });
  }
  $scope.getChildList();

  // Sorting child id list to index list display.
  $scope.sort_index_list = function(data_list) {
    let temp_key_list = []
    $scope.sorted_child_list = []
    if (child_list.length == 0) {
      for (var j = 1; j < data_list.length; j++) {
        $scope.sorted_child_list.push(data_list[j]);
      }
    }
    else {
      for (var i = 0; i < child_list.length; i++) {
        for (var j = 0; j < data_list.length; j++) {
          if (temp_key_list.indexOf(data_list[j].key) == -1 && child_list[i] == data_list[j].key.split('/').pop()) {
            temp_key_list.push(data_list[j].key);
            $scope.sorted_child_list.push(data_list[j]);
          }
        }
      }
    }
  }

  // Check all records for restricted content
  $scope.$on('invenio.search.finished', function(evt) {
    $rootScope.display_comment_jounal()
  });
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
    angular.forEach($scope.vm.invenioSearchResults.hits.hits, function(record) {
      item_index = $rootScope.item_export_checkboxes.indexOf(record.id);
      if (checkAll &&  item_index == -1) {
        $rootScope.item_export_checkboxes.push(record.id);
      } else if(!checkAll && item_index >= 0) {
        $rootScope.item_export_checkboxes.splice(item_index, 1);
      }
    });
  }

  $scope.checkAll = function(checkAll) {
    angular.forEach($scope.vm.invenioSearchResults.hits.hits, function(record) {
      item_index = $rootScope.item_export_checkboxes.indexOf(record.id);
      if (checkAll &&  item_index == -1) {
        $rootScope.item_export_checkboxes.push(record.id);
      } else if(!checkAll && item_index >= 0) {
        $rootScope.item_export_checkboxes.splice(item_index, 1);
      }
    });
  }

  $scope.checkAllExportItems = function(event) {
    if(event.target.checked) {
      $scope.checkAll(true);
      $rootScope.check_all = true;
    }
    else {
      $scope.checkAll(false);
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
      records_metadata = $scope.getExportItemsMetadata();
      $('#record_ids').val(JSON.stringify($rootScope.item_export_checkboxes));
      let export_metadata = {}
      $rootScope.item_export_checkboxes.map((recid)=>{
        $.each(records_metadata, function (index, value) {
          if (value.id == recid) {
            export_metadata[recid] = value;
          }
        });
      })
      $('#record_metadata').val(JSON.stringify(export_metadata));
      $('#export_items_form').submit();  // Submit form and let controller handle file making
    }
    $('#item_export_button').attr("disabled", false);
  }

  $scope.getExportItemsMetadata = function() {
    let cur_url = new URL(window.location.href);
    let q = cur_url.searchParams.get("q");
    let search_type = cur_url.searchParams.get("search_type");

    let request_url = '';

    if (search_type == "2") {
      request_url = '/api/index/?page=1&size=9999&search_type=' + search_type + '&q=' + q;
    } else {
      if (search_type === null) {
        search_type = "0";
      }
      if (q === null) {
        q = "";
      }
      request_url = '/api/records/?page=1&size=9999&search_type=' + search_type + '&q=' + q;
    }

    let search_results = []
    $('#item_export_button').attr("disabled", true);
    $.ajax({
      method: 'GET',
      url: request_url,
      async: false,
      contentType: 'application/json',
      dataType: 'json',
      success: function(data, status){
        search_results = data.hits.hits;
      },
      error: function(status, error){
        console.log(error);
      }
    });

    return search_results;
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
  .controller('itemExportCtrl', itemExportCtrl)
  .filter("sanitize", ['$sce', function($sce) {
        return function(htmlCode){
            return $sce.trustAsHtml(htmlCode);
        }
  }]);

function format_comment(comment){
  let result = ""
  let href = ''
  let text = ''
  let where = 'href'
  let flat = false
  for(let i = 0; i< comment.length; i++){
    let c = comment[i]
    if(c === '[') {
      if(comment[i+1] === '['){
        flat = true;
        i++
        continue
      }
    }
    if(c === ']'){
        if (flat === true && comment[i+1] === ']') {
          flat = false
          text = text ? text : href
          result += '<a href="'+href+'" target="_blank">'+ text + '</a>'
          text = ''
          href = ''
          where = 'href'
          i++

          continue
        }
    }
    if(flat){
      if(c === '|' && where === 'href') {
        where = 'text'
        continue
      }
      if(where === 'text'){
        if(c == '\n') {
          text += "<br/>"
        } else {
          text+=c
        }
      } else {
        if(c == '\n') {
          href += "<br/>"
        } else {
          href+=c
        }
      }
    } else {
      if(c == '\n') {
        result += "<br/>"
      } else {
        result+=c

      }
    }

  }
  if (text) {
     result += '<a href="'+href+'" target="_blank">'+ text + '</a>'
  } else {
    if(href) {
      result += '<a href="'+href+'" target="_blank">'+ href + '</a>'
    }
  }
  return result
}
// add by ryuu. at 20181129 end
