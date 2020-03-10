require([
  "jquery",
  "bootstrap"
], function () {

  $(document).ready(function () {
    setDatePickerFormSearch();
    autoFilterSearch();
    changeParamPages();
  });

  $('#filter_form_submit').on('click', function () {
    submitFilterSearch();
  });
  function changeParamPages() {
    if ($('#change_page_param').length == 1) {
      let result = [];
      if (window.location.search != '') {
        let locationParam = window.location.search.split('?')[1].split('&');
        for (let key in locationParam) {
          let param = {};
          param.name = locationParam[key].split('=')[0];
          if (param.name == $("#change_page_param").val()) {
            param.value = 1;
          }
          else {
            param.value = locationParam[key].split('=')[1];
          }
          result.push(param);
        }
      }
      let urlEncodedDataPairs = [];
      for (let key in result) {
        result[key].name = decodeURIComponent(result[key].name.replace(/\+/g, ' '));
        result[key].value = decodeURIComponent(result[key].value.toString().replace(/\+/g, ' '));
        urlEncodedDataPairs.push(encodeURIComponent(result[key].name) + '=' + encodeURIComponent(result[key].value));
      }
      window.history.pushState("", "", '?' + urlEncodedDataPairs.join('&').replace(/%20/g, '+'));
    }
  }

  $("#page_count").change(function () {
    window.location.href = creatURL(createParamArray($(this).val(), getSizeAndPagesName('size')));
  });

  $(".get-pages").click(function () {
    window.location.href = creatURL(createParamArray($(this).data('pages'), getSizeAndPagesName('pages')));
  });

  $(".activity_tab").click(function () {
    window.location.href = creatURL(createParamArray($(this).data('tab'), 'tab'));
  });

  $('.filter_option').on('click', function () {
    addFilterRow($(this).text(), $(this).data('name'), '');
  });

  $("#filter_form").on("click", ".remove_row", function (event) {
    $(this).parent().parent().parent().remove();
  });
  function getSizeAndPagesName(type) {
    let checkExists = false;
    let result = '';
    if (window.location.search != '') {
      let locationParam = window.location.search.split('?')[1].split('&');
      for (let key in locationParam) {
        let name = locationParam[key].split('=')[0];
        if (name === 'tab') {
          if (locationParam[key].split('=')[1] === 'todo') {
            checkExists = true;
            result = type + 'todo';
          }
          else if (locationParam[key].split('=')[1] === 'wait') {
            checkExists = true;
            result = type + 'wait';
          }
          else if (locationParam[key].split('=')[1] === 'all') {
            checkExists = true;
            result = type + 'all';
          }
        }
      }
    }
    if (!checkExists) {
      result = type + 'todo';
    }
    return result;
  }
  function submitFilterSearch() {
    let params = $('#filter_form').serializeArray();
    let paramsAfterFilter = [];
    jQuery.each(params, function (i, field) {
      if (field.value) {
        field.name += "_" + i;
        paramsAfterFilter.push(field);
      }
    });
    if (window.location.search != '') {
      let locationParam = window.location.search.split('?')[1].split('&');
      let listParamName = ['tab', 'sizetodo', 'sizeall', 'sizewait'];
      for (let key in locationParam) {
        let paramName = locationParam[key].split('=')[0];
        if (listParamName.indexOf(paramName) >= 0) {
          let param = {};
          param.name = paramName;
          param.value = locationParam[key].split('=')[1];
          paramsAfterFilter.push(param);
        }
      }
    }
    window.location.href = creatURL(paramsAfterFilter);
  }

  function creatURL(data) {
    let urlEncodedDataPairs = [];
    for (let key in data) {
      data[key].name = decodeURIComponent(data[key].name.replace(/\+/g, ' '));
      data[key].value = decodeURIComponent(data[key].value.toString().replace(/\+/g, ' '));
      urlEncodedDataPairs.push(encodeURIComponent(data[key].name) + '=' + encodeURIComponent(data[key].value));
    }
    return window.location.origin + window.location.pathname + '?' + urlEncodedDataPairs.join('&').replace(/%20/g, '+');
  }

  function setDatePickerFormSearch() {
    $("#createdfrom").datepicker({
      format: "yyyy-mm-dd",
      autoclose: true,
    });
    $("#createdto").datepicker({
      format: "yyyy-mm-dd",
      autoclose: true,
    });
    if ($("#createdfrom").val() === '') {
      let now = new Date();
      now.setFullYear(now.getFullYear() - 1);
      $("#createdfrom").datepicker("setDate", now);
    }
  }

  function createParamArray(value, name) {
    let checkExists = false;
    let result = [];
    if (window.location.search != '') {
      let locationParam = window.location.search.split('?')[1].split('&');
      for (let key in locationParam) {
        let param = {};
        param.name = locationParam[key].split('=')[0];
        if (param.name == name) {
          param.value = value;
          checkExists = true;
        }
        else {
          param.value = locationParam[key].split('=')[1];
        }
        result.push(param);
      }
    }
    if (!checkExists) {
      let param = {
        'name': name,
        'value': value
      };
      result.push(param);
    }
    return result;
  }

  function autoFilterSearch() {
    if (window.location.search != '') {
      let locationParam = window.location.search.split('?')[1].split('&');
      for (let key in locationParam) {
        let param = {};
        let listParamName = ['createdfrom', 'createdto', 'workflow', 'user', 'item', 'status'];
        param = locationParam[key].split('=');
        if (param[0].split('_')[1] >= 0) {
          let paramName = param[0].split('_')[0];
          if (listParamName.indexOf(paramName) >= 0) {
            let paramValue = decodeURIComponent(param[1].replace(/\+/g, ' '));
            if (paramName == 'createdfrom' || paramName == 'createdto') {
              if (paramValue.length === 10) {
                date = new Date(paramValue);
                if (date != 'Invalid Date') {
                  date.setFullYear(date.getFullYear())
                  $("#" + paramName).datepicker('setDate', date);
                }
              }
            } else {
              if (paramName == 'status') {
                if ($('#status_id').length != 1) {
                  addFilterRow($('#status').text(), paramName, '');
                }
                $("#" + paramValue).prop('checked', true);
              } else {
                addFilterRow($("#" + paramName).text(), paramName, paramValue);
              }
            }
          }
        }
      }
    }
  }

  function addFilterRow(filter, name, valueParam) {
    let newRow;
    let cols = "";
    cols += '<label class="col-sm-2"  for="' + name + '">' + filter + '</label>';
    if (name == 'status') {
      if ($('#status_id').length == 1) return;
      newRow = $('<div id="status_id" class="form-group">');
      cols += '<div class="col-sm-7">'
        + '<label class="checkbox-inline"><input type="checkbox" name="status" value="doing" id="doing">' + $('#action_doing').val() + '</label>'
        + '<label class="checkbox-inline"><input type="checkbox" name="status" value="done" id="done">' + $('#action_done').val() + '</label>'
        + '<label class="checkbox-inline"><input type="checkbox" name="status" value="actioncancel" id="actioncancel">' + $('#action_cancel').val() + '</label>'
        + '</div>';
    } else {
      newRow = $('<div class="form-group">');
      cols += '<div class="col-sm-7"><input type="text" name="' + name + '" class="form-control" value= "' + valueParam + '"></div>';
    }
    cols += '<div class="col-sm-2"><div class="col-sm-8"><button type="button" class="btn btn-danger btn-sm remove_row"><span class="glyphicon glyphicon-remove"></span></button></div></div>';
    newRow.append(cols);
    $("#" + name + '_group').append(newRow);
  }

});
