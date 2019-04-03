require([
  'jquery',
  'bootstrap'
], function () {
  $('#weko_id_hidden').hide();
  $("#item-type-lists").change(function (ev) {
    window.location.href = '/items/' + $(this).val();
  });
  $("#btnModalClose").click(function () {
    $('#myModal').modal('toggle');
    $("div.modal-backdrop").remove();
  });

});

// script for Contributor
var username = [];
var email = [];
var filter = {
  filter_username: "",
  filter_email: ''
}
function autocomplete(inp, arr) {
  var currentFocus;

  inp.addEventListener("input", function (e) {
    var a, b, i, val = this.value;
    var mode = this.id;
    var flag = false;
    closeAllLists();
    if (!val) {
      return false;
    }
    currentFocus = -1;
    a = document.createElement("DIV");
    a.setAttribute("id", this.id + "autocomplete-list");
    a.setAttribute("class", "autocomplete-items");
    this.parentNode.appendChild(a);

    /*for each item in the array...*/
    for (i = 0; i < arr.length; i++) {
      /*check if the item starts with the same letters as the text field value:*/
      if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
        /*create a DIV element for each matching element:*/
        b = document.createElement("DIV");
        /*make the matching letters bold:*/
        b.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
        b.innerHTML += arr[i].substr(val.length);
        /*insert a input field that will hold the current array item's value:*/
        b.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";

        /*execute a function when someone clicks on the item value (DIV element):*/
        b.addEventListener('click', function (e) {
          /*insert the value for the autocomplete text field:*/
          inp.value = this.getElementsByTagName("input")[0].value;
          if (mode == 'share_username') {
            filter.filter_username = inp.value;
            // get exact user info contains username and email by username unique
            get_autofill_data(filter.filter_username, "", mode);
          } else {
            if (mode == 'share_email') {
              filter.filter_email = inp.value;
              // get exact user info contains username and email by email
              get_autofill_data('', filter.filter_email, mode);
            }
          }
          closeAllLists();
        });

        a.appendChild(b);
        flag = true;
      }
    }
    if (flag == false) {
      if ($(".autocomplete-items div").length == 0) {
        b = document.createElement("DIV");
        b.innerHTML = "<p>No result found" + "</p>";
        b.innerHTML += "<input type='hidden' value='No results found'>";
        a.appendChild(b);
      }
    }
  });
  inp.addEventListener("keydown", function (e) {
    var x = document.getElementById(this.id + "autocomplete-list");
    if (x) {
      x = x.getElementsByTagName("div");
    }
    if (e.keyCode == 40) {
      /*If the arrow DOWN key is pressed,
      increase the currentFocus variable:*/
      currentFocus++;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 38) { //up
      /*If the arrow UP key is pressed,
      decrease the currentFocus variable:*/
      currentFocus--;
      /*and and make the current item more visible:*/
      addActive(x);
    } else if (e.keyCode == 13) {
      /*If the ENTER key is pressed, prevent the form from being submitted,*/
      e.preventDefault();
      if (currentFocus > -1) {
        /*and simulate a click on the "active" item:*/
        if (x) {
          x[currentFocus].click();
        }
      } else {
        if (currentFocus == -1 && $("#share_username").val() != '') {
          if (x) {
            x[0].click();
          }
        }
      }
    }
  });
  function addActive(x) {
    /*a function to classify an item as "active":*/
    if (!x) return false;
    /*start by removing the "active" class on all items:*/
    removeActive(x);
    if (currentFocus >= x.length) currentFocus = 0;
    if (currentFocus < 0) currentFocus = (x.length - 1);
    /*add class "autocomplete-active":*/
    x[currentFocus].classList.add("autocomplete-active");
  }
  function removeActive(x) {
    /*a function to remove the "active" class from all autocomplete items:*/
    for (var i = 0; i < x.length; i++) {
      x[i].classList.remove("autocomplete-active");
    }
  }

  function closeAllLists(elmnt) {
    /*close all autocomplete lists in the document,
    except the one passed as an argument:*/
    var x = document.getElementsByClassName("autocomplete-items");
    for (var i = 0; i < x.length; i++) {
      if (elmnt != x[i] && elmnt != inp) {
        x[i].parentNode.removeChild(x[i]);
      }
    }
  }

  /*execute a function when someone clicks in the document:*/
  document.addEventListener("click", function (e) {
    closeAllLists(e.target);
  });
}

