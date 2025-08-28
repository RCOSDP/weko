(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function () {
    angular.module('wekoRecords.controllers', []);

    function WekoRecordsCtrl($scope, $rootScope, $modal, InvenioRecordsAPI) {
      $rootScope.$on('invenio.records.loading.stop', function (ev) {
        setTimeout(function () {
          let model = $rootScope.recordsVM.invenioRecordsModel;
          CustomBSDatePicker.setDataFromFieldToModel(model, true);
        }, 1000);
      });
      $scope.saveData = function () {

        const form1Data = new FormData(document.getElementsByClassName('admin-form form-horizontal')[0]);

        var metainfo = { 'metainfo': $rootScope.recordsVM.invenioRecordsModel };
        form2Data = new FormData();
        form2Data.append('catalog_data', JSON.stringify(metainfo));

        for (const [key, value] of form2Data) {
          form1Data.append(key, value);
        }

        fetch('', {
          method: 'POST',
          body: form1Data,
        }).then(response => {
          if (response.ok) {
            const url = new URL(response.url);
            let params = url.searchParams;
            if (params.get('pageaddFlag') == 'False') {
              alert('The community was successfully saved, but there are additional pages that failed to be created.');
              window.location.href = url.pathname;
            }
            else {
              alert('Successfully saved.');
              window.location.href = response.url;
            }
          } else {
            return response.text().then(text => {
              let errorMsg;
              try {
                // parse JSON error response
                const errorObj = JSON.parse(text);
                if (errorObj.error && errorObj.message) {
                  if (errorObj.error === "ValidationError") {
                    errorMsg = errorObj.message;
                  } else {
                    errorMsg = errorObj.error + ": " + errorObj.message;
                  }
                } else {
                  // if the JSON does not have expected fields, use the whole text
                  errorMsg = text;
                }
              } catch (e) {
                // not a JSON response
                errorMsg = text || 'Unknown error occurred';
              }
              throw new Error(errorMsg);
            });
          }
        }).catch(error => {
          alert(error.message);
        });
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
    let checkMonth = month >= 0 && month < 12;
    let checkDay = d > 0 && d <= CustomBSDatePicker.daysInMonth(month, y);
    return checkMonth && checkDay;
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
      $element.addClass('ng-invalid');
    } else {
      $element.removeClass('ng-invalid');
      $this_parent.removeClass('has-error');
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
    if ($(element).val().length == 0) return;
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
        try {
          eval(str_code);
        } catch (e) {
          // If the date on model is undefined, we can safetly ignore it.
          if (!e instanceof TypeError) {
            throw e;
          }
        }
      } else {
        //Fill data from fields to model
        str_code = 'if ($(val).val().length != 0) {' + $(val).attr('ng-model') + '=$(val).val()}';
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
  removeLastAttr: function (model) {
    let cls = CustomBSDatePicker.option.cls;
    let element_arr = $('.' + cls);
    $.each(element_arr, function (ind, val) {
      if ($(val).val().length > 0) {
        CustomBSDatePicker.initAttributeForModel(model, val);
        let ng_model = $(val).attr('ng-model');
        let last_index = ng_model.lastIndexOf('[');
        let previous_attr = ng_model.substring(0, last_index);
        let str_code = "if(" + ng_model + "==''){" + previous_attr + "={}}";
        eval(str_code);
      }
    });
  }
}

$(document).ready(function () {
  $('#content_policy').trumbowyg({
    autogrow: true,
    tagsToRemove: ['script', 'link'],
    svgPath: '/static/node_modules/trumbowyg/dist/ui/icons.svg',
    btns: [
      ["viewHTML"],
      ["undo", "redo"],
      ["formatting"],
      ['fontfamily', 'fontsize'],
      ["strong", "em", "del", 'underline', "superscript", "subscript"],
      ['foreColor', 'backColor'],
      ["link"],
      ['table'],
      ["justifyLeft", "justifyCenter", "justifyRight", "justifyFull"],
      ["unorderedList", "orderedList"],
      ["horizontalRule"],
      ["removeformat"],
      ["fullscreen"]
    ],
  });
});