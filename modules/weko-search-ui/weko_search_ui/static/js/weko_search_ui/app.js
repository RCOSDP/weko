const MESSAGE = {
  bibtex_err: {
    en: "Required item is not inputted.",
    ja: "必須項目がありません。",
  }
}
require([
  "jquery",
  "bootstrap",
  "node_modules/bootstrap-datepicker/dist/js/bootstrap-datepicker"
], function () {
  // loading all the jQuery modules for the not require.js ready scripts
  // everywhere.
  $(function () {
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
      $('#page_count').on('change', function () {
        if (page_global.queryObj['size'] != $('#page_count').val()) {
          page_global.queryObj['size'] = $('#page_count').val();
          queryStr = hash_to_query(page_global.queryObj);
          window.location.href = window.location.pathname + '?' + queryStr;
        }
      });
    }
    function query_to_hash(queryString) {
      var query = queryString || location.search.replace(/\?/, "");
      return query.split("&").reduce(function (obj, item, i) {
        if (item) {
          item = item.split('=');
          obj[item[0]] = item[1];
          return obj;
        }
      }, {});
    };
    function hash_to_query(queryObj) {
      var str = '';
      Object.keys(queryObj).forEach(function (key) {
        if (str.length > 0) {
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
      if ($('#index_list_length').val() !== undefined && $('#index_list_length').val() !== '' && $('#index_list_length').val() !== null) {
        page_global.display_list_flg = $('#display_format').val() == 1;
        if ($('#index_tree_list').length || !page_global.display_list_flg) {
          $("#journal_info").remove();
        } else {
          $("#journal_info").css({ display: "block" });
        }
        clearInterval(check);
        // display image
        if ($("#thumbnail_img").length > 0 && page_global.display_list_flg) {
          $("#journal_info_img").show();
          $("#journal_info_img").html($("#thumbnail_img").get(0));
        }
        $("#thumbnail_img").removeClass("ng-hide");
      }
    }
  }

  $(document).ready(function () {
    showJournalInfo();

    let urlVars = getUrlVars();
    if (
      urlVars !== {} &&
      urlVars.hasOwnProperty("q") &&
      urlVars.hasOwnProperty("search_type") &&
      urlVars["search_type"] !== "2"
    ) {
      let searchValue = sessionStorage.getItem('q', '');
      document.getElementById('q').value = searchValue;
    } else {
      let elem = document.getElementById("q");
      if (elem !== null && typeof elem !== "undefined") {
        document.getElementById("q").value = "";
      }
    }

    $("#display_details").click(function () {
      $(".icon-right").toggle(50);
      $("#collapsed_details").collapse('toggle');
      $(".icon-down").toggle(50);
    });
    function getUrlVars() {
      let vars = {};
      let parts = decodeURI(window.location.href).replace(/[?&]+([^=&]+)=([^&]*)/gi, function (m, key, value) { vars[key] = value; });
      return vars;
    }
  });
});

function getMessage(messageCode) {
  const defaultLanguage = "en";
  let currentLanguage = document.getElementById("current_language").value;
  let message = MESSAGE[messageCode];
  if (message) {
    if (message[currentLanguage]) {
      return message[currentLanguage];
    } else {
      return message[defaultLanguage];
    }
  } else {
    return "";
  }
}

//add controller to invenioSearch
// add by ryuu. at 20181129 start

function searchResCtrl($scope, $rootScope, $http, $location) {
  var commInfo = $("#community").val();
  if (commInfo != "") {
    $rootScope.commInfo = "?community=" + commInfo;
    $rootScope.commInfoIndex = "&community=" + commInfo;
  } else {
    $rootScope.commInfo = "";
    $rootScope.commInfoIndex = "";
  }

  $rootScope.pageSizes = [20, 50, 75, 100];
  $rootScope.vm.invenioPageSize = 20;
  $rootScope.handlePageSizeChange = function handlePageSizeChange() {
    $rootScope.vm.invenioSearchArgs.size = $rootScope.vm.invenioPageSize;
    $rootScope.vm.invenioSearchArgs.page = 1;
    let search = new URLSearchParams(window.location.search);
    search.set('size', $rootScope.vm.invenioSearchArgs.size);
    search.set('page', 1);
    if(window.invenioSearchFunctions) {
      window.history.pushState(null,document.title,window.location.pathname + '?' + search);
      if($rootScope.vm.invenioSearchHiddenParams.size) {
        $rootScope.vm.invenioSearchHiddenParams.size = $rootScope.vm.invenioSearchArgs.size;
      }else {
        $rootScope.vm.invenioSearchCurrentArgs.params.size = $rootScope.vm.invenioSearchArgs.size;
      }
    }else{
      window.location.href = "/search?" + search;
    }
  }
  function onCurrentPageSizeChange(newValue, oldValue) {
    if(newValue) $rootScope.vm.invenioPageSize = parseInt(newValue);
  }
  $rootScope.$watch('vm.invenioSearchArgs.size', onCurrentPageSizeChange);

  /**
   * This process is performed when searching without loading the full screen.
   * In this process, the search is reflected only in the search results,
   * but in the event [invenio.search.finished] after the search,
   * the search results are also reflected in the facet items.
   *
   * @param {URLSearchParams} search Search Conditions.
   */
  $rootScope.reSearchInvenio = (search) => {

    //TODO PAGE と TimeStampを入れ替える。
    search.set('page','1');
    search.set('size', $scope.vm.invenioSearchArgs.size);
    search.set('sort', $scope.vm.invenioSearchArgs.sort);
    search.set('timestamp',Date.now().toString());
    window.history.pushState(null,document.title,"/search?" + search);

    let url = search.get('search_type') == 2 ? "/api/index/" : "/api/records/";

    $rootScope.$apply(function() {
      $rootScope.vm.invenioSearchCurrentArgs.url = url;
      $rootScope.vm.invenioSearchArgs.page = 1;
      $rootScope.vm.invenioSearchLoading = true;
      $rootScope.vm.invenioSearchHiddenParams = [];
    })
  }

  $rootScope.getSettingDefault = function () {
    let data = null;
    $.ajax({
        async: false,
        method: 'GET',
        url: '/get_search_setting',
        headers: { 'Content-Type': 'application/json' },
    }).then(function successCallback(response) {
      if (response.status === 1) {
        data = response.data;
        if (data.dlt_index_sort_selected !== null && data.dlt_index_sort_selected !== undefined) {
          let key_sort = data.dlt_index_sort_selected;
          let descOrEsc = "";
          if (key_sort.includes("_asc")) {
            key_sort = key_sort.replace("_asc", "");
          }
          if (key_sort.includes("_desc")) {
            descOrEsc = "-";
            key_sort = key_sort.replace("_desc", "");
          }

          // Default param
          let param = {
            page: 1,
            size: data.dlt_dis_num_selected,
            sort: descOrEsc + key_sort
          };

          // fetch_select
          if(response.enable_fetch_select) {
            window.invenioSearchFunctions = {};
            window.invenioSearchFunctions.reSearchInvenio = $scope.reSearchInvenio;
          }

          // If initial display setting is root index
          if (data.init_disp_setting.init_disp_index === "0") {
            param['search_type'] = "0";
            param['q'] = "0";
          }
          $rootScope.vm.invenioSearchCurrentArgs = {
            method: "GET",
            params: param
          };
        }
      }
    }, function errorCallback(error) {
        console.log(error);
    });
  }
  $rootScope.getSettingDefault();

  $rootScope.disable_flg = true;
  $rootScope.display_flg = true;
  $rootScope.index_id_q = $location.search().q != undefined ? $location.search().q : '';
  let topPageIndexId = $("#index_id_q").val();
  if (topPageIndexId !== undefined && !$rootScope.index_id_q) {
    $rootScope.index_id_q = topPageIndexId;
  }
  $rootScope.journal_info = [];
  $rootScope.collapse_flg = true;
  $rootScope.journal_title = $("#journal_title_i18n").val();
  $rootScope.journal_details = $("#journal_details_i18n").val();
  $rootScope.typeIndexList = function() {
    var url = new URL(window.location.href );
    var q = url.searchParams.get("q");
    let result = 'item';
    if (q === "0") {
      return 'root';
    }
    return result;
  }

  $rootScope.isCommunityRootIndex = function() {
    let url = new URL(window.location.href );
    let community = url.searchParams.get("community");
    let rootIndexTree = url.searchParams.get("root_index");
    return !!community && !!rootIndexTree;
  };

  $rootScope.display_comment = function (comment) {

    return format_comment(comment)
  };
  $rootScope.is_permission = $("#is_permission").val() === 'True' ? true : false
  $rootScope.is_login = $("#is_login").val() === 'True' ? true : false

  $rootScope.display_comment_jounal = function () {
    let aggregations = $rootScope.vm.invenioSearchResults.aggregations || {};
    if (aggregations['path'] && aggregations.path.buckets[0] && aggregations.path.buckets[0][0]) {
      $('#index_comment').append(format_comment(aggregations.path.buckets[0][0].comment))
    }
  }


  $scope.itemManagementTabDisplay = function () {
    $rootScope.disable_flg = true;
    $rootScope.display_flg = true;
  }

  $scope.itemManagementEdit = function () {
    $rootScope.disable_flg = false;
    $rootScope.display_flg = false;
  }

  $scope.itemManagementSave = function () {
    var data = $scope.vm.invenioSearchResults.hits.hits
    var custom_sort_list =[]
    for (var x in data) {
      var sub = {"id":"", "custom_sort":""}
      sub.id= data[x].id;
      sub.custom_sort=data[x].metadata.custom_sort;
      custom_sort_list.push(sub);
    }
    var post_data = { "q_id": $rootScope.index_id_q, "sort": custom_sort_list, "es_data": data }

    // request api
    $http({
      method: 'POST',
      url: '/admin/items/custom_sort/save',
      data: post_data,
      headers: { 'Content-Type': 'application/json' },
    }).then(function successCallback(response) {
      window.location.href = '/admin/items/search?search_type=2&q=' + $rootScope.index_id_q + "&item_management=sort&sort=custom_sort";
    }, function errorCallback(response) {
      window.location.href = '/admin/items/search?search_type=2&q=' + $rootScope.index_id_q + "&item_management=sort&sort=custom_sort";
    });
  }

  $scope.itemManagementCancel = function () {
    $rootScope.disable_flg = true;
    $rootScope.display_flg = true;
    $("#tab_display").addClass("active")
  }

  $rootScope.confirmFunc = function () {
    if (!$rootScope.disable_flg) {
      return confirm("Is the input contents discarded ?");
    } else {
      return true;
    }
  }

  $scope.getJournalInfo = function () {
    if (!$rootScope.index_id_q) {
      return;
    }
    // request api
    $http({
      method: 'GET',
      url: '/journal_info/' + $rootScope.index_id_q,
      //data: post_data,
      headers: { 'Content-Type': 'application/json' },
    }).then(function successCallback(response) {
      $rootScope.journal_info = response.data;
    }, function errorCallback(error) {
      console.log(error);
    });
  }
  $scope.getJournalInfo();

  // Get child id list.
  let child_list = []
  const currentTime = new Date().getTime();
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
  $scope.sort_index_list = function (data_list) {
    let temp_key_list = []
    $scope.sorted_child_list = []
    for (var i = 0; i < child_list.length; i++) {
      for (var j = 0; j < data_list.length; j++) {
        if (temp_key_list.indexOf(data_list[j].key) == -1 && child_list[i] == data_list[j].key.split('/').pop()) {
          temp_key_list.push(data_list[j].key);
          $scope.sorted_child_list.push(data_list[j]);
        }
      }
    }
  }

  //Get path and name to dict.
  $scope.getPathName = function () {
    let aggregations = $rootScope.vm.invenioSearchResults.aggregations || {};
    let path_str = "";
    if (aggregations.hasOwnProperty("path") && aggregations.path.hasOwnProperty("buckets") && aggregations.path.buckets[0] && aggregations.path.buckets[0][0]) {
      path_str = aggregations.path.buckets[0][0].key;
    }
    if (path_str) {
      path_str = path_str.replace(/\//g, '_');
    } else {
      return;
    }
    $http({
      method: 'GET',
      url: '/get_path_name_dict/' + path_str,
      headers: {'Content-Type': 'application/json'},
    }).then(function successCallback(response) {
      $rootScope.vm.invenioSearchResults.aggregations.path.buckets[0][0]['path_name_dict'] = response.data;
    }, function errorCallback(error) {
      console.log(error);
    });
  }

  // Check all records for restricted content
  $scope.$on('invenio.search.finished', function (evt) {
    $scope.getPathName();
    $rootScope.display_comment_jounal();
    if(window.location.pathname != '/' &&
      window.facetSearchFunctions && window.facetSearchFunctions.useFacetSearch()) {
        // Apply the search results to faceted items except for the first search result.
        let search = new URLSearchParams(window.location.search);
        if(search.get('search_type') == 2){
          window.facetSearchFunctions.resetFacetData(evt.targetScope.vm.invenioSearchResults.aggregations.aggregations[0]);
        }else {
          window.facetSearchFunctions.resetFacetData(evt.targetScope.vm.invenioSearchResults.aggregations);
        }

    }
  });
}

// Item export controller
// Defined here because this feature is an extension of search
function itemExportCtrl($scope, $rootScope, $http, $location) {
  $rootScope.item_export_checkboxes = [];
  $rootScope.max_export_num = $("#max_export_num").val();
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

  $scope.checkAll = function (checkAll) {
    angular.forEach($scope.vm.invenioSearchResults.hits.hits, function (record) {
      item_index = $rootScope.item_export_checkboxes.indexOf(record.id);
      if (checkAll && item_index == -1) {
        $rootScope.item_export_checkboxes.push(record.id);
      } else if (!checkAll && item_index >= 0) {
        $rootScope.item_export_checkboxes.splice(item_index, 1);
      }
    });
  }

  $scope.checkAllExportItems = function (event) {
    if (event.target.checked) {
      $scope.checkAll(true);
      $rootScope.check_all = true;
    }
    else {
      $scope.checkAll(false);
      $rootScope.check_all = false;
    }
  }

  $scope.checkExportItem = function (record_id) {
    item_index = $rootScope.item_export_checkboxes.indexOf(record_id);
    if (item_index == -1) {
      $rootScope.item_export_checkboxes.push(record_id);
      $rootScope.check_all = $scope.checkIfAllInArray() ? true : false;
    }
    else {
      $rootScope.item_export_checkboxes.splice(item_index, 1);
      $rootScope.check_all = false;
    }
  }

  $scope.selectedExportFormat = "JSON";
  $scope.checkExportFormat = function () {
    if (!$scope.enableContentsExporting) {
      return;
    }
    if ($scope.selectedExportFormat === "ROCRATE") {
      $("input#export_file_contents_radio_on").prop("checked", true);
      $("input[name='export_file_contents_radio']").prop("disabled", true);
      $("<input>").attr({
        type: "hidden",
        name: "export_file_contents_radio",
        value: "True"
      }).appendTo($("form#export_items_form"));
    } else {
      $("input[name='export_file_contents_radio']").prop("disabled", false);
      $("input[name='export_file_contents_radio']:hidden").remove();
    }
  }

  $scope.exportItems = function () {
    if ($rootScope.item_export_checkboxes.length <= $rootScope.max_export_num) {
      records_metadata = $scope.getExportItemsMetadata();
      $('#record_ids').val(JSON.stringify($rootScope.item_export_checkboxes));
      $('#invalid_record_ids').val(JSON.stringify([]));
      let export_metadata = {}
      $rootScope.item_export_checkboxes.map(function(recid) {
        $.each(records_metadata, function (index, value) {
          if (value.id === recid) {
            export_metadata[recid] = value;
          }
        });
      })
      let exportBibtex = document.getElementById("export_format_radio_bibtex").checked
      if (exportBibtex) {
        let invalidBibtexRecordIds = $scope.validateBibtexExport(Object.keys(export_metadata));
        if (invalidBibtexRecordIds.length > 0) {
          $('#invalid_record_ids').val(JSON.stringify(invalidBibtexRecordIds));
          $scope.showErrMsgBibtex(invalidBibtexRecordIds);
        }
      }
      if ($scope.selectedExportFormat !== "ROCRATE") {
        $('#record_metadata').val(JSON.stringify(export_metadata));
      } else {
        $('#record_metadata').val("");
      }
      $('#export_items_form').submit();  // Submit form and let controller handle file making
    }
    $('#item_export_button').attr("disabled", false);
  }

  $scope.validateBibtexExport = function (record_ids) {
    var request_url = '/items/validate_bibtext_export';
    var data = { record_ids: record_ids }
    var invalidRecordIds = []
    $.ajax({
      method: 'POST',
      url: request_url,
      data: JSON.stringify(data),
      async: false,
      contentType: 'application/json',
      success: function (data) {
        if (data.invalid_record_ids.length) {
          invalidRecordIds = data.invalid_record_ids;
        }
      },
      error: function (status, error) {
        console.log(error);
      }
    });
    return invalidRecordIds;
  }

  $scope.showErrMsgBibtex = function (invalidRecordIds) {
    var errMsg = getMessage('bibtex_err');
    invalidRecordIds.forEach(function (recordId) {
      document.getElementById('bibtex_err_' + recordId).textContent=errMsg;
    });
  }

  $scope.getExportItemsMetadata = function () {
    let cur_url = new URL(window.location.href);
    let q = cur_url.searchParams.get("q");
    let search_type = cur_url.searchParams.get("search_type");
    const currentTime = new Date().getTime();
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
      success: function (data, status) {
        search_results = data.hits.hits;
      },
      error: function (status, error) {
        console.log(error);
      }
    });

    return search_results;
  }

  $scope.checkForRestrictedContent = function (record_id) {
    record_ids = [];
    angular.forEach($scope.vm.invenioSearchResults.hits.hits, function (record) {
      record_ids.push(record.id);
    });

    $http({
      method: 'POST',
      url: '/api/items/check_restricted_content',
      data: { 'record_ids': record_ids },
      headers: { 'Content-Type': 'application/json' },
    }).then(function successCallback(response) {
      $rootScope.items_with_restricted_content = response.data.restricted_records;
    }, function errorCallback(response) {
      $rootScope.items_with_restricted_content = [];
      console.log('ERROR: Unable to check for restricted items.'); // TODO: Do something useful
    });
  }

  // Check all records for restricted content
  $scope.$on('invenio.search.finished', function (evt) {
    $scope.checkForRestrictedContent();
    if ($scope.checkIfAllInArray()) {
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
  .filter("sanitize", ['$sce', function ($sce) {
    return function (htmlCode) {
      return $sce.trustAsHtml(htmlCode);
    }
  }])
  .filter("escapeTitle", function () {
    return function (data) {
      if (data){
        data = escapeString(data);
      }
      return data;
    }
  })
  .filter("escapeAuthor", function () {
    return function (authorData) {
      let tmpAuthorData = JSON.parse(JSON.stringify(authorData))
      return escapeAuthorString(tmpAuthorData);
    }
  });

function escapeAuthorString(data) {
  if (Array.isArray(data) && data.length > 0) {
    for (let i = 0; i < data.length; i++) {
      data[i] = escapeAuthorString(data[i]);
    }
  } else if (typeof data === 'object') {
    Object.keys(data).forEach(function (key) {
      data[key] = escapeAuthorString(data[key]);
    })
  } else if (typeof data === 'string') {
    data = escapeString(data)
  }
  return data;
}

function escapeString(data) {
  data = data
    .replace(/(^(&EMPTY&,|,&EMPTY&)|(&EMPTY&,|,&EMPTY&)$|&EMPTY&)/g, "")
    .replace(/[\x00-\x1F\x7F]/g, "")
    .trim();
  return data === ',' ? '' : data;
}

function format_comment(comment) {
  let result = ""
  let href = ''
  let text = ''
  let where = 'href'
  let flat = false
  for (let i = 0; i < comment.length; i++) {
    let c = comment[i]
    if (c === '[') {
      if (comment[i + 1] === '[') {
        flat = true;
        i++
        continue
      }
    }
    if (c === ']') {
      if (flat === true && comment[i + 1] === ']') {
        flat = false
        text = text ? text : href
        result += '<a href="' + href + '" target="_blank">' + text + '</a>'
        text = ''
        href = ''
        where = 'href'
        i++

        continue
      }
    }
    if (flat) {
      if (c === '|' && where === 'href') {
        where = 'text'
        continue
      }
      if (where === 'text') {
        if (c == '\n') {
          text += "<br/>"
        } else {
          text += c
        }
      } else {
        if (c == '\n') {
          href += "<br/>"
        } else {
          href += c
        }
      }
    } else {
      if (c == '\n') {
        result += "<br/>"
      } else {
        result += c

      }
    }

  }
  if (text) {
    result += '<a href="' + href + '" target="_blank">' + text + '</a>'
  } else {
    if (href) {
      result += '<a href="' + href + '" target="_blank">' + href + '</a>'
    }
  }
  return result
}
// add by ryuu. at 20181129 end