get_search_data = function (keyword) {
  get_search_data_url = '/api/items/get_search_data/' + keyword;
  if (keyword == 'username') {
    $("#id_spinners_username").css("display", "");
  } else {
    if (keyword == 'email') {
      $("#id_spinners_email").css("display", "");
    }
  }

  $.ajax({
    url: get_search_data_url,
    method: "GET",
    success: function(data, status) {
      if (data.error) {
        alert("Some errors have occured!\nDetail:" + data.error);
        return null;
      } else {
        if (keyword === 'username') {
          $("#id_spinners_username").css("display", "none");
          $("#share_username").prop('readonly', false);
          username = data.results;
          // auto fill for username
          autocomplete(document.getElementById("share_username"), username);

        } else {
          if (keyword === 'email') {
            $("#id_spinners_email").css("display", "none");
            $("#share_email").prop('readonly', false);
            email = data.results;
            // auto fill for email input
            autocomplete(document.getElementById("share_email"), email);
          }
        }

        return data.results;
      }
    },
    error: function(data, status) {
      alert("Cannot connect to server!");
    }
  });
}

get_autofill_data = function (keyword, data, mode) {
  // If autofill, "keyword" = email or username, and username, email have to fill to "data"
  // If validate, keyword = username, data = email
  let param = {
    username: "",
    email: ""
  }
  if (keyword == "username") {
    param.username = data;
  } else if (keyword == "email") {
    param.email = data;
  } else {
    param.username = keyword;
    param.email = data;
  }

  //Create request
  $.ajax({
    url: "/api/items/validate_user_info",
    method: "POST",
    headers: {
      'Content-Type': 'application/json'
    },
    data: JSON.stringify(param),
    dataType: "json",
    success: function(data, status) {
      if (mode == 'share_username') {
        $("#share_email").val(data.results.email);
      } else {
        if (mode == 'share_email') {
          if (data.results.username) {
            $("#share_username").val(data.results.username);
          }
        }
      }
    },
    error: function(data, status) {
      alert("Cannot connect to server!");
    }
  });
}

$("#share_username").focusout(function () {
  username = [];
  $("#share_email").prop('readonly', true);

})

$("#share_email").focusout(function () {
  email = [];
  $("#share_username").prop('readonly', true);
})

function handleSharePermission(value) {
  if (value == 'this_user') {
    $(".form_share_permission").css('display', 'none');
    $("#share_username").val("");
    $("#share_email").val("");
  } else {
    if (value == 'other_user') {
      $(".form_share_permission").css('display', 'block');
      $("#share_username").val("");
      $("#share_email").val("");
      $("#id_spinners_username").css("display", "none");
      $("#share_username").prop('readonly', true);
      $("#id_spinners_email").css("display", "none");
      $("#share_email").prop('readonly', true);
    }
  }
}

