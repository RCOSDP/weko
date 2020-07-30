require([
  'jquery',
  'bootstrap'
], function () {
  $('#weko_id_hidden').hide();
  $("#item-type-lists").change(function (ev) {
    window.location.href = '/items/' + $(this).val();
  });
  $("#btnModalClose").click(function () {
    //Process close 'Add Author' or 'Import Author' modal.
    window.appAuthorSearch.namespace.isCloseAuthorModal();
  });
  $("#meta-search-close").click(function () {
    $('#meta-search').modal('toggle');
    $("div.modal-backdrop").remove();
  });
});

/**
 * Custom bs-datepicker.
 * Default bs-datepicker: just support one pattern for input.
 * Custom bs-datepicker: support validate three pattern.
 * Used way:
 *  templateUrl: /static/templates/weko_deposit/datepicker_multi_format.html
 *  customFormat: enter your pattern.
 *    if it none, pattern are yyyy-MM-dd, yyyy-MM, yyyy.
*/
var Pattern = {
  yyyy: '\\d{4}',
  MM: '(((0)[1-9])|((1)[0-2]))',
  dd: '([0-2][0-9]|(3)[0-1])',
  sep: '(-)'
}
var Format = {
  yyyyMMdd: '^(' + Pattern.yyyy + Pattern.sep +
    Pattern.MM + Pattern.sep + Pattern.dd + ')$',
  yyyyMM: '^(' + Pattern.yyyy + Pattern.sep + Pattern.MM + ')$',
  yyyy: '^(' + Pattern.yyyy + ')$',
}
var CustomBSDatePicker = {
  option: {
    element: undefined,
    defaultFormat: Format.yyyyMMdd + '|' + Format.yyyyMM + '|' + Format.yyyy,
    cls: 'multi_date_format'
  },
  /**
   * Clear validate status for this element.
  */
  init: function () {
    let $element = $(CustomBSDatePicker.option.element);
    let $this_parent = $element.parent().parent();
    $element.removeClass('ng-invalid ng-invalid-date ng-invalid-parse');
    $element.next().next().addClass('hide');
    $this_parent.removeClass('has-error');
  },
  /**
   * Get format from defined user on form schema.
   * If user don't defined, this pattern get default pattern.
   * Default pattern: option.defaultFormat.
   * @return {String} return pattern.
  */
  getPattern: function () {
    let def_pattern = CustomBSDatePicker.option.defaultFormat;
    let $element = $(CustomBSDatePicker.option.element);
    let pattern = $element.data('custom-format');
    return (pattern.length == 0) ? def_pattern : pattern;
  },
  /**
   * Check data input valid with defined pattern.
   * @return {Boolean} return true if value matched
  */
  isMatchRegex: function () {
    let $element = $(CustomBSDatePicker.option.element);
    let val = $element.val();
    let pattern = CustomBSDatePicker.getPattern();
    let reg = new RegExp(pattern);
    return reg.test(val);
  },
  /**
   * Check input required.
   * @return {Boolean} return true if input required
  */
  isRequired: function () {
    let $lement = $(CustomBSDatePicker.option.element);
    let $this_parent = $lement.parent().parent();
    let label = $this_parent.find('label');
    return label.hasClass('field-required');
  },
  /**
  * Get the number of days in any particular month
  * @param  {number} m The month (valid: 0-11)
  * @param  {number} y The year
  * @return {number}   The number of days in the month
  */
  daysInMonth: function (m, y) {
    switch (m) {
      case 1:
        return (y % 4 == 0 && y % 100) || y % 400 == 0 ? 29 : 28;
      case 8: case 3: case 5: case 10:
        return 30;
      default:
        return 31
    }
  },
  /**
  * Check if a date is valid
  * @param  {number}  d The day
  * @param  {number}  m The month
  * @param  {number}  y The year
  * @return {Boolean}   Returns true if valid
  */
  isValidDate: function (d, m, y) {
    let month = parseInt(m, 10) - 1;
    let check_min_month = m >= 0;
    let check_max_month = m < 12;
    let check_min_day = d > 0;
    let check_max_day = d <= CustomBSDatePicker.daysInMonth(month, y);
    return check_min_month && check_max_month && check_min_day && check_max_day;
  },
  /**
   * Check all validate for this.
   * All validation valid => return true.
   * @return {Boolean} Returns true if valid
  */
  isValidate: function () {
    let $element = $(CustomBSDatePicker.option.element);
    let val = $element.val();
    if (val.length == 0) {
      //Required input invalid.
      if (CustomBSDatePicker.isRequired()) return false;
    } else {
      //Data input is not match with defined pattern.
      if (!CustomBSDatePicker.isMatchRegex()) return false;
      //Check day by month and year.
      let arr = val.split('-');
      if (arr.length == 3 && !CustomBSDatePicker.isValidDate(arr[2], arr[1], arr[0])) return false;
    }
    return true;
  },
  /**
   * Check validate and apply css for this field.
  */
  validate: function () {
    let $element = $(CustomBSDatePicker.option.element);
    let $this_parent = $element.parent().parent();
    if (!CustomBSDatePicker.isValidate()) {
      $element.next().next().removeClass('hide');
      $this_parent.addClass('has-error');
    }
  },
  /**
   * This is mean function in order to validate.
   * @param {[type]} element date field
  */
  process: function (element) {
    CustomBSDatePicker.option.element = element;
    CustomBSDatePicker.init();
    CustomBSDatePicker.validate();
  },
  /**
  * Init attribute of model object if them undefine.
  * @param  {[object]}  model
  * @param  {[object]}  element is date input control.
  */
  initAttributeForModel: function (model, element) {
    if($(element).val().length == 0) return;
    let ng_model = $(element).attr('ng-model').replace(/']/g, '');
    let arr = ng_model.split("['");
    //Init attribute of model object if them undefine.
    let str_code = '';
    $.each(arr, function (ind_01, val_02) {
      str_code += (ind_01 == 0) ? val_02 : "['" + val_02 + "']";
      let chk_str_code = '';
      if (ind_01 != arr.length - 1) {
        chk_str_code = "if(!" + str_code + ") " + str_code + "={};";
      }
      eval(chk_str_code);
    });
  },
  /**
  * Excute this function before 'Save' and 'Next' processing
  * Get data from fields in order to fill to model.
  * @param  {[object]}  model
  * @param  {[Boolean]}  reverse
  */
  setDataFromFieldToModel: function (model, reverse) {
    let cls = CustomBSDatePicker.option.cls;
    let element_arr = $('.' + cls);
    $.each(element_arr, function (ind, val) {
      CustomBSDatePicker.initAttributeForModel(model, val);
      if (reverse) {
        //Fill data from model to fields
        str_code = "$(val).val(" + $(val).attr('ng-model') + ")";
        eval(str_code);
      } else {
        //Fill data from fields to model
        str_code = $(val).attr('ng-model') + '=$(val).val()';
        eval(str_code);
      }
    });
  },
  /**
   * Get date fields name which invalid.
   * @return {array} Returns name list.
  */
  getInvalidFieldNameList: function () {
    let cls = CustomBSDatePicker.option.cls;
    let element_arr = $('.' + cls);
    let result = [];
    $.each(element_arr, function (ind, val) {
      let $element = $(val);
      let $parent = $element.parent().parent();
      if ($parent.hasClass('has-error')) {
        let name = $element.attr('name');
        let label = $("label[for=" + name + "]").text().trim();
        result.push(label);
      }
    });
    return result;
  },
  /**
   * If input empty, this attribute delete.
   * Fix bug: not enter data for date field.
  */
  removeLastAttr: function(model){
    let cls = CustomBSDatePicker.option.cls;
    let element_arr = $('.' + cls);
    $.each(element_arr, function (ind, val) {
      if($(val).val().length > 0){
        CustomBSDatePicker.initAttributeForModel(model, val);
        let ng_model = $(val).attr('ng-model');
        let last_index = ng_model.lastIndexOf('[');
        let previous_attr = ng_model.substring(0, last_index);
        let str_code = "if("+ng_model+"==''){"+previous_attr+"={}}";
        eval(str_code);
      }
    });
  }
}

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
    success: function (data, status) {
      if (data.error) {
        //alert("Some errors have occured!\nDetail:" + data.error);
        var modalcontent = "Some errors have occured!\nDetail:" + data.error;
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
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
    error: function (data, status) {
      //alert("Cannot connect to server!");
      var modalcontent = "Cannot connect to server!";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
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
    success: function (data, status) {
      if (mode == 'share_username') {
        $("#share_email").val(data.results.email);
      } else {
        if (mode == 'share_email') {
          if (data.results.username) {
            $("#share_username").val(data.results.username);
          } else {
            $("#share_username").val("");
          }
        }
      }
    },
    error: function (data, status) {
      //alert("Cannot connect to server!");
      var modalcontent = "Cannot connect to server!";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
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

function toObject(arr) {
  var rv = {};
  for (var i = 0; i < arr.length; ++i)
    rv[i] = arr[i];
  return rv;
}

(function (angular) {
  function addAlert(message, class_style) {
    id_alert = "";
    if (typeof class_style === 'undefined') {
      class_style = 'alert-light'
      id_alert = 'alert-style'
    }
    $('#alerts').append(
      '<div class="alert ' + class_style + '" id="' + id_alert + '">' +
      '<button type="button" class="close" data-dismiss="alert">' +
      '&times;</button>' + message + '</div>');
  }
  // Bootstrap it!
  angular.element(document).ready(function () {
    function WekoRecordsCtrl($scope, $rootScope, InvenioRecordsAPI) {
      $scope.currentUrl = window.location.pathname + window.location.search;
      $scope.resourceTypeKey = "";
      $scope.groups = [];
      $scope.filemeta_keys = [];
      $scope.bibliographic_key = '';
      $scope.bibliographic_title_key = '';
      $scope.bibliographic_title_lang_key = '';
      $scope.usage_report_activity_id = '';
      $scope.is_item_owner = false;
      $scope.feedback_emails = []
      $scope.render_requirements = false;
      $scope.error_list = [];
      $scope.required_list = [];
      $scope.usageapplication_keys = [];
      $scope.outputapplication_keys = [];
      $scope.authors_keys = [];
      $scope.data_author = [];
      $scope.sub_item_keys = ['nameIdentifiers', 'affiliation', 'contributorAffiliations'];
      $scope.scheme_uri_mapping = [
        {
          scheme : 'nameIdentifierScheme',
          uri : 'nameIdentifierURI'
        },
        {
          scheme : 'affiliationNameIdentifierScheme',
          uri : 'affiliationNameIdentifierURI'
        },
        {
          scheme : 'contributorAffiliationScheme',
          uri : 'contributorAffiliationURI'
        }
      ]
      $scope.identifiers = 'nameIdentifiers'
      $scope.identifier_mapping = 'nameIdentifier'
      $scope.scheme_identifier_mapping = 'nameIdentifierScheme'
      $scope.uri_identifier_mapping = 'nameIdentifierURI'
      $scope.scheme_affiliation_mapping = ['affiliationNameIdentifierScheme', 'contributorAffiliationScheme']
      $scope.sub_item_scheme = ['nameIdentifierScheme', 'affiliationNameIdentifierScheme', 'contributorAffiliationScheme']
      $scope.sub_item_uri = ['nameIdentifierURI', 'affiliationNameIdentifierURI', 'contributorAffiliationURI']
      $scope.sub_item_id = ['nameIdentifier', 'affiliationNameIdentifier', 'contributorAffiliation']
      $scope.previousNumFiles = 0;
      $scope.bibliographic_titles = "bibliographic_titles";

      $scope.searchFilemetaKey = function () {
        if ($scope.filemeta_keys.length > 0) {
          return $scope.filemeta_keys;
        }
        for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
          var value = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
          if (value.type == 'array') {
            if (value.items.properties.hasOwnProperty('filename')) {
              $scope.filemeta_keys.push(key);
            }
          }
        }
      }

      $scope.searchForm = function (sub_item_key) {
        let form = "";
        $rootScope.recordsVM.invenioRecordsForm.forEach(function (recordForm) {
          if (recordForm.hasOwnProperty('items')) {
            items = recordForm.items
            for (let i in items) {
              if (items[i].hasOwnProperty('key') && items[i].key.indexOf(sub_item_key) >= 0) {
                form = recordForm
              }
            }
          }
        });
        return form;
      };

      $scope.searchSchemaIdentifierKey = function(item) {
        for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
          var value = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
          var properties = value.properties ? value.properties : (value.items ? value.items.properties : [])
          if (Object.keys(properties).indexOf(item) >= 0) {
              if ($scope.authors_keys.indexOf(key) >= 0) {
                break
              }
             $scope.authors_keys.push(key);
          }
        }
      };

      $scope.getValueAuthor = function () {
        var data_author = {}
        $scope.data_author.map(function (item) {
          data_author[item.scheme] = item.url
        })
        $scope.authors_keys.map(function (key) {
          let list_nameIdentifiers = []
          let uri_form_model = $rootScope.recordsVM.invenioRecordsModel[key]
          if (!Array.isArray(uri_form_model)) {
            $scope.sub_item_keys.map(function (subkey) {
              if (Object.keys(uri_form_model).indexOf(subkey) >= 0) {
                let name_identifier_form = uri_form_model[subkey]
                name_identifier_form.map(function (form) {
                  $scope.sub_item_scheme.map(function (scheme) {
                    if (form.hasOwnProperty(scheme)) {
                      $scope.scheme_uri_mapping.map(function (mapping) {
                        if (mapping.scheme == scheme) {
                          form[mapping.uri] = data_author[form[scheme]]
                        }
                      })
                    }
                  })
                  list_nameIdentifiers.push(form)
                })
              }
            })
          }
          else if (Array.isArray(uri_form_model)) {
            uri_form_model.map(function (object) {
              $scope.sub_item_keys.map(function (subkey) {
                if (Object.keys(object).indexOf(subkey) >= 0) {
                  let name_identifier_form = object[subkey]
                  name_identifier_form.map(function (form) {
                    $scope.sub_item_scheme.map(function (scheme) {
                      if (form.hasOwnProperty(scheme)) {
                        $scope.scheme_uri_mapping.map(function (mapping) {
                          if (mapping.scheme == scheme) {
                            form[mapping.uri] = data_author[form[scheme]]
                          }
                        })
                      }
                    })
                    list_nameIdentifiers.push(form)
                  })
                }
              })
            })
          }

          $scope.sub_item_scheme.map(function (scheme) {
            if (Object.keys($rootScope.recordsVM.invenioRecordsModel[key]).indexOf(scheme) >= 0) {
              $rootScope.recordsVM.invenioRecordsModel[key].scheme = list_nameIdentifiers
            }
          })
        })
      }

      /**
       * Common handle for author identifier.
       * @param identifier_key Identifier key
       * @param handlerFunction Handler function
       */
      $scope.commonHandleForAuthorIdentifier = function (identifier_key, handlerFunction) {
        var data_author = {};
        let model = $rootScope.recordsVM.invenioRecordsModel;
        $scope.data_author.map(function (item) {
          data_author[item.scheme] = item.url;
        })
        if ($scope.authors_keys.indexOf(identifier_key) >= 0 ) {
          let list_nameIdentifiers = [];
          let uri_form_model = model[identifier_key];
          if (!Array.isArray(uri_form_model)) {
            if (Object.keys(uri_form_model).indexOf($scope.identifiers) >= 0) {
              let name_identifier_form = uri_form_model[$scope.identifiers];
              name_identifier_form.forEach(function (form) {
                handlerFunction(form, data_author);
                list_nameIdentifiers.push(form);
              })
            }
          }
          else if (Array.isArray(uri_form_model)) {
            uri_form_model.forEach(function (object) {
              if (Object.keys(object).indexOf($scope.identifiers) >= 0) {
                let name_identifier_form = object[$scope.identifiers];
                name_identifier_form.forEach(function (form) {
                  handlerFunction(form, data_author);
                  list_nameIdentifiers.push(form);
                })
              }
            })
          }

          $scope.sub_item_scheme.map(function (scheme) {
            if (Object.keys(model[identifier_key]).indexOf(scheme) >= 0) {
              model[identifier_key].scheme = list_nameIdentifiers;
            }
          })
        }

      }

      /**
       * Clear author value
       * @param e HTML event
       * @param identifier_key Identifier key
       */
      $scope.clearAuthorValue = function (e, identifier_key) {
        function handleClearAuthorValue(form) {
          if (form.hasOwnProperty($scope.identifier_mapping) && form.hasOwnProperty($scope.uri_identifier_mapping)) {
            form[$scope.identifier_mapping] = "";
            form[$scope.uri_identifier_mapping] = "";
          }
                  }
        $scope.commonHandleForAuthorIdentifier(identifier_key, handleClearAuthorValue);
          }

      /**
       * Get Identifier URI value.
       * @param e HTML event
       * @param identifier_key Identifier key.
       */
      $scope.getIdentifierURIValue = function (e, identifier_key) {
        function handleGetValueForAuthorIdentifierURI(form, data_author) {
          let schemaMappingKey = $scope.scheme_identifier_mapping;
          let idMappingKey = $scope.identifier_mapping;
          let uriMappingKey = $scope.uri_identifier_mapping;
          let isFillIdentifierURI = checkFillCreatorIdentifierURI(data_author[form[schemaMappingKey]], form[idMappingKey])
          if (form[schemaMappingKey] && isFillIdentifierURI) {
            form[uriMappingKey] = data_author[form[schemaMappingKey]].replace(/#+$/, form[idMappingKey]);
          } else {
            form[uriMappingKey] = data_author[form[schemaMappingKey]];
          }
        }
        $scope.commonHandleForAuthorIdentifier(identifier_key, handleGetValueForAuthorIdentifierURI);
      }

      $scope.initAuthorList = function () {
        $.ajax({
          url: '/api/items/author_prefix_settings',
          method: 'GET',
          async: false,
          success: function (data, status) {
            $scope.data_author = data;
          },
          error: function (data, status) {
          }
        });
      }

      $scope.getDataAuthors = function () {
        var author_schema;
        var author_form;
        $scope.sub_item_keys.map(function(key) {
          $scope.searchSchemaIdentifierKey(key);
        })
        $scope.authors_keys.forEach(function (author_key) {
          var author_idt_schema = $rootScope.recordsVM.invenioRecordsSchema.properties[author_key];
          var author_idt_form = $scope.searchForm(author_key);
          if (author_idt_schema && author_idt_form) {
            if (author_idt_schema.type == 'object') {
              $scope.sub_item_keys.map(function (item) {
                if (!!author_idt_schema.properties[item]){
                  author_schema = author_idt_schema.properties[item].items;
                  author_form = get_subitem(author_idt_form.items, item);
                  if (typeof author_form != 'undefined' && typeof author_schema != 'undefined') {
                      $scope.addSchemeToSelectForm(author_form, author_schema);
                    }
                  }
                })
              }
            else if (author_idt_schema.type == 'array') {
              $scope.sub_item_keys.map(function (item) {
                  if (!!author_idt_schema.items.properties[item]) {
                      author_schema = author_idt_schema.items.properties[item].items;
                      author_form = get_subitem(author_idt_form.items, item);
                      if (typeof author_form != 'undefined' && typeof author_schema != 'undefined') {
                        $scope.addSchemeToSelectForm(author_form, author_schema);
                    }
                  }
                })
              }
          }
        });
        $rootScope.$broadcast('schemaFormRedraw');
      };


      $scope.addSchemeToSelectForm = function(author_form, author_schema) {
           for (let searchTitleMap in author_form.items) {
                if (author_form.items[searchTitleMap].hasOwnProperty('titleMap')) {
                  var numberTitleMap = searchTitleMap;
                  var author_form_key = author_form.items[searchTitleMap].key
                  // Only clear and do logic for "Scheme" field
                  $scope.sub_item_scheme.map(function (scheme) {
                      if (author_form_key.indexOf(scheme) != -1) {
                        author_form.items[searchTitleMap].titleMap = [];
                        $scope.sub_item_scheme.map(function (item) {
                          if (author_schema.properties[item]) {
                            author_schema.properties[item]['enum'] = [];
                            author_schema.properties[item]['enum'].push(null);
                            $scope.data_author.forEach(function (value_scheme) {
                              $scope.sub_item_scheme.map(function (key) {
                                if (author_schema.properties[key]) {
                                  author_schema.properties[key]['enum'].push(value_scheme['scheme']);
                                  author_form.items[numberTitleMap].titleMap.push({
                                    name: value_scheme['scheme'],
                                    value: value_scheme['scheme']
                                  });
                                }
                              })
                            });
                            if (typeof author_form.key === 'string') {
                              let identifierKey = author_form.key.split('.')[0];
                              if (scheme === $scope.scheme_identifier_mapping) {
                                author_form.items[searchTitleMap]['onChange'] = 'clearAuthorValue($event,"' + identifierKey + '")';
                              } else if ($scope.scheme_affiliation_mapping.indexOf(scheme) >= 0) {
                                author_form.items[searchTitleMap]['onChange'] = 'getValueAuthor($event,"' + identifierKey + '")';
                              }
                            }
                          }
                        })
                      }
                  })
              }
              // set read only Creator Name Identifier URI
              $scope.sub_item_uri.map(function(item) {
                let identifier_uri_form = get_subitem(author_form.items, item)
                if (identifier_uri_form) {
                  identifier_uri_form['readonly'] = true;
                }
              })

              $scope.sub_item_id.map(function(item) {
               let items = author_form.items;
                for (var i = 0; i < items.length; i++) {
                 var key = items[i].key;
                  if (typeof key === 'string') {
                   let listKey = key.split('.');
                    for (let index in listKey) {
                      if (listKey[index] === item) {
                       var identifier_id_form = items[i];
                      }
                    }
                  }
            }

                if (identifier_id_form && typeof author_form.key === 'string') {
                 identifier_id_form['onChange'] = 'getIdentifierURIValue($event,"' + author_form.key.split('.')[0] + '")';
                }
              })
            }
      }
      function checkFillCreatorIdentifierURI(nameIdentifierURI, nameIdentifier) {
        return !!(nameIdentifierURI.search(/#+$/) > -1 && nameIdentifier);
      }

      $scope.searchUsageApplicationIdKey = function() {
        if ($scope.usageapplication_keys.length > 0) {
          return $scope.usageapplication_keys;
        }
        for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
          var value = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
          if (value.type == 'array') {
            if (value.items.properties.hasOwnProperty('subitem_corresponding_usage_application_id')) {
              $scope.usageapplication_keys.push(key);
              break;
            }
          }
        }
      };

      $scope.searchOutputApplicationIdKey = function() {
        if ($scope.outputapplication_keys.length > 0) {
            return $scope.outputapplication_keys;
        }
        for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
          if ($rootScope.recordsVM.invenioRecordsSchema.properties[key].type == 'array') {
            if ($rootScope.recordsVM.invenioRecordsSchema.properties[key].items.properties.hasOwnProperty('subitem_corresponding_output_id')) {
              $scope.outputapplication_keys.push(key);
              break;
            }
          }
        }
      }

      $scope.initCorrespondingIdList = function () {
        $scope.searchUsageApplicationIdKey();
        $scope.usageapplication_keys.forEach(function (key) {
          schema = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
          form = $scope.searchForm('subitem_corresponding_usage_application_id');
          if (schema && form) {
            schema.items.properties['subitem_corresponding_usage_application_id']['enum'] = [];
            schema.items.properties['subitem_corresponding_usage_application_id']['enum'].push(null);
            usage_application_form = form.items[0];
            usage_application_form['titleMap'] = []
          }
        });

        $scope.searchOutputApplicationIdKey();
        $scope.outputapplication_keys.forEach(function (key) {
          output_schema = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
          output_form = $scope.searchForm('subitem_corresponding_output_id');
          if (output_schema && output_form) {
            output_schema.items.properties['subitem_corresponding_output_id']['enum'] = [];
            output_schema.items.properties['subitem_corresponding_output_id']['enum'].push(null);
            output_report_form = output_form.items[0];
            output_report_form['titleMap'] = []
          }
        });

        if ($scope.usageapplication_keys.length > 0 || $scope.outputapplication_keys.length > 0) {
          const acitivityUrl = '/items/corresponding-activity';

          activityList = {};
          $.ajax({
            url: acitivityUrl,
            method: 'GET',
            async: false,
            success: function (data, status) {
              let usageActivity;
              if ($scope.usage_report_activity_id != ''){
                usageActivity = [$scope.usage_report_activity_id];
              } else {
                usageActivity = data['usage_application'];
              }
              if (usageActivity.length > 0) {
                usageActivity.forEach(function (activity) {
                  if (typeof schema != 'undefined' && typeof usage_application_form != 'undefined' && schema && usage_application_form) {
                    schema.items.properties['subitem_corresponding_usage_application_id']['enum'].push(activity);
                    usage_application_form['titleMap'].push({
                      name: activity,
                      value: activity
                    });
                  }
                })
              }

              let outputReport = data['output_report'];
              if (outputReport.length > 0) {
                outputReport.forEach(function (report) {
                  if (typeof output_schema != 'undefined' && typeof output_report_form != 'undefined' && output_schema && output_report_form) {
                    output_schema.items.properties['subitem_corresponding_output_id']['enum'].push(report);
                    output_report_form['titleMap'].push({
                      name: report,
                      value: report
                    });
                  }
                })
              }
              $rootScope.$broadcast('schemaFormRedraw');
            },
            error: function (data, status) {
            }
          });
        }
      };

      function get_subitem(items, subitem) {
        for (var i = 0; i < items.length; i++) {
          var key = items[i].key
          if (typeof key !== 'undefined' && key.indexOf(subitem) != -1) {
            return items[i]
          }
        }
      }

      $scope.getFormByKey = function (key) {
        let forms = $rootScope.recordsVM.invenioRecordsForm;
        for (let i in forms) {
          if (forms[i].hasOwnProperty('key') && forms[i].key == key) {
            return forms[i];
          }
        }
      }

      $scope.initFilenameList = function () {
        var filekey = 'filename';
        $scope.searchFilemetaKey();
        $scope.filemeta_keys.forEach(function (filemeta_key) {
          filemeta_schema = $rootScope.recordsVM.invenioRecordsSchema.properties[filemeta_key];
          filemeta_form = $scope.getFormByKey(filemeta_key);
          if (filemeta_schema && filemeta_form && filemeta_schema.items.properties[filekey]) {
            filemeta_schema.items.properties[filekey]['enum'] = [];
            filemeta_schema.items.properties[filekey]['enum'].push(null)
            filemeta_filename_form = get_subitem(filemeta_form.items, filekey);
            filemeta_filename_form['titleMap'] = [];
            $rootScope.filesVM.files.forEach(function (file) {
              if (file.completed && !file.is_thumbnail) {
                filemeta_schema.items.properties[filekey]['enum'].push(file.key);
                filemeta_filename_form['titleMap'].push({ name: file.key, value: file.key });
              }
            });
          }
          groupsprice_schema = filemeta_schema.items.properties['groupsprice']
          groupsprice_form = get_subitem(filemeta_form.items, 'groupsprice')
          if (groupsprice_schema && groupsprice_form) {
            groupsprice_schema.items.properties['group']['enum'] = [];
            groupsprice_schema.items.properties['group']['enum'].push(null);
            group_form = get_subitem(groupsprice_form.items, 'groupsprice');
            group_form['titleMap'] = [];
            $scope.groups.forEach(function (group) {
              groupsprice_schema.items.properties['group']['enum'].push(group.id);
              group_form['titleMap'].push({ name: group.value, value: group.id });
            });
          }
        });
        $rootScope.$broadcast('schemaFormRedraw');
      }
      $scope.initContributorData = function () {
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
              success: function (data, stauts) {
                if (data.owner) {
                  $scope.is_item_owner = true;
                  $("#contributor-panel").removeClass("hidden");
                  $(".other_user_rad").click();
                  $("#share_username").val(data.username);
                  $("#share_email").val(data.email);
                } else {
                  $(".other_user_rad").click();
                  $("#share_username").val(data.username);
                  $("#share_email").val(data.email);
                }
              },
              error: function (data, status) {
                //alert("Cannot connect to server!");
                var modalcontent = "Cannot connect to server!";
                $("#inputModal").html(modalcontent);
                $("#allModal").modal("show");
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
      $scope.initUserGroups = function () {
        $.ajax({
          url: '/accounts/settings/groups/grouplist',
          method: 'GET',
          async: false,
          success: function (data, status) {
            if (!$.isEmptyObject(data)) {
              for (let key in data) {
                let group = {
                  id: key,
                  value: data[key]
                };
                $scope.groups.push(group);
              }
            }
          }
        });
      }
      $scope.searchTypeKey = function () {
        if ($scope.resourceTypeKey.length > 0) {
          return $scope.resourceTypeKey;
        }
        for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
          let value = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
          if (value.type == 'object') {
            if (value.properties.hasOwnProperty('resourcetype')) {
              $scope.resourceTypeKey = key;
              break;
            }
          }
        }
      }
      $scope.resourceTypeSelect = function () {
        let resourcetype = $("select[name='resourcetype']").val();
        resourcetype = resourcetype.split("string:").pop();
        let resourceuri = "";
        if ($scope.resourceTypeKey) {
          if (!$("#resourceuri").prop('disabled')) {
            $("#resourceuri").prop('disabled', true);
          }

          switch (resourcetype) {
            // multiple
            case 'interactive resource':
              resourceuri = "http://purl.org/coar/resource_type/c_e9a0";
              break;
            case 'learning material':
              resourceuri = "http://purl.org/coar/resource_type/c_1843";
              break;
            case 'musical notation':
              resourceuri = "http://purl.org/coar/resource_type/c_18cw";
              break;
            case 'research proposal':
              resourceuri = "http://purl.org/coar/resource_type/c_baaf";
              break;
            case 'software':
              resourceuri = "http://purl.org/coar/resource_type/c_5ce6";
              break;
            case 'technical documentation':
              resourceuri = "http://purl.org/coar/resource_type/c_71bd";
              break;
            case 'workflow':
              resourceuri = "http://purl.org/coar/resource_type/c_393c";
              break;
            case 'other（その他）':
              resourceuri = "http://purl.org/coar/resource_type/c_1843";
              break;
            case 'other（プレプリント）':
              $("#resourceuri").prop('disabled', false);
              resourceuri = "";
              break;
            // conference
            case 'conference object':
              resourceuri = "http://purl.org/coar/resource_type/c_c94f";
              break;
            case 'conference proceedings':
              resourceuri = "http://purl.org/coar/resource_type/c_f744";
              break;
            case 'conference poster':
              resourceuri = "http://purl.org/coar/resource_type/c_6670";
              break;
            // patent
            case 'patent':
              resourceuri = "http://purl.org/coar/resource_type/c_15cd";
              break;
            // lecture
            case 'lecture':
              resourceuri = "http://purl.org/coar/resource_type/c_8544";
              break;
            // Book
            case 'book':
              resourceuri = "http://purl.org/coar/resource_type/c_2f33";
              break;
            case 'book part':
              resourceuri = "http://purl.org/coar/resource_type/c_3248";
              break;
            // Dataset
            case 'dataset':
              resourceuri = "http://purl.org/coar/resource_type/c_ddb1";
              break;
            // Article
            case 'conference paper':
              resourceuri = "http://purl.org/coar/resource_type/c_5794";
              break;
            case 'data paper':
              resourceuri = "http://purl.org/coar/resource_type/c_beb9";
              break;
            case 'departmental bulletin paper':
              resourceuri = "http://purl.org/coar/resource_type/c_6501";
              break;
            case 'editorial':
              resourceuri = "http://purl.org/coar/resource_type/c_b239";
              break;
            case 'journal article':
              resourceuri = "http://purl.org/coar/resource_type/c_6501";
              break;
            case 'periodical':
              resourceuri = "http://purl.org/coar/resource_type/c_2659";
              break;
            case 'review article':
              resourceuri = "http://purl.org/coar/resource_type/c_dcae04bc";
              break;
            case 'article':
              resourceuri = "http://purl.org/coar/resource_type/c_6501";
              break;
            // Image
            case 'image':
              resourceuri = "http://purl.org/coar/resource_type/c_c513";
              break;
            case 'still image':
              resourceuri = "http://purl.org/coar/resource_type/c_ecc8";
              break;
            case 'moving image':
              resourceuri = "http://purl.org/coar/resource_type/c_8a7e";
              break;
            case 'video':
              resourceuri = "http://purl.org/coar/resource_type/c_12ce";
              break;
            // Cartographic
            case 'cartographic material':
              resourceuri = "http://purl.org/coar/resource_type/c_12cc";
              break;
            case 'map':
              resourceuri = "http://purl.org/coar/resource_type/c_12cd";
              break;
            // Sound
            case 'sound':
              resourceuri = "http://purl.org/coar/resource_type/c_18cc";
              break;
            // Report
            case 'internal report':
              resourceuri = "http://purl.org/coar/resource_type/c_18ww";
              break;
            case 'report':
              resourceuri = "http://purl.org/coar/resource_type/c_93fc";
              break;
            case 'research report':
              resourceuri = "http://purl.org/coar/resource_type/c_18ws";
              break;
            case 'technical report':
              resourceuri = "http://purl.org/coar/resource_type/c_18gh";
              break;
            case 'policy report':
              resourceuri = "http://purl.org/coar/resource_type/c_186u";
              break;
            case 'report part':
              resourceuri = "http://purl.org/coar/resource_type/c_ba1f";
              break;
            case 'working paper':
              resourceuri = "http://purl.org/coar/resource_type/c_8042";
              break;
            // Thesis
            case 'thesis':
              resourceuri = "http://purl.org/coar/resource_type/c_46ec";
              break;
            case 'bachelor thesis':
              resourceuri = "http://purl.org/coar/resource_type/c_7a1f";
              break;
            case 'master thesis':
              resourceuri = "http://purl.org/coar/resource_type/c_bdcc";
              break;
            case 'doctoral thesis':
              resourceuri = "http://purl.org/coar/resource_type/c_db06";
              break;
            default:
              resourceuri = "";
          }
          $rootScope.recordsVM.invenioRecordsModel[$scope.resourceTypeKey].resourceuri = resourceuri;
        }
      }
      $scope.getBibliographicMetaKey = function () {
        let recordSchemaProperties = $rootScope.recordsVM.invenioRecordsSchema.properties;
        let bibliographicKey = $scope.bibliographic_titles;
        for (let key in recordSchemaProperties) {
          let properties = recordSchemaProperties[key].properties;
          if (properties && properties.hasOwnProperty(bibliographicKey)) {
            $scope.bibliographic_key = key;
            const titleProperties = properties[bibliographicKey].items.properties;
            // Get language key
            for (let subKey in titleProperties) {
              let subValue = titleProperties[subKey];
              if (subValue.format === "text") {
                $scope.bibliographic_title_key = subKey;
              } else if (subValue.format === "select") {
                $scope.bibliographic_title_lang_key = subKey;
              }
            }
          }
        }
      }
      $scope.autofillJournal = function () {
        this.getBibliographicMetaKey();
        const bibliographicKey = $scope.bibliographic_key;
        const title = $scope.bibliographic_title_key;
        const titleLanguage = $scope.bibliographic_title_lang_key;
        const activityId = $("#activity_id").text();
        let model = $rootScope.recordsVM.invenioRecordsModel;
        if (bibliographicKey && model && activityId) {
          let request = {
            url: '/api/autofill/get_auto_fill_journal/' + activityId,
            method: "GET",
            dataType: "json"
          };

          InvenioRecordsAPI.request(request).then(
            function success(response) {
              let data = response.data;
              if (data && data.result) {
                let journalData = data.result;
                const defaultLanguage = "en";
                if (journalData.keywords) {
                  let titleData = {};
                  titleData[title] = journalData.keywords;
                  titleData[titleLanguage] = defaultLanguage;
                  model[bibliographicKey][$scope.bibliographic_titles] = [titleData];
                }
              }
            },
            function error(response) {
              $("#inputModal").html(response);
              $("#allModal").modal("show");
            }
          );
        }
      }

      $scope.findTextByElementId = function (elementId, value){
        var options = document.getElementById(elementId).options;
        for (i=0; i< options.length; i++){
          if (options[i].value === value){
            return options[i].text
          }
        }
      }

      $scope.findValueByElementId = function (elementId, text){
        var options = document.getElementById(elementId).options;
        for (i=0; i< options.length; i++){
          if (options[i].text === text){
            return options[i].value
          }
        }
      }
      $scope.translationsInstitutePosition = function (value) {
          return $scope.findTextByElementId('institute_position_list', value)
      };

      $scope.translationsInstitutePositionByText = function (text) {
          return $scope.findValueByElementId('institute_position_list', text)
      };

      $scope.translationsPosition = function (value) {
          return $scope.findTextByElementId('position_list', value)
      };

      $scope.translationsPositionByText = function (text) {
          return $scope.findValueByElementId('position_list', text)
      };

      $scope.updatePositionKey = function() {
                let model = $rootScope.recordsVM.invenioRecordsModel;
                if (Object.keys(model).length === 0 && model.constructor === Object) {
                    return false;
                } else {
                    let isExisted = false;
                    for (let key in model) {
                        if (model.hasOwnProperty(key)) {
                            let fullName = model[key]['subitem_fullname'];
                            let userMail = model[key]['subitem_mail_address'];
                            // let userPosition = model[key]['subitem_position'];
                            if (fullName || userMail) {
                                let position = model[key]['subitem_position'];
                                position = $scope.translationsPositionByText(position);
                                $rootScope.recordsVM.invenioRecordsModel[key]['subitem_position'] = position;
                                if (model[key]['subitem_affiliated_institution'] && model[key]['subitem_affiliated_institution'].length >0) {

                                  for (let index in toObject(model[key]['subitem_affiliated_institution'])) {
                                      let affiliatedInstitution = toObject(model[key]['subitem_affiliated_institution'])[index];
                                      let translationsAffiliatedInstitution = affiliatedInstitution['subitem_affiliated_institution_position']
                                        if (translationsAffiliatedInstitution) {
                                            let institutionPosition = $scope.translationsInstitutePositionByText(translationsAffiliatedInstitution);
                                            $rootScope.recordsVM.invenioRecordsModel[key]['subitem_affiliated_institution'][index]['subitem_affiliated_institution_position'] = institutionPosition;
                                        }
                                    }

                                }
                                isExisted = true;
                                // Set read only for user information property
                                $rootScope.recordsVM.invenioRecordsForm.find(function (subItem) { return subItem.key == key })['readonly'] = true;
                                break;
                            }
                        }
                    }
                    return isExisted;
                }
      };
      $scope.isExistingUserProfile = function() {
        let model = $rootScope.recordsVM.invenioRecordsModel;
        if (Object.keys(model).length === 0 && model.constructor === Object){
          return false;
        } else {
          let isExisted = false;
          for (let key in model) {
            if (model.hasOwnProperty(key)) {
              let fullName = model[key]['subitem_fullname'];
              let userMail = model[key]['subitem_mail_address'];
              if (fullName || userMail) {
                let position = model[key]['subitem_position'];
                position = $scope.translationsPosition(position);
                $rootScope.recordsVM.invenioRecordsModel[key]['subitem_position'] = position;
                if (model[key]['subitem_affiliated_institution'] && model[key]['subitem_affiliated_institution'].length >0) {

                     for (let index in toObject(model[key]['subitem_affiliated_institution'])) {
                        let affiliatedInstitution = toObject(model[key]['subitem_affiliated_institution'])[index];
                        let translationsAffiliatedInstitution = affiliatedInstitution['subitem_affiliated_institution_position']
                        if (translationsAffiliatedInstitution) {
                            let institutionPosition = $scope.translationsInstitutePosition(translationsAffiliatedInstitution);
                            $rootScope.recordsVM.invenioRecordsModel[key]['subitem_affiliated_institution'][index]['subitem_affiliated_institution_position'] = institutionPosition;
                        }
                    }
                }
                isExisted = true;
                // Set read only for user information property
                $rootScope.recordsVM.invenioRecordsForm.find(function (subItem) { return subItem.key == key })['readonly'] = true;
                break;
              }
            }
          }
          return  isExisted;
        }
      };

      $scope.autoFillProfileInfo = function () {
        var needToAutoFillProfileInfo = $("#application_item_type").val();
        if (needToAutoFillProfileInfo == 'False' || $scope.isExistingUserProfile()) {
          return;
        }
        var user_info_html = $("#user_info_data").val();
        if (!user_info_html) {
          return;
        }
        var data = JSON.parse(user_info_html);
        // Key for detecting user profile info
        // These 2 keys is unique for User Information so use these to detect user_information obj
        var affiliatedDivision = 'subitem_affiliated_division/department';
        var affiliatedInstitution = 'subitem_affiliated_institution';
        // Key for dectecting affiliated institution
        var affiliatedInstitutionName = 'subitem_affiliated_institution_name';
        var affiliatedInstitutionPosition = 'subitem_affiliated_institution_position';
        var userInfoKey = null;
        for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
          var currentInvenioRecordsSchema = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
          if (currentInvenioRecordsSchema.properties) {
            let containAffiliatedDivision = currentInvenioRecordsSchema.properties.hasOwnProperty(affiliatedDivision);
            let containAffiliatedInstitution = currentInvenioRecordsSchema.properties.hasOwnProperty(affiliatedInstitution);
            if (containAffiliatedDivision && containAffiliatedInstitution) {
              // Store key of user info to disable this form later
              userInfoKey = key;
              $rootScope.recordsVM.invenioRecordsModel[key] = {};
              var currentInvenioRecordsModel = $rootScope.recordsVM.invenioRecordsModel[key];
              for (let subKey in currentInvenioRecordsSchema.properties) {
                if (currentInvenioRecordsSchema.properties[subKey].type == "array") {
                  //Affiliated institution is an array
                  let containInstitutionName = currentInvenioRecordsSchema.properties[subKey].items.properties.hasOwnProperty(affiliatedInstitutionName);
                  let containInstitutionPosition = currentInvenioRecordsSchema.properties[subKey].items.properties.hasOwnProperty(affiliatedInstitutionPosition);
                  if (containInstitutionName && containInstitutionPosition) {
                    //init the Affiliated Institution
                    currentInvenioRecordsModel[subKey] = [];
                    // get arr Affiliated institution form the result data
                    var arrAffiliatedData = data.results[subKey];
                    if (arrAffiliatedData) {
                      // Set value for each pair of Affiliated Institution data
                      arrAffiliatedData.forEach(function(value, index) {
                        currentInvenioRecordsModel[subKey][index] = {};
                        currentInvenioRecordsModel[subKey][index][affiliatedInstitutionName] = value.subitem_affiliated_institution_name;
                        let institutionPosition = $scope.translationsInstitutePosition(value.subitem_affiliated_institution_position);
                        currentInvenioRecordsModel[subKey][index][affiliatedInstitutionPosition] = institutionPosition;
                      });
                    }
                  }
                } else {
                  if (data.results[subKey]) {
                    if (subKey==='subitem_position') {
                      let position = $scope.translationsPosition(data.results[subKey]);
                      $rootScope.recordsVM.invenioRecordsModel[key][subKey] = position;
                    } else {
                      $rootScope.recordsVM.invenioRecordsModel[key][subKey] = String(data.results[subKey])
                    }
                  }
                }
              }
            }
          }
        }
        if (userInfoKey != null) {
          // Set read only for user information property
          $rootScope.recordsVM.invenioRecordsForm.find(function (subItem) { return subItem.key == userInfoKey })['readonly'] = true;
        }
      };

      $scope.isExistingTitle = function () {
        let model = $rootScope.recordsVM.invenioRecordsModel;
        if (Object.keys(model).length === 0 && model.constructor === Object) {
          return false;
        } else {
          let isExisted = false;
          for (let key in model) {
            if (model.hasOwnProperty(key) && model[key].length > 0) {
              let title = model[key][0]['subitem_item_title'];
              if (title){
                var activity_id= title.match(/A-[0-9]{8}-[0-9]{5}/g);
                if (activity_id){
                  $scope.usage_report_activity_id = activity_id[0];
                }
              }
              if (title && $("#auto_fill_title").val() !== '""') {
                $rootScope.recordsVM.invenioRecordsForm.find(function (subItem) { return subItem.key == key })['readonly'] = true;
                setTimeout(function () {
                  $("input[name='subitem_item_title'], select[name='subitem_item_title_language']").attr("disabled", "disabled");
                }, 1000);
                isExisted = true;
                break;
              }
            }
          }
          return isExisted;
        }
      };

      $scope.autoSetTitle = function () {
        if ($scope.isExistingTitle()) {
          return;
        }
        if ($("#user_info_data") !== null) {
          let titleData = $("#auto_fill_title").val();
            if (titleData ==='""' || titleData ==="") {
            return;
          }
          let titleKey = null;
          titleData = JSON.parse(titleData);
          let userName = JSON.parse($('#user_info_data').val()).results.subitem_displayname;
          for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
            var value = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
              if (value && value.type === "array" && value.items) {
                if (value.items.properties && value.items.properties.hasOwnProperty("subitem_item_title")) {
                  titleKey = key;
                  let enTitle = {};
                  enTitle['subitem_item_title'] = titleData['en'] + " - " + userName;
                  enTitle['subitem_item_title_language'] = "en";
                  let jaTitle = {};
                  jaTitle['subitem_item_title'] = titleData['ja'] + " - " + userName;
                  jaTitle['subitem_item_title_language'] = "ja";
                  $rootScope.recordsVM.invenioRecordsModel[key] = [jaTitle, enTitle];
                  break;
              }
            }
          }
          if (titleKey != null) {
            // Set read only for title
            $rootScope.recordsVM.invenioRecordsForm.find(function (subItem) { return subItem.key == titleKey })['readonly'] = true;
          }
          setTimeout(function () {
            $("input[name='subitem_item_title'], select[name='subitem_item_title_language']").attr("disabled", "disabled");
          }, 500);
        }
      };

      $scope.isExistingTitleData = function () {
        let model = $rootScope.recordsVM.invenioRecordsModel;
        if (Object.keys(model).length === 0 && model.constructor === Object) {
          return false;
        } else {
          let isExisted = false;
          for (let key in model) {
            if (model.hasOwnProperty(key)) {
              let title = model[key]['subitem_dataset_usage'];
              if (title && $("#item_title").val() !== '""') {
                if ($rootScope.recordsVM.invenioRecordsForm.find(function (subItem) { return subItem.key == key })) {
                  $rootScope.recordsVM.invenioRecordsForm.find(function (subItem) { return subItem.key == key })['readonly'] = true;
                  setTimeout(function () {
                    $("input[name='subitem_dataset_usage']").attr("disabled", "disabled");
                  }, 1000);
                }
                isExisted = true;
                break;
              }
            }
          }
          return isExisted;
        }
      };

      //Auto fill Title Data
      $scope.autoTitleData = function () {
        if ($scope.isExistingTitleData()) {
          return;
        }
        let itemTitleElement = $("#item_title");
        if (itemTitleElement !== null && itemTitleElement.val()) {
          let itemTitle = decodeURI(itemTitleElement.val());
          let titleKey = null;
          for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
            let value = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
              if (value && value.properties) {
                if (value.properties.hasOwnProperty("subitem_dataset_usage")) {
                  titleKey = key;
                  $rootScope.recordsVM.invenioRecordsModel[key] = {'subitem_dataset_usage': itemTitle};
                  break;
                }
              }
          }
          if (titleKey != null) {
            // Set read only for title
            $rootScope.recordsVM.invenioRecordsForm.find(function (subItem) { return subItem.key === titleKey })['readonly'] = true;
          }
          setTimeout(function () {
            $("input[name='subitem_dataset_usage']").attr("disabled", "disabled");
          }, 500);
        }
      };

      $scope.setDataForLicenseType = function () {
        var list_license = $("#list_license_data").val();
        if (!list_license) {
          return;
        }
        var listLicenseObj = JSON.parse(list_license);
        var licenseTypeName = 'licensetype';
        var schema = $rootScope.recordsVM.invenioRecordsSchema;
        var listLicenseTypeKey = [];

        for (let key in schema.properties) {
          let value = schema.properties[key];
          // Find form that contains license type obj
          if (value.items && value.items.properties && value.items.properties.hasOwnProperty(licenseTypeName)) {
            let listLicenseEnum = [null];
            // Collect list license
            for (let ind in listLicenseObj) {
              listLicenseEnum.push(listLicenseObj[ind]['value']);
              //set enum of license type form as list license above
              value.items.properties[licenseTypeName]['enum'] = listLicenseEnum;
              listLicenseTypeKey.push(key);
            }
          }
        }
        if (listLicenseTypeKey.length > 0) {
          let containLicenseTypeForm = null;
            for(let ind in listLicenseTypeKey){
              for(let key in $rootScope.recordsVM.invenioRecordsForm)
              {
                if($rootScope.recordsVM.invenioRecordsForm[key].key == listLicenseTypeKey[ind]){
                  containLicenseTypeForm = $rootScope.recordsVM.invenioRecordsForm[key];
                  if (containLicenseTypeForm && containLicenseTypeForm.items) {
                    licenseTypeForm = get_subitem(containLicenseTypeForm.items, 'licensetype');
                    // Set title map by listLicenseObj above
                    licenseTypeForm['titleMap'] = listLicenseObj;
                  }
                  break;
                }
              }
              if(containLicenseTypeForm){
                break;
              }
            }
        }
    }

      $scope.autoSetCorrespondingUsageAppId = function () {
        if ($scope.usage_report_activity_id != ''){
          for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
            let value = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
              if (value && value.items) {
                if (value.items.properties.hasOwnProperty("subitem_corresponding_usage_application_id")) {
                  $rootScope.recordsVM.invenioRecordsModel[key] = []
                  $rootScope.recordsVM.invenioRecordsModel[key].push({'subitem_corresponding_usage_application_id': $scope.usage_report_activity_id})
                }
              }
          }
          setTimeout(function () {
            $("[name='subitem_corresponding_usage_application_id']").attr("disabled", 'disabled');
          }, 1000);
        }
      };

      $scope.renderValidationErrorList = function () {
        const activityId = $("#activity_id").text();
        $.ajax({
          url: '/api/items/check_validation_error_msg/' + activityId,
          method: 'GET',
          async: false,
          success: function (response) {
            if (response.code) {
              // addAlert(response.msg, 'alert-danger');
              response.msg.map(function (item) {
                addAlert(item, 'alert-danger');
              })
              $scope.render_requirements = true;
              $scope.error_list = response.error_list;
            }
          },
          error: function (data) {
            alert('Cannot connect to server!');
          }
        });
      }
      $scope.showError = function () {
        if ($scope.render_requirements) {
          var check = setInterval(show, 500);
          var cnt = 0;
          function show() {
            if ($('#loader_spinner').hasClass('ng-hide')) {
              cnt++;
              $scope.$broadcast('schemaFormValidate');
              if (cnt === 3) {
                if ($scope.error_list['required'].length > 0) {
                  angular.forEach($scope.error_list['required'], function (value, key) {
                    let id = value.split('.')[1]
                    if (id) {
                      $scope.depositionForm[id].$viewValue = '';
                      $scope.depositionForm[id].$commitViewValue();
                    }
                  });
                  $scope.$broadcast('schemaFormValidate');
                }
                clearInterval(check);
              }
            }
          }
        }
      }

      /**
      * Set required and collapsed for all sub item.
      * If form required, setting "required" is true and "collapsed" is false.
      * If root panel collapse, sub panel will collapse.
      * @param {Boolean} isCollapsed.
      * @param {object} forms is item of form.
      */
      $scope.recursiveSetCollapsedForForm = function (isCollapsed, forms) {
        angular.forEach(forms, function(val, key){
          if ("key" in val && val.key) {
            let sub_item;
            if (val.key instanceof Array) {
              sub_item = val.key.pop();
            } else if (typeof(val.key) === 'string') {
              sub_item = val.key.split(".").pop()
            }
            val["collapsed"] = isCollapsed && $scope.required_list.indexOf(sub_item) === -1;
          } else {
            val["collapsed"] = isCollapsed;
          }
          if(val.hasOwnProperty('items') && val['items'] && val['items'].length > 0){
            $scope.recursiveSetCollapsedForForm(isCollapsed, val["items"]);
          }
        });
      }
      /**
      * Set required and collapsed for all root item.
      */
      $scope.setCollapsedAndRequiredForForm = function(){
        $scope.prepareRequiredList();
        let requiredList = $rootScope.recordsVM.invenioRecordsSchema.required;
        let forms = $rootScope.recordsVM.invenioRecordsForm;
        let isCollapsed;
        angular.forEach(forms, function(val, key){
          isCollapsed = requiredList.indexOf(val.key) == -1;
          val["collapsed"] = isCollapsed && $scope.required_list.indexOf(val.key) === -1;
          if(val.hasOwnProperty('items') && val['items'] && val['items'].length > 0){
            $scope.recursiveSetCollapsedForForm(isCollapsed, val["items"]);
          }
        });
      }

      /**
      * Prepare required list for expand/collapse panel.
      */
      $scope.prepareRequiredList = function () {
        let prepareRequiredList = function (json_data) {
          let temp_key;

          let pushToRequiredList = function (key) {
              if ($scope.required_list.indexOf(key) === -1) {
                $scope.required_list.push(key);
              }

              temp_key = key;
          };

          angular.forEach(json_data, function (val, key) {
              if (val.required) {
                  return pushToRequiredList(key);
              } else if (val.items) {
                  if (val.items.required) {
                      return pushToRequiredList(key);
                  } else if (prepareRequiredList(val.items.properties)) {
                      return pushToRequiredList(key);
                  }
              } else if (val.properties) {
                  if (prepareRequiredList(val.properties)) {
                      return pushToRequiredList(key);
                  }
              }
          });

          return temp_key;
        }

        let json_data = $rootScope.recordsVM.invenioRecordsSchema;
        if (json_data.required) {
          $scope.required_list = $scope.required_list.concat(json_data.required);
        }

        if ($scope.error_list && $scope.error_list['either']) {
          angular.forEach($scope.error_list['either'], function (val, key) {
            let ids = [];
            if (val instanceof Array) {
              val.map(function(x) {
                return x.split('.');
              }).forEach(function(x) {
                ids = ids.concat(x);
              });
            } else {
              ids = val.split('.');
            }
            angular.forEach(ids, function (_val, _key) {
              if ($scope.required_list.indexOf(_val) === -1) {
                $scope.required_list.push(_val);
              }
            });
          });
        }

        prepareRequiredList(json_data.properties);
      }

      $scope.loadFilesFromSession = function () {
        //When switch language, Getting files uploaded.
        let actionID = $("#activity_id").text();
        let fileData = sessionStorage.getItem(actionID);
        if (!fileData) {
          $scope.setFilesModel();
          return;
        }
        fileData = JSON.parse(fileData);
        let bucketFiles = fileData['files'];
        let bucketEndpoints = fileData['endpoints'];
        let recordsModel = fileData['recordsModel'];
        if (bucketFiles && bucketEndpoints) {
          bucketFiles = JSON.parse(bucketFiles);
          bucketEndpoints = JSON.parse(bucketEndpoints);
          recordsModel = JSON.parse(recordsModel);
          bucketEndpoints.html = '';
          $rootScope.filesVM.files = bucketFiles;
          $rootScope.filesVM.invenioFilesEndpoints = bucketEndpoints;
          if (bucketEndpoints.hasOwnProperty('bucket')) {
            $rootScope.$broadcast(
              'invenio.records.endpoints.updated', bucketEndpoints
            );
          }
          $scope.setFilesModel(recordsModel);
        }
      }

      $scope.storeFilesToSession = function () {
        //Add file uploaded to sessionStorage when uploaded processing done
        window.history.pushState("", "", $scope.currentUrl);
        let actionID = $("#activity_id").text();
        let data = {
          "files": JSON.stringify($rootScope.filesVM.files),
          "endpoints": JSON.stringify($rootScope.filesVM.invenioFilesEndpoints),
          "recordsModel": JSON.stringify($rootScope.recordsVM.invenioRecordsModel),
        }
        sessionStorage.setItem(actionID, JSON.stringify(data))
      }

      $scope.setFilesModel = function (recordsModel) {
        setTimeout(function (){
          let model = $rootScope.recordsVM.invenioRecordsModel;
          $scope.searchFilemetaKey();
          if(!$.isEmptyObject(recordsModel)){
            $scope.filemeta_keys.forEach(function (filemeta_key) {
              if($.isEmptyObject(recordsModel[filemeta_key])){
                model[filemeta_key] = [{}];
              } else {
                model[filemeta_key] = recordsModel[filemeta_key];
              }
            });
          }

          let files = $rootScope.filesVM.files;
          $scope.filemeta_keys.forEach(function (filemeta_key) {
            for (let i = 0; i < model[filemeta_key].length; i++) {
              if (model[filemeta_key][i]) {
                let modelFile = model[filemeta_key][i];
                files.forEach(function (file) {
                  if (modelFile.filename === file.key
                    && !$rootScope.isModelFileVersion(model[filemeta_key], file.version_id)) {
                    modelFile.version_id = file.version_id;
                  }
                })
              }
            }
          });

        }, 3000);
      }

      $rootScope.isModelFileVersion = function (modelFileList, versionId) {
        let rtnValue = false;
        for (let i = 0; i < modelFileList.length; i++) {
          if (modelFileList[i].version_id === versionId) {
            rtnValue = true;
            break;
          }
        }
        return rtnValue;
      }

      $rootScope.$on('invenio.records.loading.stop', function (ev) {
        $scope.hiddenPubdate();
        $scope.initContributorData();
        $scope.initUserGroups();
        $scope.loadFilesFromSession();
        $scope.initFilenameList();
        $scope.searchTypeKey();
        $scope.setDataForLicenseType();
        $scope.renderValidationErrorList();
        $scope.autoSetTitle();
        $scope.initCorrespondingIdList();
        $scope.autoTitleData();
        $scope.initAuthorList();
        $scope.getDataAuthors();
        $scope.updateNumFiles();
        //In case save activity
        hide_endpoints = $('#hide_endpoints').text()
        if (hide_endpoints.length > 2) {
          endpoints = JSON.parse($('#hide_endpoints').text());
          endpoints.html = '';
          if (endpoints.hasOwnProperty('bucket')) {
            $rootScope.$broadcast(
              'invenio.records.endpoints.updated', endpoints
            );
          }
        }

        $scope.showError();
        // Delay 3s after page render
        setTimeout(function () {
          $scope.autofillJournal();
          //Case edit: fill data to fields when page loaded.
          let model = $rootScope.recordsVM.invenioRecordsModel;
          CustomBSDatePicker.setDataFromFieldToModel(model, true);
        }, 3000);
        // Auto fill user profile
        $scope.autoFillProfileInfo();
        $scope.autoSetCorrespondingUsageAppId();
        //Set required and collapsed for all root and sub item.
        $scope.setCollapsedAndRequiredForForm();

        // Delay 0.5s after page render
        $scope.changePositionFileInterval = setInterval(function () {
          // Change position of File and Billing File
          $scope.changePositionFileName();
        }, 500);

        // Resize main content widget after optional items are collapsed
        setTimeout(function () {
          $scope.resizeMainContentWidget();
        }, 500)
      });

      /**
       * Resize main content widget after optional items are collapsed
       */
      $scope.resizeMainContentWidget = function () {
        if (typeof widgetBodyGrid !== 'undefined') {
          let mainContent = $('#main_contents');
          let width = mainContent.data("gsWidth");
          widgetBodyGrid.resizeWidget(mainContent, width, DEFAULT_WIDGET_HEIGHT);
        }
      }

      $scope.changePositionFileName = function () {
        let records = $rootScope.recordsVM.invenioRecordsForm;
        let depositionForm = $('invenio-records-form').find('form[name="depositionForm"]');
        $scope.searchFilemetaKey();
        let fileFormElements = [];
        let isClearInterval = false;
        $scope.filemeta_keys.forEach(function (filemeta_key) {
          records.forEach(function (item, i) {
            if (item.key == filemeta_key) {
              let fileElement = depositionForm
                .find('bootstrap-decorator[form="schemaForm.form[' + i + ']"]');
              if (fileElement.length) {
                fileFormElements.push(fileElement);
              }
            }
          });
        });
        if ($scope.filemeta_keys.length === 0) {
          isClearInterval = true;
        } else if (fileFormElements.length) {
          fileFormElements.forEach(function (element) {
            // Move to top
            element.prependTo(depositionForm);
          });
          isClearInterval = true;
        }
        if (isClearInterval) {
          clearInterval($scope.changePositionFileInterval);
        }
      }

      $scope.addFileFormAndFill = function () {
        let model = $rootScope.recordsVM.invenioRecordsModel;
        let filesUploaded = $rootScope.filesVM.files;
        $scope.searchFilemetaKey();
        $scope.filemeta_keys.forEach(function (filemeta_key) {
          for (var i = $scope.previousNumFiles; i < filesUploaded.length; i++) {
            let fileInfo = {};
            let fileData = filesUploaded[i];
            // Do not add the thumbnail file info to the form file.
            if (fileData.hasOwnProperty('is_thumbnail') && fileData['is_thumbnail']) {
              continue;
            }
            // Fill filename
            fileInfo['version_id'] = fileData.version_id;
            fileInfo['filename'] = fileData.key;
            // Fill size
            fileInfo.filesize = [{}]; // init array
            fileInfo.filesize[0].value = $scope.bytesToReadableString(fileData.size);
            // Fill format
            fileInfo.format = fileData.mimetype;
            // Fill Date and DateType
            fileInfo.date = [{}]; // init array
            fileInfo.date[0].dateValue = new Date().toJSON().slice(0,10);
            fileInfo.date[0].dateType = "Available";
            // Push data to model
            model[filemeta_key].push(fileInfo);
          }
        });
        // Filter empty form
        $scope.filemeta_keys.forEach(function (filemeta_key) {
          model[filemeta_key] = model[filemeta_key].filter(function (fileInfo) {
            return fileInfo.filename;
          });
        });
      }

      $scope.removeFileForm = function (version_id) {
        let model = $rootScope.recordsVM.invenioRecordsModel;
        $scope.searchFilemetaKey();
        $scope.filemeta_keys.forEach(function (filemeta_key) {
          model[filemeta_key] = model[filemeta_key].filter(function (fileInfo) {
            return fileInfo.version_id != version_id;
          });
        });
      }

      $scope.bytesToReadableString = function (bytes) {
        function round(num, precision) {
          return Math.round(num * Math.pow(10, precision)) / Math.pow(10, precision);
        }
        var limit = Math.pow(1024, 4);
        if (bytes > limit) {
            return round(bytes / limit, 1) + ' Tb';
        } else if (bytes > (limit /= 1024)) {
            return round(bytes / limit, 1) + ' Gb';
        } else if (bytes > (limit /= 1024)) {
            return round(bytes / limit, 1) + ' Mb';
        } else if (bytes > 1024) {
            return Math.round(bytes / 1024) + ' Kb';
        }
        return bytes + ' B';
      }

      // This is callback function - Please do NOT change function name
      $scope.fileNameSelect = function (modelValue) {
        let model = $rootScope.recordsVM.invenioRecordsModel;
        let filesObject = $scope.getFilesObject();
        $scope.searchFilemetaKey();
        $scope.filemeta_keys.forEach(function (filemeta_key) {
          model[filemeta_key].forEach(function (fileInfo) {
            if (fileInfo.filename == modelValue) {
              fileInfo.filesize = [{}];
              fileInfo.filesize[0].value = filesObject[modelValue].size;
              fileInfo.format = filesObject[modelValue].format;
              fileInfo.date = [{}];
              fileInfo.date[0].dateValue = new Date().toJSON().slice(0,10);
              fileInfo.date[0].dateType = "Available";
            }
          });
        });
      }

      $scope.updateNumFiles = function () {
        if (!angular.isUndefined($rootScope.filesVM)) {
          $scope.previousNumFiles = $rootScope.filesVM.files.length;
        }
      }

      $scope.getFilesObject = function () {
        let filesUploaded = $rootScope.filesVM.files;
        var filesObject = new Object();
        filesUploaded.forEach(function (file) {
          filesObject[file.key] = new Object();
          filesObject[file.key].size = $scope.bytesToReadableString(file.size);
          filesObject[file.key].format = file.mimetype;
        });
        return filesObject;
      }

      $rootScope.$on('invenio.uploader.upload.completed', function (ev) {
        $scope.initFilenameList();
        $scope.hiddenPubdate();
        $scope.addFileFormAndFill();
        $scope.updateNumFiles();
        $scope.storeFilesToSession();
        // Delay 1s after page render
        setTimeout(function() {
          // Change position of FileName
          $scope.changePositionFileName();
        }, 1000);
      });

      $scope.$on('invenio.uploader.file.deleted', function (ev, f) {
        if (f.completed) {
          $scope.initFilenameList();
          $scope.hiddenPubdate();
          $scope.removeFileForm(f.version_id);
          $scope.updateNumFiles();
          $scope.storeFilesToSession();
          // Delay 1s after page render
          setTimeout(function() {
            // Change position of FileName
            $scope.changePositionFileName();
          }, 1000);
        }
      });

      $scope.getItemMetadata = function () {
        // Reset error message befor open modal.
        this.resetAutoFillErrorMessage();
        $('#meta-search').modal('show');
      };

      $scope.hiddenPubdate = function () {
        if ($("#is_hidden_pubdate").val() !== "True"){
          return;
        }
        let pubdate = $rootScope.recordsVM.invenioRecordsForm.find(function (subItem) { return subItem.key == 'pubdate' });
        pubdate['condition'] = true;
        pubdate['required'] = false;
        if (!$rootScope.recordsVM.invenioRecordsModel["pubdate"]) {
        let now = new Date();
        let day = ("0" + now.getDate()).slice(-2);
        let month = ("0" + (now.getMonth() + 1)).slice(-2);
        let today = now.getFullYear() + "-" + (month) + "-" + (day);
          $rootScope.recordsVM.invenioRecordsModel["pubdate"] = today;
        }
      };

      $scope.setValueToField = function (id, value) {
        if (!id) {
          return;
        } else if (!$scope.depositionForm[id] || typeof $scope.depositionForm[id] != "object") {
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

      $scope.setAutoFillErrorMessage = function (message) {
        $("#autofill-error-message").text(message);
        $("#auto-fill-error-div").addClass("alert alert-danger");
      }

      $scope.resetAutoFillErrorMessage = function () {
        $("#autofill-error-message").text("");
        $("#auto-fill-error-div").removeClass("alert alert-danger");
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
        this.setRecordDataFromApi(param);
      }

      $scope.clearAllField = function () {
        $rootScope.recordsVM.invenioRecordsModel["pubdate"] = "";
        for (let item in $rootScope.recordsVM.invenioRecordsModel) {
          this.clearAllFieldCallBack($rootScope.recordsVM.invenioRecordsModel[item]);
        }
        for(let key in $scope.depositionForm){
          $scope.setValueToField($scope.depositionForm[key]);
        }
      }

      $scope.clearAllFieldCallBack = function (item) {
        if ($.isEmptyObject(item)) {
          return item;
        }
        if (Array.isArray(item)) {
          for (let i in item) {
            let subItem = item[i];
          this.clearAllFieldCallBack(subItem);
          }
        } else {
          for (let subItem in item) {
            if ($.isEmptyObject(item[subItem])) {
              continue;
            } else if (Array.isArray(item[subItem])) {
              let result = [];
              for (let i in item[subItem]) {
                let childItem = item[subItem][i];
                result.push(this.clearAllFieldCallBack(childItem));
              }
              item[subItem] = result;
            } else {
              if (typeof item[subItem] === 'string' || item[subItem] instanceof String) {
                item[subItem] = "";
              }
            }
          }
          return item;
        }
      }

      $scope.setRecordDataFromApi = function (param) {
        let request = {
          url: '/api/autofill/get_auto_fill_record_data',
          headers: {
            'Content-Type': 'application/json'
          },
          method: "POST",
          data: JSON.stringify(param),
          dataType: "json"
        };

        InvenioRecordsAPI.request(request).then(
          function success(response) {
            let data = response.data;
            if (data.error) {
              $scope.setAutoFillErrorMessage("An error have occurred!\nDetail: " + data.error);
            } else if (!$.isEmptyObject(data.result)) {
              $scope.clearAllField();
              $scope.setRecordDataCallBack(data);
            } else {
              $scope.setAutoFillErrorMessage($("#autofill_error_doi").val());
            }
          },
          function error(response) {
            $scope.setAutoFillErrorMessage("Cannot connect to server!");
          }
        );
      }

      $scope.setRecordDataCallBack = function (data) {

        data.result.forEach(function (item) {
            let model = $rootScope.recordsVM.invenioRecordsModel;
            $scope.setRecordData(model, item);
        });
        CustomBSDatePicker.setDataFromFieldToModel($rootScope.recordsVM.invenioRecordsModel, true);
        $('#meta-search').modal('toggle');
      };

      $scope.setRecordData = function (model, itemData) {
        if (Array.isArray(itemData)) {
          if (itemData.length === 1) {
            $scope.setRecordData(model[0], itemData[0]);
          } else {
            let cloneData = model[0];
            for (let key in itemData) {
              if (model[key]) {
                $scope.setRecordData(model[key], itemData[key]);
              } else {
                model.push(JSON.parse(JSON.stringify(cloneData)));
                $scope.setRecordData(model[key], itemData[key]);
              }
            }
          }
        } else if (typeof (itemData) === "object") {
          let keys = Object.keys(itemData);
          keys.forEach(function (itemKey) {
            let data = itemData[itemKey];
            if (typeof data === "string") {
              model[itemKey] = data
            } else {
              if (model) {
                if (model[itemKey]) {
                  $scope.setRecordData(model[itemKey], itemData[itemKey]);
                } else {
                  model[itemKey] = itemData[itemKey];
                }
              }
            }
          });
        }
      };

      $scope.searchSource = function (model_id, arrayFlg, form) {
        // alert(form.key[1]);
        var modalcontent = form.key[1];
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
      }
      $scope.searchAuthor = function (model_id, arrayFlg, form) {
        // add by ryuu. start 20180410
        $("#btn_id").text(model_id);
        $("#array_flg").text(arrayFlg);
        $("#array_index").text(form.key[1]);
        // add by ryuu. end 20180410
        //Reset data before show modal 'myModal'.
        window.appAuthorSearch.namespace.resetSearchData();
        $('#myModal').modal('show');
      }
      // add by ryuu. start 20180410
      $scope.setAuthorInfo = function () {
        var authorInfo = $('#author_info').text();
        var arrayFlg = $('#array_flg').text();
        var modelId = $('#btn_id').text();
        var array_index = $('#array_index').text();
        var authorInfoObj = JSON.parse(authorInfo);
        var weko_id = $('#weko_id').text();
        let creatorModel;
        if(arrayFlg == 'true'){
          creatorModel = $rootScope.recordsVM.invenioRecordsModel[modelId][array_index];
        }else{
          creatorModel = $rootScope.recordsVM.invenioRecordsModel[modelId];
        }
        angular.forEach(authorInfoObj, function(value, key) {
          creatorModel.affiliation = value.hasOwnProperty('affiliation') ? value.affiliation : [{}];
          creatorModel.creatorAlternatives = value.hasOwnProperty('creatorAlternatives') ? value.creatorAlternatives : [{}];
          creatorModel.familyNames = value.hasOwnProperty('familyNames') ? value.familyNames : [{}];
          creatorModel.givenNames = value.hasOwnProperty('givenNames') ? value.givenNames : [{}];
          creatorModel.nameIdentifiers = value.hasOwnProperty('nameIdentifiers') ? value.nameIdentifiers : [{}];
          creatorModel.creatorMails = value.hasOwnProperty('creatorMails') ? value.creatorMails : [{}];
          //creatorName = familyName + givenName
          if (value.hasOwnProperty('familyNames') && value.hasOwnProperty('givenNames')) {
            if (!value.hasOwnProperty('creatorNames')) {
              creatorModel.creatorNames = [];
            }
            for (var i = 0; i < value.familyNames.length; i++) {
              let subCreatorName = { "creatorName": "", "creatorNameLang": "" };
              let familyName = value.familyNames[i].familyName;
              let givenName = value.givenNames[i].givenName;
              subCreatorName.creatorName = familyName + " " + givenName;
              subCreatorName.creatorNameLang = value.familyNames[i].familyNameLang;
              creatorModel.creatorNames.push(subCreatorName);
            }
          }
        });
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
            success: function (data, status) {
              if (data.user_id) {
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
            success: function (data, stauts) {
              if (data.error) {
                alert('Some errors have occured!\nDetail: ' + data.error);
                //var modalcontent =  "Some errors have occured!\nDetail: " + data.error;
                //$("#inputModal").html(modalcontent);
                //$("#allModal").modal("show");
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
                    //var modalcontent = "You cannot specify yourself in "Other users" setting.";
                    //$("#inputModal").html(modalcontent);
                    //$("#allModal").modal("show");
                  } else {
                    $rootScope.recordsVM.invenioRecordsModel['shared_user_id'] = otherUser.userID;
                    result = true;
                  }
                } else {
                  alert('Shared user information is not valid\nPlease check it again!');
                  //var modalcontent = "Shared user information is not valid\nPlease check it again!";
                  //$("#inputModal").html(modalcontent);
                  //$("#allModal").modal("show");
                }
              }
            },
            error: function (data, status) {
              alert('Cannot connect to server!');
              //var modalcontent =  "Cannot connect to server!";
              //$("#inputModal").html(modalcontent);
              //$("#allModal").modal("show");
            }
          })
        } else {
          alert('Some errors have occured when edit Contributer');
          //var modalcontent =  "Some errors have occured when edit Contributer";
          //$("#inputModal").html(modalcontent);
          //$("#allModal").modal("show");
        }
        return result;
      }

      $scope.genTitleAndPubDate = function () {
        let itemTypeId = $("#autofill_item_type_id").val();
        let get_url = '/api/autofill/get_title_pubdate_id/' + itemTypeId;
        $.ajax({
          url: get_url,
          method: 'GET',
          async: false,
          success: function (data, status) {
            let title = "";
            let lang = "en";
            let titleData = data.title;
            if (titleData['title_parent_key'] && $rootScope.recordsVM.invenioRecordsModel.hasOwnProperty(titleData['title_parent_key'])) {
              tempRecord = $rootScope.recordsVM.invenioRecordsModel[titleData['title_parent_key']];
              // Get title
              if (titleData['title_value_lst_key']) {
                titleData['title_value_lst_key'].forEach(function (val) {
                  if (Array.isArray(tempRecord) && tempRecord[0].hasOwnProperty(val)) {
                    tempRecord = tempRecord[0][val];
                  }
                  else if (tempRecord.hasOwnProperty(val)) {
                    tempRecord = tempRecord[val];
                  }
                  title = tempRecord;
                });
              }
              if (titleData['title_lang_lst_key']) {
                tempRecord = $rootScope.recordsVM.invenioRecordsModel[titleData['title_parent_key']];
                // Get pubDate
                titleData['title_lang_lst_key'].forEach(function (val) {
                  if (Array.isArray(tempRecord) && tempRecord[0].hasOwnProperty(val)) {
                    tempRecord = tempRecord[0][val];
                  }
                  else if (tempRecord.hasOwnProperty(val)) {
                    tempRecord = tempRecord[val];
                  }
                  lang = tempRecord;
                });
              }
              if (!$rootScope.recordsVM.invenioRecordsModel['title']) {
                $rootScope.recordsVM.invenioRecordsModel['title'] = title;
                $rootScope.recordsVM.invenioRecordsModel['lang'] = lang;
              } else {
                if (title != "") {
                  $rootScope.recordsVM.invenioRecordsModel['title'] = title;
                  $rootScope.recordsVM.invenioRecordsModel['lang'] = lang;
                }
              }
            }
          },
          error: function (data, status) {
            //alert('Cannot connect to server!');
            var modalcontent = "Cannot connect to server!";
            $("#inputModal").html(modalcontent);
            $("#allModal").modal("show");
          }
        });
      }

      $scope.getFeedbackMailList = function() {
        const re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        $scope.feedback_emails = []
        invalid_emails = [];
        emails = []
        emails = $('#sltBoxListEmail').children('a');
        if (emails.length === 0) {
          return invalid_emails;
        }
        emails.each(function (idx) {
          email = emails[idx]
          result = re.test(String(email.text).toLowerCase());
          if (result) {
            $scope.feedback_emails.push({
              "author_id": email.attributes[1]['value'],
              "email": email.text
            })
          } else {
            invalid_emails.push(email.text);
          }
        });
        return invalid_emails;
      }

      $scope.getItemsDictionary = function (item) {
        let result = {};
        if (item.hasOwnProperty('items')) {
          let subitem = item.items;
          for (let i = 0; i < subitem.length; i++) {
            result = Object.assign(this.getItemsDictionary(subitem[i]), result);
          }
        } else if (item.key && item.key.length) {
          let title = item.title;
          if (item.hasOwnProperty('title_i18n')) {
            let currentLanguage = $("#current_language").val();
            title = item.title_i18n[currentLanguage];
          }
          result[item.key[item.key.length - 1]] = title;
        }
        return result;
      };

      $scope.validateInputData = function (activityId, steps, isAutoSetIndexAction) {
        let schemaForm = $scope.depositionForm.$error.schemaForm;
        //Get error of custom bs-datepicker fields.
        let listCusItemErrors = CustomBSDatePicker.getInvalidFieldNameList();
        if (!this.validateRequiredItem()) {
          // Check required item
          return false;
        }else if(!this.validatePosition()) {
          return false;
        } else if (!this.validateFieldMaxItems()) {
          return false;
        } else if (($scope.depositionForm.$invalid && schemaForm) || listCusItemErrors.length > 0) {
          // Check containing control or form is invalid

          let recordsForm = $rootScope.recordsVM.invenioRecordsForm;
          let itemsDict = {};
          for (let i = 0; i < recordsForm.length; i++) {
            itemsDict = Object.assign($scope.getItemsDictionary(recordsForm[i]), itemsDict);
          }
          //Get error from schemaForm
          let listItemErrors = [];
          if(schemaForm){
            for (let i = 0; i < schemaForm.length; i++) {
              let name = schemaForm[i].$name;
              if (itemsDict.hasOwnProperty(name)) {
                name = itemsDict[name];
              }
              listItemErrors.push(name);
            }
          }
          //Merge two array error to one array error.
          listItemErrors = listItemErrors.concat(listCusItemErrors);
          // Generate error message and show modal
          let message = $("#validate_error").val() + '<br/><br/>';
          message += listItemErrors.join(', ');
          $("#inputModal").html(message);
          $("#allModal").modal("show");
          return false;
        } else if (!$scope.validateEmailsAndIndexAndUpdateApprovalActions(activityId, steps, isAutoSetIndexAction)) {
          return false;
       }else{
          // Call API to validate input data base on json schema define
          let validateURL = '/api/items/validate';
          let isValid = false;
          // Remove select value empty
          let model = angular.copy($rootScope.recordsVM.invenioRecordsModel);
          angular.forEach($rootScope.recordsVM.invenioRecordsModel, function (value, key) {
            if (value instanceof Object) {
              angular.forEach(value, function (_value, _key) {
                if (_value == '') {
                  delete model[key][_key];
                }
              });
              if (angular.equals(model[key], {})) {
                delete model[key];
              }
            }
          });
          let request = InvenioRecordsAPI.prepareRequest(
            validateURL,
            'POST',
            model,
            $rootScope.recordsVM.invenioRecordsArgs,
            $rootScope.recordsVM.invenioRecordsEndpoints
          );
          let requestData = {
            'item_id': $("#autofill_item_type_id").val(),
            'data': request.data
          }
          $.ajax({
            url: validateURL,
            method: 'POST',
            data: JSON.stringify(requestData),
            contentType: "application/json",
            async: false,
            success: function (data, status) {
              if (data.is_valid) {
                isValid = true;
              } else {
                $("#inputModal").html(data.error);
                $("#allModal").modal("show");
                isValid = false;
              }
            },
            error: function (data, status) {
              var modalcontent = data;
              $("#inputModal").html(modalcontent);
              $("#allModal").modal("show");
              isValid = false;
            }
          });
          return isValid;
        }
      };

      $scope.validateFieldMaxItems = function () {
        let isValid = true;
        for (let key in $rootScope.recordsVM.invenioRecordsModel) {
          let value = $rootScope.recordsVM.invenioRecordsModel[key];
          if (value && value.hasOwnProperty('subitem_field') &&
              Array.isArray(value['subitem_field']) && value['subitem_field'].length > 2) {
              let errorMessage = $("#validate_maxitems_field").val();
              $("#inputModal").html(errorMessage);
              $("#allModal").modal("show");
              isValid = false;
              return isValid;
            }
          }
        return isValid;
      };

      $scope.validatePosition = function () {
        var result = true;
        var subItemPosition = '';
        var subItemPositionOther = '';
        var subItemAdvisorPosition = 'subitem_advisor_position';
        var subItemAdvisorPositionOther = 'subitem_advisor_position(other)';
        var subItemGuarantorPosition = 'subitem_guarantor_position';
        var subItemGuarantorPositionOther = 'subitem_guarantor_position(other)';
        var otherChoice = "Others (Input Detail)";
        for (let key in $rootScope.recordsVM.invenioRecordsSchema.properties) {
            if (result) {
              var currentInvenioRecordsSchema = $rootScope.recordsVM.invenioRecordsSchema.properties[key];
              if (currentInvenioRecordsSchema.properties) {
                let containSubItemPosition = false;
                if (currentInvenioRecordsSchema.properties.hasOwnProperty(subItemAdvisorPosition) &&
                  currentInvenioRecordsSchema.properties.hasOwnProperty(subItemAdvisorPositionOther)) {
                  subItemPosition = subItemAdvisorPosition;
                  subItemPositionOther = subItemAdvisorPositionOther;
                  containSubItemPosition = true;
                } else if (currentInvenioRecordsSchema.properties.hasOwnProperty(subItemGuarantorPosition) &&
                  currentInvenioRecordsSchema.properties.hasOwnProperty(subItemGuarantorPositionOther)) {
                  subItemPosition = subItemGuarantorPosition;
                  subItemPositionOther = subItemGuarantorPositionOther;
                  containSubItemPosition = true;
                }
                if (containSubItemPosition) {
                  var currentInvenioRecordsModel = $rootScope.recordsVM.invenioRecordsModel;
                  var subItemPositionValue = currentInvenioRecordsModel[key][subItemPosition];
                  var subItemPositionOtherValue = currentInvenioRecordsModel[key][subItemPositionOther];
                  if (subItemPositionValue != otherChoice && typeof subItemPositionOtherValue != "undefined" && subItemPositionOtherValue != '') {
                    //Show error same
                    let message = $("#err_input_other_position").val();
                    $("#inputModal").html(message);
                    $("#allModal").modal("show");
                    result = false;
                    return false;
                  } else if (subItemPositionValue == otherChoice && (subItemPositionOtherValue == '' || subItemPositionOtherValue == undefined)) {
                    let message = $("#err_position_not_provided").val();
                    $("#inputModal").html(message);
                    $("#allModal").modal("show");
                    result = false;
                    return false;
                  }
                }
              }
            }
          }
        return result;
      }

      // This method use to do these 3 things:
      // -Validate input approval email
      // -Set approval user for each action corresponding
      // -Validate index existence(if any)
      $scope.validateEmailsAndIndexAndUpdateApprovalActions = function (activityId, steps, isAutoSetIndexAction) {
        let emailsToValidate = [];
        let actionEndpointKey = $("#action_endpoint_key").val();
        let approvalMailSubKey = $("#approval_email_key").val();
        if (actionEndpointKey === "" || approvalMailSubKey === "") {
          return true;
        }
        actionEndpointKey = JSON.parse(actionEndpointKey);
        approvalMailSubKey = JSON.parse(approvalMailSubKey);
        let param = {};
        steps.forEach(function (step) {
          if (step.ActionEndpoint == actionEndpointKey.approval1 && approvalMailSubKey.approval1) {
            emailsToValidate.push('email_approval1');
            let subitemApprovalMailAddress = $scope.depositionForm[approvalMailSubKey.approval1];
            let mail_adress = '';
            if (subitemApprovalMailAddress) {
              mail_adress = subitemApprovalMailAddress.$modelValue;
            }
            param['email_approval1'] = {
              'mail': mail_adress,
              'action_id': step.ActionId
            }
          } else if (step.ActionEndpoint == actionEndpointKey.approval2 && approvalMailSubKey.approval2) {
            emailsToValidate.push('email_approval2');
            let subitemApproval2MailAddress = $scope.depositionForm[approvalMailSubKey.approval2];
            let mail_adress = '';
            if (subitemApproval2MailAddress) {
              mail_adress = subitemApproval2MailAddress.$modelValue;
            }
            param['email_approval2'] = {
              'mail': mail_adress,
              'action_id': step.ActionId
            }
          }
        });
        param['activity_id'] = activityId;
        param['user_to_check'] = emailsToValidate;
        param['auto_set_index_action'] = isAutoSetIndexAction;
        var itemsDict = {};
        let recordsForm = $rootScope.recordsVM.invenioRecordsForm;
        for (let i = 0; i < recordsForm.length; i++) {
          itemsDict = Object.assign($scope.getItemsDictionary(recordsForm[i]), itemsDict);
        }
        return this.sendValidationRequest(param, itemsDict, isAutoSetIndexAction, approvalMailSubKey);
      };

      $scope.sendValidationRequest = function (param, itemsDict, isAutoSetIndexAction, approvalMailSubKey) {
        let result = true;
        $.ajax({
          context: this,
          url: '/api/items/validate_email_and_index',
          headers: {
            'Content-Type': 'application/json'
          },
          method: 'POST',
          async: false,
          data: JSON.stringify(param),
          dataType: "json",
          success: function (data, status) {
            let listEmailErrors = [];
            if (param.email_approval1 && param.email_approval2) {
              result = this.processResponseEmailValidation(itemsDict, data.email_approval1, approvalMailSubKey.approval1, listEmailErrors) + this.processResponseEmailValidation(itemsDict, data.email_approval2, approvalMailSubKey.approval2, listEmailErrors);
            }
            else{
              if (param.email_approval1){
                result = this.processResponseEmailValidation(itemsDict, data.email_approval1, approvalMailSubKey.approval1, listEmailErrors)
              }
              if (param.email_approval2) {
                result = this.processResponseEmailValidation(itemsDict, data.email_approval2, approvalMailSubKey.approval2, listEmailErrors);
              }
            }
            if (listEmailErrors.length > 0) {
              let message = $("#validate_email_register").val() + '<br/><br/>';
              message += listEmailErrors[0];
              for (let k = 1; k < listEmailErrors.length; k++) {
                let subMessage = ', ' + listEmailErrors[k];
                message += subMessage;
              }
              $("#inputModal").html(message);
              $("#allModal").modal("show");
              result = false;
            }
            if (isAutoSetIndexAction && !data.index) {
              let error_message = $("#not_existed_index_tree_err").val() + '<br/><br/>';
              $("#inputModal").html(error_message);
              $("#allModal").modal("show");
              result = false;
            }
          },
          error: function (data, status) {
            $("#inputModal").html("Cannot connect to server!");
            $("#allModal").modal("show");
            result = false;
          }
        });
        return result;
      };

      $scope.processResponseEmailValidation = function (itemsDict, emailData, subKey, errorList) {
        let validationResult = true;
        if (emailData) {
          if (emailData.error && typeof emailData.validation !== 'undefined') {
            $("#inputModal").html(emailData.error);
            $("#allModal").modal("show");
            validationResult = false;
          } else if (!emailData.validation) {
            validationResult = false;
            let mailAddressItem = $scope.depositionForm[subKey];
            if (mailAddressItem) {
              let name = mailAddressItem.$name;
              if (itemsDict.hasOwnProperty(name)) {
                name = itemsDict[name];
              }
              errorList.push(name);
            }
          }
        }
        return validationResult;
      }

      $scope.priceValidator = function () {
        var result = true;
        $scope.filemeta_keys.forEach(function (filemeta_key) {
          groupsprice_record = $rootScope.recordsVM.invenioRecordsModel[filemeta_key];
          if (!Array.isArray(groupsprice_record)){
            return result;
          }
          groupsprice_record.forEach(function (record) {
            prices = record.groupsprice;
            if (!prices) {
              return;
            }
            prices.forEach(function (price) {
              if (price.price && isNaN(price.price)) {
                result = false;
              }
            });
          });
        });
        return result;
      }

      $scope.findRequiredItemInSchemaForm = function (item) {
        let result = [];
        if (item.hasOwnProperty('items')) {
          let subitem = item.items;
          for (let i = 0; i < subitem.length; i++) {
            result.push.apply(result, this.findRequiredItemInSchemaForm(subitem[i]));
          }
        } else {
          if (item.required) {
            let newData = {
              'title': '',
              'id': '',
            }
            if (item.hasOwnProperty('title_i18n')) {
              let currentLanguage = $("#current_language").val();
              newData['title'] = item.title_i18n[currentLanguage];
            }
            if (!newData['title']) {
              newData['title'] = item.title;
            }
            newData['id'] = item.key[item.key.length - 1]
            result.push(newData);
          }
        }
        return result;
      }

      $scope.checkEitherRequired = function(depositionForm) {
        let eitherRequireds = [];
        if ($scope.error_list) {
          eitherRequireds = $scope.error_list['either'];
        }

        if (!eitherRequireds) {
          return true;
        }

        for (let i = 0; i < eitherRequireds.length; i++) {
          if (eitherRequireds[i] instanceof Array) {
            let check = true;
            for (let y = 0; y < eitherRequireds[i].length; y++) {
              let sub_item = eitherRequireds[i][y].split('.').pop();
              if (sub_item in depositionForm && depositionForm[sub_item].$viewValue) {
                check = check && true;
              } else {
                check = check && false;
              }
            }

            if (check) {
              return true;
            }
          } else {
            let sub_item = eitherRequireds[i].split('.').pop();
            if (sub_item in depositionForm && depositionForm[sub_item].$viewValue) {
              return true;
            }
          }
        }

        return false;
      }

      $scope.validateRequiredItem = function () {
        let schemaForm = $rootScope.recordsVM.invenioRecordsForm;
        let depositionForm = $scope.depositionForm;
        let listItemErrors = [];
        let eitherRequired = [];
        let noEitherError = $scope.checkEitherRequired(depositionForm);
        if (noEitherError && $scope.error_list && $scope.error_list['either']) {
          eitherRequired = [];
          $scope.error_list['either'].forEach(function(item) {
            if (item instanceof Array) {
              item.forEach(function(i) {
                eitherRequired.push(i.split('.').pop());
              });
            } else {
              eitherRequired.push(item.split('.').pop());
            }
          });
        }
        for (let i = 0; i < schemaForm.length; i++) {
          let listSubItem = $scope.findRequiredItemInSchemaForm(schemaForm[i])
          if (listSubItem.length == 0) {
            continue;
          }
          for (let j = 0; j < listSubItem.length; j++) {
            if (!depositionForm[listSubItem[j].id].$viewValue) {
              if (depositionForm[listSubItem[j].id].$name == "pubdate") {
                depositionForm[listSubItem[j].id].$setViewValue(null);
              } else {
                depositionForm[listSubItem[j].id].$setViewValue("");
              }
              if (noEitherError && eitherRequired) {
                if (eitherRequired.indexOf(listSubItem[j].id) === -1) {
                  listItemErrors.push(listSubItem[j].title);
                }
              } else {
                listItemErrors.push(listSubItem[j].title);
              }
            }
          }
        }

        // Handle validate radio_version
        if ($("#react-component-version").length != 0) {
          let versionSelected = $("input[name='radioVersionSelect']:checked").val();
          if (versionSelected == undefined) {
            var versionHeader = $("#component-version-label").text().trim();
            listItemErrors.push(versionHeader);
            $("#react-component-version").addClass("has-error");
          }
        }

        if (listItemErrors.length > 0) {
          let message = $("#validate_error").val() + '<br/><br/>';
          message += listItemErrors[0];
          for (let k = 1; k < listItemErrors.length; k++) {
            let subMessage = ', ' + listItemErrors[k];
            message += subMessage;
          }
          $("#inputModal").html(message);
          $("#allModal").modal("show");
          return false;
        }
        return true;
      }

      $scope.updateDataJson = function (activityId, steps, item_save_uri, currentActionId, isAutoSetIndexAction, enableContributor, enableFeedbackMail) {
        $scope.saveDataJson(item_save_uri, currentActionId, isAutoSetIndexAction, enableContributor, enableFeedbackMail);
        if (!$scope.priceValidator()) {
            var modalcontent = "Billing price is required half-width numbers.";
            $("#inputModal").html(modalcontent);
            $("#allModal").modal("show");
            return false;
        } else if (enableFeedbackMail === 'True' && $scope.getFeedbackMailList().length > 0) {
          let modalcontent = $('#invalid-email-format').val();
          $("#inputModal").html(modalcontent);
          $("#allModal").modal("show");
          return false;
        }
        let isValid = this.validateInputData(activityId, steps, isAutoSetIndexAction);
        if (!isValid) {
          return false;
        } else {
          $scope.genTitleAndPubDate();
          this.mappingThumbnailInfor();
          let next_frame = $('#next-frame').val();
          let next_frame_upgrade = $('#next-frame-upgrade').val();
          let next_frame_edit = $('#next-frame-edit').val();
          if (enableContributor === 'True' && !this.registerUserPermission()) {
            // Do nothing
          } else if (enableFeedbackMail === 'True' && !this.saveFeedbackMailListCallback(currentActionId)) {
            // Do nothing
          } else {
            $scope.addApprovalMail();
            var jsonObj = $scope.cleanJsonObject($rootScope.recordsVM.invenioRecordsModel);
            var str = JSON.stringify(jsonObj);
            var indexOfLink = str.indexOf("authorLink");
            if (indexOfLink != -1) {
              str = str.split(',"authorLink":[]').join('');
            }
            if (enableFeedbackMail === 'True') {
              if (!$scope.saveFeedbackMailListCallback(currentActionId)) {
                return false;
              }
            }
            $rootScope.recordsVM.invenioRecordsModel = JSON.parse(str);
            //If CustomBSDatePicker empty => remove attr.
            CustomBSDatePicker.removeLastAttr($rootScope.recordsVM.invenioRecordsModel);

            let title = $rootScope.recordsVM.invenioRecordsModel['title'];
            let shareUserID = $rootScope.recordsVM.invenioRecordsModel['shared_user_id'];
            $scope.saveTilteAndShareUserID(title, shareUserID);
            $scope.updatePositionKey();
            sessionStorage.removeItem(activityId);
            let versionSelected = $("input[name='radioVersionSelect']:checked").val();
            if ($rootScope.recordsVM.invenioRecordsEndpoints.initialization.includes("redirect")) {
              if (versionSelected == "keep") {
                $rootScope.recordsVM.actionHandler(
                  ["edit", "PUT"],
                  next_frame_edit
                );
              } else if (versionSelected == "update") {
                $rootScope.recordsVM.actionHandler(
                  [
                    ["newversion", "PUT"],
                    ["index_upgrade", "PUT"],
                  ],
                  next_frame_upgrade
                );
              }
            } else {
              $rootScope.recordsVM.actionHandler(['index', 'PUT'], next_frame);
            }
          }
        }
      };

      /* Delete all empty and null Nodes in a JSON Object tree */
      $scope.cleanJsonObject = function(obj) {
        obj = JSON.parse(JSON.stringify(obj, function (k, v) {
          /* Filter empty and null value */
          return !v ? void 0 : v;
        }));
        while (!$scope.isJsonCleaned(obj)) {
          obj = JSON.parse(JSON.stringify(obj, function (k, v) {
            /* Filter empty Objects */
            return JSON.stringify(v) === JSON.stringify({}) ? void 0 : v;
          }));
          obj = JSON.parse(JSON.stringify(obj, function (k, v) {
            /* Filter null values and empty Arrays */
            if (Array.isArray(v)) {
              v = v.filter(function(value, index, arr){
                return value !== null;
              });
            }
            return JSON.stringify(v) === JSON.stringify([]) ? void 0 : v;
          }));
        }
        return obj;
      }

      /* Check if the JSON Object tree contains empty object by recursive method */
      $scope.isJsonCleaned = function(obj) {
        if (typeof obj === 'object') {
          if (jQuery.isEmptyObject(obj)) {
            return false;
          } else {
            for (var key in obj) {
              if (!$scope.isJsonCleaned(obj[key])) {
                 return false;
               }
            }
          }
        }
        return true;
      }

      $scope.saveTilteAndShareUserID = function(title, shareUserID) {
        let activityID = $('#activity_id').text();
        let data = {
          'title': title,
          'shared_user_id': shareUserID,
          'activity_id': activityID
        }
        $.ajax({
          url: '/api/items/save_title_and_share_user_id',
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          data: JSON.stringify(data),
          dataType: 'json',
          success: function(response){

          }
        });
      }

      $scope.addApprovalMail = function () {
        let approvalMailSubKey = $("#approval_email_key").val();
        if (approvalMailSubKey === "") {
          return;
        }
        approvalMailSubKey = JSON.parse(approvalMailSubKey);
        // Add approval1, approval2 mail in oder to save to db
        let approval1Mail = '';
        let approval2Mail = '';
        $.each($rootScope.recordsVM.invenioRecordsModel, function (k, v) {
          if (v != undefined) {
            if (approvalMailSubKey.approval1 && v[approvalMailSubKey.approval1] != undefined) {
              approval1Mail = v[approvalMailSubKey.approval1];
            }
            if (approvalMailSubKey.approval2 && v[approvalMailSubKey.approval2] != undefined) {
              approval2Mail = v[approvalMailSubKey.approval2];
            }
          }
        });
        $rootScope.recordsVM.invenioRecordsModel['approval1'] = approval1Mail;
        $rootScope.recordsVM.invenioRecordsModel['approval2'] = approval2Mail;
      };

      $scope.saveDataJson = function (item_save_uri, currentActionId, enableContributor, enableFeedbackMail) {
        //When press 'Next' or 'Save' button, setting data for model.
        //This function is called in updataDataJson function.
        let model = $rootScope.recordsVM.invenioRecordsModel;
        CustomBSDatePicker.setDataFromFieldToModel(model, false);

        var invalidFlg = $('form[name="depositionForm"]').hasClass("ng-invalid");
        let permission = false;
        $scope.$broadcast('schemaFormValidate');
        if (enableFeedbackMail === 'True' && enableContributor === 'True') {
          if (!invalidFlg && $scope.is_item_owner) {
            if (!this.registerUserPermission()) {
              // Do nothing
            } else {
              permission = true;
            }
          }else {
            permission = true;
          }
          if (permission) {
            if ($scope.getFeedbackMailList().length > 0) {
              let modalcontent = $('#invalid-email-format').val();
              $("#inputModal").html(modalcontent);
              $("#allModal").modal("show");
              return;
            }
            this.saveDataJsonCallback(item_save_uri);
            this.saveFeedbackMailListCallback(currentActionId);
          }
        }else{
            this.saveDataJsonCallback(item_save_uri);
        }
      };

      $scope.saveDataJsonCallback = function (item_save_uri) {
        $scope.unattachedSystemProperties();
        var metainfo = { 'metainfo': $rootScope.recordsVM.invenioRecordsModel };
        if (!angular.isUndefined($rootScope.filesVM)) {
          this.mappingThumbnailInfor();
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
            //When save: date fields data is lost, so this will fill data.
            let model = $rootScope.recordsVM.invenioRecordsModel;
            CustomBSDatePicker.setDataFromFieldToModel(model, true);
            addAlert(response.data.msg);
          },
          function error(response) {
            //alert(response);
            var modalcontent = response;
            if (response.status == 400) {
              window.location.reload();
            } else {
              $("#inputModal").html(modalcontent);
              $("#allModal").modal("show");
            }
          }
        );
      }

      $scope.saveFeedbackMailListCallback = function (cur_action_id) {
        const activityID = $("#activity_id").text();
        const actionID = cur_action_id;// Item Registration's Action ID
        let emails = $scope.feedback_emails;
        let result = true;
        if (!emails.length) return true

        $.ajax({
          url: '/workflow/save_feedback_maillist/'+ activityID+ '/'+ actionID,
          headers: {
            'Content-Type': 'application/json'
          },
          method: 'POST',
          async: false,
          data: JSON.stringify(emails),
          dataType: "json",
          success: function(data, stauts) {
          },
          error: function(data, status) {
            var modalcontent =  "Cannot save Feedback-Mail list!";
            $("#inputModal").html(modalcontent);
            $("#allModal").modal("show");
            result = false;
          }
        });
        return result;
      };

      // mapping URL & Name of file
      $scope.mappingThumbnailInfor = function () {
        if (!angular.isUndefined($rootScope.filesVM)
          && !angular.isUndefined($rootScope.$$childHead.model)
          && !angular.equals([], $rootScope.$$childHead.model.thumbnailsInfor)) {
          // search thumbnail form
          let thumbnailItemKey = this.searchThumbnailForm();
          let subThumbnailKey = 'subitem_thumbnail';
          let subThumbnailLabelKey = 'thumbnail_label';
          let subThumbnailUrlKey = 'thumbnail_url';
          if (thumbnailItemKey) {
            var thumbnail_list = [];

            $rootScope.filesVM.files.forEach(function (file) {
              if (file.is_thumbnail) {
                var file_form = {};
                file_form[subThumbnailLabelKey] = file.key;
                var deposit_files_api = $("#deposit-files-api").val();
                file_form[subThumbnailUrlKey] = deposit_files_api + (file.links ? (file.links.version || file.links.self).split(deposit_files_api)[1] : '');
                thumbnail_list.push(file_form);
              }
            });
            if (thumbnail_list.length > 0) {
              let recordModel = $rootScope.recordsVM.invenioRecordsModel;
              if ($rootScope.$$childHead.model.allowMultiple == 'True') {
                recordModel[thumbnailItemKey] = [];
                var sub_item = {};
                sub_item[subThumbnailKey] = thumbnail_list;
                recordModel[thumbnailItemKey].push(sub_item);
              } else {
                recordModel[thumbnailItemKey] = {};
                recordModel[thumbnailItemKey][subThumbnailKey] = thumbnail_list;
              }
            }
          }
        }
      }

      $scope.searchThumbnailForm = function () {
        let thumbnailItemKey = '';
        let recordSchema = $rootScope.recordsVM.invenioRecordsSchema;
        for (let key in recordSchema.properties) {
          let value = recordSchema.properties[key];
          var properties = value.properties ? value.properties : (value.items ? value.items.properties : [])
          if (Object.keys(properties).indexOf('subitem_thumbnail') >= 0) {
            thumbnailItemKey = key;
            break;
          }
        }
        return thumbnailItemKey;
      }

      $scope.unattachedSystemProperties = function () {
        // Remove system file properties from metadata
        delete $rootScope.recordsVM.invenioRecordsModel.system_file;
        delete $rootScope.recordsVM.invenioRecordsModel.system_identifier_doi;
        delete $rootScope.recordsVM.invenioRecordsModel.system_identifier_hdl;
        delete $rootScope.recordsVM.invenioRecordsModel.system_identifier_uri;
        delete $rootScope.recordsVM.invenioRecordsModel.updated_date;
        delete $rootScope.recordsVM.invenioRecordsModel.created_date;
        delete $rootScope.recordsVM.invenioRecordsModel.persistent_identifier_doi;
        delete $rootScope.recordsVM.invenioRecordsModel.persistent_identifier_h;
        delete $rootScope.recordsVM.invenioRecordsModel.ranking_page_url;
        delete $rootScope.recordsVM.invenioRecordsModel.belonging_index_info;
      }
    }
    // Inject depedencies
    WekoRecordsCtrl.$inject = [
      '$scope',
      '$rootScope',
      'InvenioRecordsAPI',
    ];
    angular.module('wekoRecords.controllers', [])
      .controller('WekoRecordsCtrl', WekoRecordsCtrl);

    var ModalInstanceCtrl = function ($scope, $modalInstance, items) {
      $scope.items = items;
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
        $scope.items.push($scope.searchSchemaIdentifierKey);
      }
    };

    angular.module('wekoRecords', [
      'invenioRecords',
      'wekoRecords.controllers',
    ]);

    angular.module('uploadThumbnail', ['schemaForm', 'invenioFiles'])
    .controller('UploadController', function ($scope, $rootScope, InvenioFilesAPI) {
        'use strict';
        $scope.schema = {
            type: 'object',
            title: 'Upload',
            properties: {
                "thumbnail": {
                    "title": "thumbnail",
                    "type": 'string',
                    "format": 'file'
                }
            }
        };
        $scope.form = [
            {
                "key": "thumbnail",
                "type": "fileUpload"
            }
        ];
        $scope.model = {
            thumbnailsInfor: [],
            allowedType: ['image/gif', 'image/jpg', 'image/jpe', 'image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/tif'],
            allowMultiple: $("#allow-thumbnail-flg").val(),
        };


        $scope.$on('invenio.records.loading.stop', function () {
          let thumbnailsInfor;
          let files = $rootScope.filesVM.files;
          if (Array.isArray(files) && files.length > 0) {
            thumbnailsInfor = files.filter(function (file) {
              return (file.hasOwnProperty('is_thumbnail') && file['is_thumbnail'])
            });
          } else {
            thumbnailsInfor = $("form[name='uploadThumbnailForm']").data('files-thumbnail');
          }
          // set current data thumbnail if has
          if (thumbnailsInfor.length > 0) {
            $scope.model.thumbnailsInfor = thumbnailsInfor;
          }
        });

        // click input upload files
        $scope.uploadThumbnail = function() {
          if ($rootScope.filesVM.invenioFilesEndpoints.bucket === undefined) {
            InvenioFilesAPI.request({
                method: 'POST',
                url: $rootScope.filesVM.invenioFilesEndpoints.initialization,
                data: {},
                headers: ($rootScope.filesVM.invenioFilesArgs.headers !== undefined) ? $rootScope.filesVM.invenioFilesArgs.headers : {}
            }).then(function success(response) {
                $rootScope.filesVM.invenioFilesArgs.url = response.data.links.bucket;
                $rootScope.$broadcast(
                  'invenio.records.endpoints.updated', response.data.links
                );
            }, function error(response) {
            });
          }
          setTimeout(function() {
              document.getElementById('selectThumbnail').click();
          }, 0);
        };

        $scope.updateFileList = function(removeFile) {
          let model = $scope.model;
          model['thumbnailsInfor'] = model['thumbnailsInfor'].filter(function(fileInfo) {
            return !(fileInfo.lastModified === removeFile.lastModified
              && fileInfo.key === removeFile.key);
          });
        }

        // Get file links
        $scope.getFileLinks = function(file) {
          let fileLink = $rootScope.filesVM.files.filter(function (fileInfo) {
            return fileInfo.is_thumbnail && fileInfo.key === file.key;
          })
          let links;
          if (Array.isArray(fileLink) && fileLink.length > 0) {
            links = fileLink[0].links;
          }
          return links;
        }

        // remove file
        $scope.removeThumbnail = function (file) {
          if (angular.isUndefined(file.links)) {
            let links = $scope.getFileLinks(file);
            if (links) {
              file.links = links;
            } else {
              console.log('File not found!');
              return;
            }
          }
          $rootScope.filesVM.remove(file);
          $scope.updateFileList(file);
        };

    }).$inject = [
      '$scope',
      '$rootScope',
      'InvenioFilesAPI',
    ];

    angular.bootstrap(
      document.getElementById('weko-records'), [
        'wekoRecords', 'invenioRecords', 'mgcrea.ngStrap',
        'mgcrea.ngStrap.modal', 'pascalprecht.translate', 'ui.sortable',
        'ui.select', 'mgcrea.ngStrap.select', 'mgcrea.ngStrap.datepicker',
        'mgcrea.ngStrap.helpers.dateParser', 'mgcrea.ngStrap.tooltip',
        'invenioFiles', 'uploadThumbnail'
      ]
    );
  });
})(angular);
