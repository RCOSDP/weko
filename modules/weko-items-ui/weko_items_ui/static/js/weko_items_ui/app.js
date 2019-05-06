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

  $("#meta-search-close").click(function () {
    $('#meta-search').modal('toggle');
    $("div.modal-backdrop").remove();
  });

});

// script for Contributor
var username_arr = [];
var email_arr = [];
var filter = {
  filter_username: "",
  filter_email: ''
}
function autocomplete(inp, arr) {
  var currentFocus;

  inp.addEventListener("input", function (e) {
    var form_share_other_user, droplist_show_other_user, i, val = this.value;
    var mode = this.id;
    var flag = false;
    closeAllLists();
    if (!val) {
      return false;
    }
    currentFocus = -1;
    form_share_other_user = document.createElement("DIV");
    form_share_other_user.setAttribute("id", this.id + "autocomplete-list");
    form_share_other_user.setAttribute("class", "autocomplete-items");
    this.parentNode.appendChild(form_share_other_user);

    /*for each item in the array...*/
    for (i = 0; i < arr.length; i++) {
      /*check if the item starts with the same letters as the text field value:*/
      if (arr[i].substr(0, val.length).toUpperCase() == val.toUpperCase()) {
        /*create a DIV element for each matching element:*/
        droplist_show_other_user = document.createElement("DIV");
        /*make the matching letters bold:*/
        droplist_show_other_user.innerHTML = "<strong>" + arr[i].substr(0, val.length) + "</strong>";
        droplist_show_other_user.innerHTML += arr[i].substr(val.length);
        /*insert a input field that will hold the current array item's value:*/
        droplist_show_other_user.innerHTML += "<input type='hidden' value='" + arr[i] + "'>";

        /*execute a function when someone clicks on the item value (DIV element):*/
        droplist_show_other_user.addEventListener('click', function (e) {
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

        form_share_other_user.appendChild(droplist_show_other_user);
        flag = true;
      }
    }
    if (flag == false) {
      if ($(".autocomplete-items div").length == 0) {
        droplist_show_other_user = document.createElement("DIV");
        droplist_show_other_user.innerHTML = "<p>No result found" + "</p>";
        droplist_show_other_user.innerHTML += "<input type='hidden' value='No results found'>";
        form_share_other_user.appendChild(droplist_show_other_user);
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
    $("#share_username").prop('readonly', true);
    $("#id_spinners_username").css("display", "");
  } else {
    if (keyword == 'email') {
      $("#share_email").prop('readonly', true);
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
          username_arr = data.results;
          // auto fill for username
          autocomplete(document.getElementById("share_username"), username_arr);

        } else {
          if (keyword === 'email') {
            $("#id_spinners_email").css("display", "none");
            $("#share_email").prop('readonly', false);
            email_arr = data.results;
            // auto fill for email input
            autocomplete(document.getElementById("share_email"), email_arr);
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
          }else {
            $("#share_username").val("");
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
  username_arr = [];
  $("#share_email").prop('readonly', true);

})

$("#share_email").focusout(function () {
  email_arr = [];
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
        
      }
      $scope.initContributorData = function() {
        $("#contributor-panel").addClass("hidden");
        // Load Contributor information
        let recordModel = $rootScope.recordsVM.invenioRecordsModel;
        let owner_id = 0
            if (recordModel.owner) {
              owner_id = recordModel.owner;
            } else {
              $scope.is_item_owner = true;
            }
        if (!recordModel.hasOwnProperty('shared_user_id')) {
          $("#contributor-panel").removeClass("hidden");
          $(".input_contributor").prop("checked", true);
          $("#share_username").val("");
          $("#share_email").val("");
          // Apply for run feature when Display Workflow is error.
          // When Display Workflow is fixed, please remove this
          $scope.is_item_owner = true;
          // ----
        } else {
          if (recordModel.shared_user_id && recordModel.shared_user_id != -1) {
            // Call rest api to get user information
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
                  $(".other_user_rad").click();
                  $("#share_username").val(data.username);
                  $("#share_email").val(data.email);
                }
              },
              error: function(data, status) {
                alert("Cannot connect to server!");
              }
            });
          } else {
            $("#contributor-panel").removeClass("hidden");
            $(".input_contributor").prop("checked", true);
            $("#share_username").val("");
            $("#share_email").val("");
            // Apply for run feature when Display Workflow is error.
            // When Display Workflow is fixed, please remove this
            $scope.is_item_owner = true;
            // ----
          }
        }
      }

      $rootScope.$on('invenio.records.loading.stop', function (ev) {
        $scope.initContributorData();
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

      $scope.getItemMetadata = function () {
        // Reset error message befor open modal.
        this.resetAutoFillErrorMessage();
        $('#meta-search').modal('show');
      }

      $scope.setValueToField = function (id, value) {
        if (!id) {
          return;
        } else if (!$scope.depositionForm[id]) {
          return;
        }

        if (!value) {
          // Reset current value
          $scope.depositionForm[id].$setViewValue("");
          $scope.depositionForm[id].$render();
          $scope.depositionForm[id].$commitViewValue();
          return;
        }
        $scope.depositionForm[id].$setViewValue(value);
        $scope.depositionForm[id].$render();
        $scope.depositionForm[id].$commitViewValue();
      }

      $scope.getAutoFillValue = function (data) {
        if (data) {
          return data;
        } else {
          return "";
        }
      }

      $scope.setAutoFillErrorMessage = function (message) {
        $("#autofill-error-message").text(message);
        $("#auto-fill-error-div").addClass("alert alert-danger");
      }

      $scope.resetAutoFillErrorMessage = function () {
        $("#autofill-error-message").text("");
        $("#auto-fill-error-div").removeClass("alert alert-danger");
      }

      $scope.dictValue = function (id, sub1 = null, sub2 = null, sub3 = null) {
        if (!id) {
          return null;
        }
        if (sub1) {
          if (id.hasOwnProperty(sub1)) {
            if (!sub2 && !sub3) {
              return id[sub1];
            }
            else if (sub2 && !sub3) {
              if (id[sub1].hasOwnProperty(sub2)) {
                return id[sub1][sub2];
              }
            } else if (sub2 && sub3) {
              if (id[sub1].hasOwnProperty(sub2)) {
                if (id[sub1][sub2].hasOwnProperty(sub3)) {
                  return id[sub1][sub2][sub3];
                }
              }
            }
          }
        }
        return null;
      }

      $scope.setItemMetadata = function () {
        let autoFillID = $('#autofill_id_type').val();
        let value = $('#autofill_item_id').val();
        let itemTypeId = $("#autofill_item_type_id").val();
        if (autoFillID === 'Default') {
          this.setAutoFillErrorMessage($("#autofill_error_id").val());
          return;
        } else if (!value.length) {
          this.setAutoFillErrorMessage($("#autofill_error_input_value").val());
          return;
        }

        let param = {
          api_type: autoFillID,
          search_data: $.trim(value),
          item_type_id: itemTypeId
        }
        this.setItemMetadataFromApi(param);
      }

      $scope.clearAllField = function() {
        for (var property in $scope.depositionForm) {
          if ($scope.depositionForm.hasOwnProperty(property)) {
            if (property.indexOf("item") != -1) {
              this.setValueToField(property, "");
            }
            if(typeof($scope.depositionForm[property]) == "object" && $scope.depositionForm[property].hasOwnProperty("$dateValue")) {
              $scope.depositionForm[property].$dateValue = null;
            }
          }
        }
      }

      $scope.setItemMetadataFromApi = function (param) {
        $.ajax({
          url: '/api/autofill/get_items_autofill_data',
          headers: {
            'Content-Type': 'application/json'
          },
          method: "POST",
          data: JSON.stringify(param),
          dataType: "json",
          success: (data, status) => {
            if (data.error) {
              this.setAutoFillErrorMessage("An error have occurred!\nDetail: " + data.error);
            } else {
              let items = data.items;
              if (!items) {
                this.setAutoFillErrorMessage('Some error is occurs!');
              }
              let result = data.result;
              if (!result) {
                this.setAutoFillErrorMessage($("#autofill_error_doi").val());
              } else {
                // Reset all fields
                this.clearAllField();
                // Reset error message
                this.resetAutoFillErrorMessage();

                this.setItemMetadataCreator(items, result);

                if (items.hasOwnProperty('numPages')) {
                  this.setValueToField(this.dictValue(items.numPages, '@value'), this.getAutoFillValue(this.dictValue(result.numPages, '@value')));
                }

                if (items.hasOwnProperty('pageStart')) {
                  this.setValueToField(this.dictValue(items.pageStart, '@value'), this.getAutoFillValue(this.dictValue(result.pageStart, '@value')));
                }

                if (items.hasOwnProperty('pageEnd')) {
                  this.setValueToField(this.dictValue(items.pageEnd, '@value'), this.getAutoFillValue(this.dictValue(result.pageEnd, '@value')));
                }

                if (items.hasOwnProperty('publisher')) {
                  let id = items.publisher;
                  let resultId = result.publisher;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
                    this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                    this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
                  }
                }

                this.setItemMetadataRelation(items, result);

                if (items.hasOwnProperty('contributor')) {
                  let contributor = items.contributor;
                  let resultId = result.contributor;
                  if (contributor.hasOwnProperty('contributorName')) {
                    let id = contributor.contributorName;
                    let subResultId = resultId.contributorName;
                    if (subResultId && subResultId['@value']) {
                      this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(subResultId, '@attributes', 'xml:lang')));
                      this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subResultId, '@value')));
                    } else {
                      this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
                      this.setValueToField(this.dictValue(id, '@value'), "");
                    }
                  }
                }

                if (items.hasOwnProperty('subject')) {
                  let subject = items.subject;
                  let resultId = result.subject;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(subject, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
                    this.setValueToField(this.dictValue(subject, '@attributes', 'subjectScheme'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'subjectScheme')));
                    this.setValueToField(this.dictValue(subject, '@attributes', 'subjectURI'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'subjectURI')));
                    this.setValueToField(this.dictValue(subject, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(subject, '@attributes', 'xml:lang'), "");
                    this.setValueToField(this.dictValue(subject, '@value'), "");
                    this.setValueToField(this.dictValue(subject, '@attributes', 'subjectScheme'), "");
                    this.setValueToField(this.dictValue(subject, '@attributes', 'subjectURI'), "");
                  }
                }

                if (items.hasOwnProperty('description')) {
                  let description = items.description;
                  let resultId = result.description;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(description, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
                    this.setValueToField(this.dictValue(description, '@attributes', 'descriptionType'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'descriptionType')));
                    this.setValueToField(this.dictValue(description, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(description, '@attributes', 'xml:lang'), "");
                    this.setValueToField(this.dictValue(description, '@value'), "");
                    this.setValueToField(this.dictValue(description, '@attributes', 'descriptionType'), "");
                  }
                }

                if (items.hasOwnProperty('sourceTitle')) {
                  let sourceTitle = items.sourceTitle;
                  let resultId = result.sourceTitle;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(sourceTitle, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
                    this.setValueToField(this.dictValue(sourceTitle, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(sourceTitle, '@attributes', 'xml:lang'), "");
                    this.setValueToField(this.dictValue(sourceTitle, '@value'), "");
                  }
                }

                if (items.hasOwnProperty('volume')) {
                  let volume = items.volume;
                  let resultId = result.volume;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(volume, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(volume, '@value'), "");
                  }
                }

                if (items.hasOwnProperty('issue')) {
                  let issue = items.issue;
                  let resultId = result.issue;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(issue, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(issue, '@value'), "");
                  }
                }

                if (items.hasOwnProperty('sourceIdentifier')) {
                  let sourceIdentifier = items.sourceIdentifier;
                  let resultId = result.sourceIdentifier;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(sourceIdentifier, '@attributes', 'identifierType'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'identifierType')));
                    this.setValueToField(this.dictValue(sourceIdentifier, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(sourceIdentifier, '@attributes', 'identifierType'), "");
                    this.setValueToField(this.dictValue(sourceIdentifier, '@value'), "");
                  }
                }
        
                if (items.hasOwnProperty('title')) {
                  let id = items.title;
                  let resultId = result.title;
                  if (Array.isArray(id))
                  {
                    for(var i = 0 ; i < id.length;i++)
                    {
                      if (id[i].hasOwnProperty('title'))
                      {
                        let sub_id= id[i].title;
                        let sub_resultId = resultId[i].title;
                        if(sub_resultId && sub_resultId['@value'])
                        {
                          this.setValueToField(this.dictValue(sub_id, '@value'), this.getAutoFillValue(this.dictValue(sub_resultId, '@value')));
                          this.setValueToField(this.dictValue(sub_id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(sub_resultId, '@attributes', 'xml:lang')));
                          $rootScope.recordsVM.invenioRecordsModel['title'] = this.getAutoFillValue(this.dictValue(sub_resultId, '@value'));
                          $rootScope.recordsVM.invenioRecordsModel['lang'] = this.getAutoFillValue(this.dictValue(sub_resultId, '@attributes', 'xml:lang'));
                          break;
                        }
                        else
                        {
                          this.setValueToField(this.dictValue(sub_id, '@value'), "");
                          this.setValueToField(this.dictValue(sub_id, '@attributes', 'xml:lang'), "");
                        }
                      }
                    }
                  }
                  else
                  {
                    if (resultId && resultId['@value']) {
                      this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
                      this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                      $rootScope.recordsVM.invenioRecordsModel['title'] = this.getAutoFillValue(this.dictValue(resultId, '@value'));
                      $rootScope.recordsVM.invenioRecordsModel['lang'] = this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang'));
                    } else {
                      this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                      $rootScope.recordsVM.invenioRecordsModel['title'] = this.getAutoFillValue(this.dictValue(resultId, '@value'));
                      this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
                    }
                  }
                }

                if (items.hasOwnProperty('date'))
                {
                  let id = items.date;
                  let resultId = result.date;
                  if(Array.isArray(id))
                  {
                    for(var i = 0 ; i < id.length;i++)
                    {
                      let sub_id= id[i].date;
                      let sub_resultId = resultId[i].date;
                      if(sub_resultId && sub_resultId['@value'])
                      {
                        this.setValueToField(this.dictValue(sub_id, '@value'), this.getAutoFillValue(this.dictValue(sub_resultId, '@value')));
                        this.setValueToField(this.dictValue(sub_id, '@attributes', 'dateType'), this.getAutoFillValue(this.dictValue(sub_resultId, '@attributes', 'dateType')));
                        break;
                      }
                      else
                      {
                        this.setValueToField(this.dictValue(sub_id, '@value'), "");
                        this.setValueToField(this.dictValue(sub_id, '@attributes', 'dateType'), "");
                      }
                    }
                  }
                  else
                  {
                    if(resultId && resultId['@value'])
                      {
                        this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                        this.setValueToField(this.dictValue(id, '@attributes', 'dateType'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'dateType')));
                      }
                      else
                      {
                        this.setValueToField(this.dictValue(id, '@value'), "");
                        this.setValueToField(this.dictValue(id, '@attributes', 'dateType'), "");
                      }
                  }
                }

                if (param.api_type == 'CrossRef') {
                  this.setItemMetadataCrossRef(items, result);
                }
                else if (param.api_type == 'CiNii') {
                  this.setItemMetadataCiNii(items, result);
                }

                $('#meta-search').modal('toggle');
              }
            }
          },
          error: (data, status) => {
            this.setAutoFillErrorMessage("Cannot connect to server!");
          }
        });
      }

      $scope.setItemMetadataCrossRef = function (items, result) {
        if (items.hasOwnProperty('language'))
                {
                  let id = items.language;
                  let resultId = result.language;
                  if(Array.isArray(id))
                  {
                    for(var i = 0 ; i < id.length;i++)
                    {
                      let sub_id= id[i].language;
                      let sub_resultId = resultId[i].language;
                      if(sub_resultId && sub_resultId['@value'])
                      {
                        this.setValueToField(this.dictValue(sub_id, '@value'), this.getAutoFillValue(this.dictValue(sub_resultId, '@value')));
                      }
                      else
                      {
                        this.setValueToField(this.dictValue(sub_id, '@value'), "");
                      }
                    }
                  }
                  else
                  {
                    if(resultId && resultId['@value'])
                    {
                      this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                    }
                    else
                    {
                      this.setValueToField(this.dictValue(id, '@value'), "");
                    }
                  }
                }
      }

      $scope.setItemMetadataCiNii = function (items, result) {
        if (items.hasOwnProperty('alternative')) {
          let id, resultId;
          id = items.alternative;
          resultId = result.alternative;
          if (this.getAutoFillValue(this.dictValue(resultId, '@value'))) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
            this.setValueToField(this.dictValue(id, '@value'), "");
          }
        }
      }

      $scope.setItemMetadataCreator = function (items, result) {
        if (!items.hasOwnProperty('creator')) {
          return;
        }
        if (items.creator.hasOwnProperty('affiliation')) {
          if (items.creator.affiliation.hasOwnProperty('affiliationName')) {
            let id = items.creator.affiliation.affiliationName;
            let resultId = result.creator.affiliation.affiliationName;
            if (resultId && resultId['@value']) {
              this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            } else {
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
              this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
            }
          }

          if (items.creator.affiliation.hasOwnProperty('nameIdentifier')) {
            let id = items.creator.affiliation.nameIdentifier;
            let resultId = result.creator.affiliation.nameIdentifier;
            this.setValueToField(this.dictValue(id, '@attributes', 'nameIdentifierScheme'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'nameIdentifierScheme')));
            this.setValueToField(this.dictValue(id, '@attributes', 'nameIdentifierURI'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'nameIdentifierURI')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(resultId['@value']));
          }
        }

        if (items.creator.hasOwnProperty('creatorAlternative')) {
          let id = items.creator.creatorAlternative;
          let resultId = result.creator.creatorAlternative;
          if (resultId && resultId['@value']) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
          }
        }

        if (items.creator.hasOwnProperty('creatorName')) {
          let id = items.creator.creatorName;
          let resultId = result.creator.creatorName;
          if (resultId && resultId['@value']) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
          }
        }

        if (items.creator.hasOwnProperty('familyName')) {
          let id = items.creator.familyName;
          let resultId = result.creator.familyName;
          if (resultId && resultId['@value']) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
          }
        }

        if (items.creator.hasOwnProperty('givenName')) {
          let id = items.creator.givenName;
          let resultId = result.creator.givenName;
          if (resultId && resultId['@value']) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
          }
        }

        if (items.creator.hasOwnProperty('nameIdentifier')) {
          let id = items.creator.nameIdentifier;
          let resultId = result.creator.nameIdentifier;
          this.setValueToField(this.dictValue(id, '@attributes', 'nameIdentifierScheme'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'nameIdentifierScheme')));
          this.setValueToField(this.dictValue(id, '@attributes', 'nameIdentifierURI'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'nameIdentifierURI')));
          this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
        }
      }

      $scope.setItemMetadataRelation = function (items, result) {
        if (items.hasOwnProperty('relation')) {
          let relation = items.relation;
          let resultId = result.relation;
          this.setValueToField(this.dictValue(relation, '@attributes', 'relationType'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'relationType')));
          if (relation.hasOwnProperty('relatedIdentifier')) {
            let id = relation.relatedIdentifier;
            let subresultId = resultId.relatedIdentifier;
            if (subresultId && subresultId['@value']) {
              this.setValueToField(this.dictValue(id, '@attributes', 'identifierType'), this.getAutoFillValue(this.dictValue(subresultId, '@attributes', 'identifierType')));
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subresultId, '@value')));
            } else {
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subresultId, '@value')));
              this.setValueToField(this.dictValue(id, '@attributes', 'identifierType'), "");
            }
          }

          if (relation.hasOwnProperty('relatedTitle')) {
            let id = relation.relatedTitle;
            let subresultId = resultId.relatedTitle;
            if (subresultId && subresultId['@value']) {
              this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(subresultId, '@attributes', 'xml:lang')));
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subresultId, '@value')));
            } else {
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subresultId, '@value')));
              this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
            }
          }
        }
      }

      $scope.searchSource = function(model_id,arrayFlg,form) {

        alert(form.key[1]);

      }


      $scope.searchAuthor = function(model_id,arrayFlg,form) {
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
          $rootScope.recordsVM.invenioRecordsModel['shared_user_id'] = -1;
          result = true;
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

      $scope.genTitleAndPubDate = function() {
        let itemTypeId = $("#autofill_item_type_id").val();
        let get_url = '/api/autofill/get_title_pubdate_id/'+itemTypeId;
        $.ajax({
          url: get_url,
          method: 'GET',
          async: false,
          success: (data, status) => {
            let title = "";
            let lang = "en";
            let titleID = data.title;
            if ($rootScope.recordsVM.invenioRecordsModel.hasOwnProperty(titleID[0])){
              let titleField = $rootScope.recordsVM.invenioRecordsModel[titleID[0]];
              if (typeof(titleField) == 'array') {
                titleField = titleField[0];
                if (titleField[0].hasOwnProperty(titleID[1])){
                  titleField = titleField[0];
                }
              }
              if (titleField.hasOwnProperty(titleID[1])) {
                title = titleField[titleID[1]];
                if (titleField.hasOwnProperty(titleID[2]) && titleField[titleID[2]]) {
                  lang = titleField[titleID[2]]
                }
              }
            }
            if (!$rootScope.recordsVM.invenioRecordsModel['title']){
              $rootScope.recordsVM.invenioRecordsModel['title'] = title;
              $rootScope.recordsVM.invenioRecordsModel['lang'] = lang;
            }else {
              if (title != "") {
                $rootScope.recordsVM.invenioRecordsModel['title'] = title;
                $rootScope.recordsVM.invenioRecordsModel['lang'] = lang;
              }
            }
          },
          error: function(data, status) {
            alert('Cannot connect to server!');
          }
        });
      }

      $scope.updateDataJson = async function () {
        this.genTitleAndPubDate();
        if (!$rootScope.recordsVM.invenioRecordsModel['title']) {
          alert('Title is required! Please input title');
        }else if (!$rootScope.recordsVM.invenioRecordsModel['pubdate']){
          alert('PubDate is required! Please input pubDate');
        }
        else {
          let next_frame = $('#next-frame').val();
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
              $rootScope.recordsVM.actionHandler(['index', 'PUT'], next_frame);
            }
          } else {
            var str = JSON.stringify($rootScope.recordsVM.invenioRecordsModel);
            var indexOfLink = str.indexOf("authorLink");
            if (indexOfLink != -1) {
              str = str.split(',"authorLink":[]').join('');
            }
            $rootScope.recordsVM.invenioRecordsModel = JSON.parse(str);
            $rootScope.recordsVM.actionHandler(['index', 'PUT'], next_frame);
          }
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

      $scope.cancelDataJson = function() {
        alert("Action Canceled");
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