(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function () {
    angular.module('wekoRecords.controllers', []);
    function WekoRecordsCtrl($scope, $rootScope, $modal, InvenioRecordsAPI) {
      //      $scope.items = [ 'item1', 'item2', 'item3' ];
      $scope.filemeta_key = '';
      $scope.filemeta_form_idx = -1;
      $scope.is_item_owner = false;
      $scope.searchFilemetaKey = function () {
        if ($scope.filemeta_key.length > 0) {
          return $scope.filemeta_key;
        }
        Object.entries($rootScope.recordsVM.invenioRecordsSchema.properties).forEach(
          ([key, value]) => {
            if (value.type == 'array') {
              if (value.items.properties.hasOwnProperty('filename')) {
                $scope.filemeta_key = key;
              }
            }
          }
        );
      }
      $scope.findFilemetaFormIdx = function () {
        if ($scope.filemeta_form_idx >= 0) {
          return $scope.filemeta_form_idx;
        }
        $rootScope.recordsVM.invenioRecordsForm.forEach(
          (element, index) => {
            if (element.hasOwnProperty('key')
              && element.key == $scope.filemeta_key) {
              $scope.filemeta_form_idx = index;
            }
          }
        );
      }
      $scope.initFilenameList = function () {
        $scope.searchFilemetaKey();
        $scope.findFilemetaFormIdx();
        filemeta_schema = $rootScope.recordsVM.invenioRecordsSchema.properties[$scope.filemeta_key];
        filemeta_schema.items.properties['filename']['enum'] = [];
        filemeta_form = $rootScope.recordsVM.invenioRecordsForm[$scope.filemeta_form_idx];
        filemeta_filename_form = filemeta_form.items[0];
        filemeta_filename_form['titleMap'] = [];
        $rootScope.filesVM.files.forEach(file => {
          if (file.completed) {
            filemeta_schema.items.properties['filename']['enum'].push(file.key);
            filemeta_filename_form['titleMap'].push({ name: file.key, value: file.key });
          }
        });
        $rootScope.$broadcast('schemaFormRedraw');
        // implement by hieu vo - 1/4/2019
        $("#contributor-panel").addClass("hidden");
        // Load Contributor information
        let recordModel = $rootScope.recordsVM.invenioRecordsModel;
        if (!recordModel.hasOwnProperty('shared_user_id')) {
          $("#contributor-panel").removeClass("hidden");
          $(".input_contributor").prop("checked", true);
          $("#share_username").val("");
          $("#share_email").val("");
        } else {
          if (recordModel.shared_user_id) {
            // Call rest api to get user information
            let owner_id = 0
            if (recordModel.owner) {
              owner_id = recordModel.owner;
            } 
            let get_user_url = '/api/items/get_user_info/' + owner_id + '/' + recordModel.shared_user_id;
            $.ajax({
              url: get_user_url,
              method: 'GET',
              success: function(data, stauts) {
                if (data.owner) {
                  $scope.is_item_owner = true;
                  $("#contributor-panel").removeClass("hidden");
                  $(".other_user_rad").click();
                  $("#share_username").val(data.username);
                  $("#share_email").val(data.email);
                }else {
                  if (owner_id == 0) {
                    $scope.is_item_owner = true;
                  }
                  $(".other_user_rad").click();
                  $("#share_username").val(data.username);
                  $("#share_email").val(data.email);
                }
              },
              error: function(data, status) {
                alert("Cannot connect to server!");
              }
            })
          } else {
            $("#contributor-panel").removeClass("hidden");
            $(".input_contributor").prop("checked", true);
            $("#share_username").val("");
            $("#share_email").val("");
          }
        }
        // implement by hieu vo - 1/4/2019
      }

      $rootScope.$on('invenio.records.loading.stop', function (ev) {
        $scope.initFilenameList();
        hide_endpoints = $('#hide_endpoints').text()
        if (hide_endpoints.length > 2) {
          endpoints = JSON.parse($('#hide_endpoints').text());
          if (endpoints.hasOwnProperty('bucket')) {
            $rootScope.$broadcast(
              'invenio.records.endpoints.updated', endpoints
            );
          }
        }
      });
      $rootScope.$on('invenio.uploader.upload.completed', function (ev) {
        $scope.initFilenameList();
      });
      $scope.$on('invenio.uploader.file.deleted', function (ev, f) {
        $scope.initFilenameList();
      });

      $scope.searchAuthor = function (model_id, arrayFlg, form) {
        // add by ryuu. start 20180410
        $("#btn_id").text(model_id);
        $("#array_flg").text(arrayFlg);
        $("#array_index").text(form.key[1]);
        // add by ryuu. end 20180410
        $('#myModal').modal('show');
      }
      // add by ryuu. start 20180410
      $scope.setAuthorInfo = function () {
        var authorInfo = $('#author_info').text();
        var arrayFlg = $('#array_flg').text();
        var modelId = $('#btn_id').text();
        var array_index = $('#array_index').text();
        var authorInfoObj = JSON.parse(authorInfo);
        var updateIndex = 0;
        if (arrayFlg == 'true') {
          //            $rootScope.recordsVM.invenioRecordsModel[modelId].push(authorInfoObj[0]);
          //              $rootScope.recordsVM.invenioRecordsModel[modelId][array_index]= authorInfoObj[0];
          //            2018/05/28 start
          var familyName = "";
          var givenName = "";
          if (authorInfoObj[0].hasOwnProperty('affiliation')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].affiliation = authorInfoObj[0].affiliation;
          }
          if (authorInfoObj[0].hasOwnProperty('creatorAlternatives')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].creatorAlternatives = authorInfoObj[0].creatorAlternatives;
          }

          if (authorInfoObj[0].hasOwnProperty('creatorNames')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].creatorNames = authorInfoObj[0].creatorNames;
          }

          if (authorInfoObj[0].hasOwnProperty('familyNames')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].familyNames = authorInfoObj[0].familyNames;
            if ($rootScope.recordsVM.invenioRecordsModel[modelId][array_index].familyNames.length == 1) {
              familyName = authorInfoObj[0].familyNames[0].familyName;
            }
          } else {
            $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].familyNames = { "familyName": "", "lang": "" };
          }
          if (authorInfoObj[0].hasOwnProperty('givenNames')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].givenNames = authorInfoObj[0].givenNames;
            if ($rootScope.recordsVM.invenioRecordsModel[modelId][array_index].givenNames.length == 1) {
              givenName = authorInfoObj[0].givenNames[0].givenName;
            }
          } else {
            $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].givenNames = { "givenName": "", "lang": "" };
          }

          if (authorInfoObj[0].hasOwnProperty('familyNames') && authorInfoObj[0].hasOwnProperty('givenNames')) {
            if (!authorInfoObj[0].hasOwnProperty('creatorNames')) {
              $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].creatorNames = [];
            }
            for (var i = 0; i < authorInfoObj[0].familyNames.length; i++) {
              var subCreatorName = { "creatorName": "", "lang": "" };
              subCreatorName.creatorName = authorInfoObj[0].familyNames[i].familyName + "　" + authorInfoObj[0].givenNames[i].givenName;
              subCreatorName.lang = authorInfoObj[0].familyNames[i].lang;
              $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].creatorNames.push(subCreatorName);
            }
          }

          if (authorInfoObj[0].hasOwnProperty('nameIdentifiers')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].nameIdentifiers = authorInfoObj[0].nameIdentifiers;
          }

          var weko_id = $('#weko_id').text();
          $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].weko_id = weko_id;
          $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].weko_id_hidden = weko_id;
          $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].authorLink = ['check'];
          //            2018/05/28 end
        } else {
          if (authorInfoObj[0].hasOwnProperty('affiliation')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId].affiliation = authorInfoObj[0].affiliation;
          }
          if (authorInfoObj[0].hasOwnProperty('creatorAlternatives')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId].creatorAlternatives = authorInfoObj[0].creatorAlternatives;
          }
          if (authorInfoObj[0].hasOwnProperty('creatorNames')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId].creatorNames = authorInfoObj[0].creatorNames;
          } else {
            $rootScope.recordsVM.invenioRecordsModel[modelId].creatorNames = {};
          }
          if (authorInfoObj[0].hasOwnProperty('familyNames')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId].familyNames = authorInfoObj[0].familyNames;
          } else {
            $rootScope.recordsVM.invenioRecordsModel[modelId].familyNames = {};
          }
          if (authorInfoObj[0].hasOwnProperty('givenNames')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId].givenNames = authorInfoObj[0].givenNames;
          } else {
            $rootScope.recordsVM.invenioRecordsModel[modelId].givenNames = {};
          }
          if (authorInfoObj[0].hasOwnProperty('nameIdentifiers')) {
            $rootScope.recordsVM.invenioRecordsModel[modelId].nameIdentifiers = authorInfoObj[0].nameIdentifiers;
          }

          var weko_id = $('#weko_id').text();
          $rootScope.recordsVM.invenioRecordsModel[modelId].weko_id = weko_id;
          $rootScope.recordsVM.invenioRecordsModel[modelId].weko_id_hidden = weko_id;
          $rootScope.recordsVM.invenioRecordsModel[modelId].authorLink = ['check'];

        }
        //画面にデータを設定する
        $("#btn_id").text('');
        $("#author_info").text('');
        $("#array_flg").text('');
      }
      // add by ryuu. end 20180410
      $scope.updated = function (model_id, modelValue, form, arrayFlg) {
        //        2018/05/28 start

        if (arrayFlg) {
          var array_index = form.key[1];
          if (modelValue == true) {
            $rootScope.recordsVM.invenioRecordsModel[model_id][array_index].weko_id = $rootScope.recordsVM.invenioRecordsModel[model_id][array_index].weko_id_hidden;
          } else {
            delete $rootScope.recordsVM.invenioRecordsModel[model_id][array_index].weko_id;
          }
        } else {
          if (modelValue == true) {
            $rootScope.recordsVM.invenioRecordsModel[model_id].weko_id = $rootScope.recordsVM.invenioRecordsModel[model_id].weko_id_hidden;
          } else {
            delete $rootScope.recordsVM.invenioRecordsModel[model_id].weko_id;
          }
        }
        //        2018/05/28 end
      }
      //    authorLink condition
      $scope.linkCondition = function (val) {
        var linkStus = val.hasOwnProperty('authorLink');
        if (linkStus) {
          return true;
        } else {
          return false;
        }
      }
      //    authorId condition
      $scope.idCondition = function (val) {
        var c = val.hasOwnProperty('authorLink');
        if (!c) {
          return false;
        } else {
          return true;
        }
      }

      $scope.registerUserPermission = function () {
        // let userSelection = $('#input').val();
        let userSelection = $(".form_share_permission").css('display');
        let result = false;
        if (userSelection == 'none') {
          return;
        } else if (userSelection == 'block') {
          let _username = $('#share_username').val();
          let _email = $('#share_email').val();
          let current_login_user = 0;
          // Get current login user
          $.ajax({
            url: '/api/items/get_current_login_user_id',
            method: 'GET',
            async: false,
            success: function(data, status) {
              if (data.user_id){
                current_login_user = data.user_id;
              }
            }
          });
          let param = {
            username: _username,
            email: _email
          };
          $.ajax({
            url: '/api/items/validate_user_info',
            headers: {
              'Content-Type': 'application/json'
            },
            method: 'POST',
            async: false,
            data: JSON.stringify(param),
            dataType: "json",
            success: function(data, stauts) {
              if (data.error) {
                alert('Some errors have occured!\nDetail: ' + data.error);
              } else {
                if (data.validation) {
                  userInfo = data.results;
                  let otherUser = {
                    username: userInfo.username,
                    email: userInfo.email,
                    userID: userInfo.user_id
                  };
                  if (otherUser.userID == current_login_user) {
                    alert('You cannot specify yourself in "Other users" setting.');
                  }else {
                    $rootScope.recordsVM.invenioRecordsModel['shared_user_id'] = otherUser.userID;
                    result = true;
                  }
                } else {
                  alert('Shared user information is not valid\nPlease check it again!');
                }
              }
            },
            error: function(data, status) {
              alert('Cannot connect to server!');
            }
          })
        } else {
          alert('Some errors have occured when edit Contributer');
        }
        return result;
      }

      $scope.updateDataJson = async function () {
        if ($scope.is_item_owner) {
          if (!this.registerUserPermission()) {
            // Do nothing
          } else {
            var str = JSON.stringify($rootScope.recordsVM.invenioRecordsModel);
            var indexOfLink = str.indexOf("authorLink");
            if (indexOfLink != -1) {
              str = str.split(',"authorLink":[]').join('');
            }
            $rootScope.recordsVM.invenioRecordsModel = JSON.parse(str);
            // $rootScope.recordsVM.actionHandler(['index', 'PUT'], 'r');
          }
        } else {
          var str = JSON.stringify($rootScope.recordsVM.invenioRecordsModel);
          var indexOfLink = str.indexOf("authorLink");
          if (indexOfLink != -1) {
            str = str.split(',"authorLink":[]').join('');
          }
          $rootScope.recordsVM.invenioRecordsModel = JSON.parse(str);
          // $rootScope.recordsVM.actionHandler(['index', 'PUT'], 'r');
        }
      }
      $scope.saveDataJson = function (item_save_uri) {
        if ($scope.is_item_owner) {
          if (!this.registerUserPermission()) {
            // Do nothing
          } else {
            this.saveDataJsonCallback(item_save_uri);
          }
        }else {
          this.saveDataJsonCallback(item_save_uri);
        }
        
      }
      $scope.saveDataJsonCallback = function(item_save_uri) {
        var metainfo = { 'metainfo': $rootScope.recordsVM.invenioRecordsModel };
        if (!angular.isUndefined($rootScope.filesVM)) {
          metainfo = angular.merge(
            {},
            metainfo,
            {
              'files': $rootScope.filesVM.files,
              'endpoints': $rootScope.filesVM.invenioFilesEndpoints
            }
          );
        }
        var request = {
          url: item_save_uri,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          data: JSON.stringify(metainfo)
        };
        InvenioRecordsAPI.request(request).then(
          function success(response) {
            alert(response.data.msg);
          },
          function error(response) {
            alert(response);
          }
        );
      }
    }
    // Inject depedencies
    WekoRecordsCtrl.$inject = [
      '$scope',
      '$rootScope',
      '$modal',
      'InvenioRecordsAPI',
    ];
    angular.module('wekoRecords.controllers')
      .controller('WekoRecordsCtrl', WekoRecordsCtrl);

    var ModalInstanceCtrl = function ($scope, $modalInstance, items) {
      $scope.items = items;
      $scope.searchKey = '';
      $scope.selected = {
        item: $scope.items[0]
      };
      $scope.ok = function () {
        $modalInstance.close($scope.selected);
      };
      $scope.cancel = function () {
        $modalInstance.dismiss('cancel');
      };
      $scope.search = function () {
        $scope.items.push($scope.searchKey);
      }
    };

    angular.module('wekoRecords', [
      'invenioRecords',
      'wekoRecords.controllers',
    ]);

    angular.bootstrap(
      document.getElementById('weko-records'), [
        'wekoRecords', 'invenioRecords', 'schemaForm', 'mgcrea.ngStrap',
        'mgcrea.ngStrap.modal', 'pascalprecht.translate', 'ui.sortable',
        'ui.select', 'mgcrea.ngStrap.select', 'mgcrea.ngStrap.datepicker',
        'mgcrea.ngStrap.helpers.dateParser', 'mgcrea.ngStrap.tooltip',
        'invenioFiles'
      ]
    );
  });
})(angular);
