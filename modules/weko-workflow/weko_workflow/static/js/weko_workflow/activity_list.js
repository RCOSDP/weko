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
  $('#filter_form_download').on('click', function () {
    downloadActivities();
  });

  $('#filter_form_clear').on('click', function () {
    $('#activitylogs_clear_modal').fadeIn();
  });

  $('#confirm_clear_activitylogs').on('click', function () {
    $('#activitylogs_clear_modal').fadeOut();
    clearActivities();
  });

  $('#cancel_clear_activitylogs').on('click', function () {
    $('#activitylogs_clear_modal').fadeOut();
  });

  $('.clear-activitylog').on('click', function () {
    $('#activitylog_clear_modal').fadeIn();
    var activity_id=$(this).closest('tr').find('a').text();
    $('#del_activity_id').text(activity_id);

  });

  $('#confirm_clear_activitylog').on('click', function () {
    var activity_id=document.getElementById("del_activity_id").textContent;
    $('#activitylog_clear_modal').fadeOut();

    clearActivity(activity_id);
  });
  $('#cancel_clear_activitylog').on('click', function () {
    $('#activitylog_clear_modal').fadeOut();
  });

  $(".activity-link").on("click", function(event){
    $.ajax({
      url:"/workflow/verify_deletion/"+$(this).text(),
      method:"GET",
      async:false,
      success: function(data, status) {
        if(data.is_deleted === true && data.for_delete === false){
          alert($('#item_deleted_msg').text());
          event.preventDefault();
        }
      }
    });
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
        field.value = field.value.trim();
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
    let now
    if ($("#createdfrom").val() === '') {
      $.ajax({
        url: '/api/admin/get_server_date',
        method: 'GET',
        async: false,
        success: function (data, status) {
          now = new Date(data.year-1,data.month-1,data.day)
        },
        error: function (data, status) {
          now = new Date();
          now.setFullYear(now.getFullYear() - 1);
        }
      });
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
        let listParamName = ['createdfrom', 'createdto', 'workflow', 'user', 'item', 'status', 'action'];
        param = locationParam[key].split('=');
        if (param[0].split('_')[1] >= 0) {
          let paramName = param[0].split('_')[0];
          if (listParamName.indexOf(paramName) >= 0) {
            let paramValue = decodeURIComponent(param[1].replace(/\+/g, ' '));
            if (paramName == 'createdfrom' || paramName == 'createdto') {
              if (paramValue.length === 10) {
                let date = new Date(paramValue);
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
              } else if (paramName == 'action') {
                if ($('#action_id').length != 1) {
                  addFilterRow($('#action').text(), paramName, '');
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
    } else if (name == 'action') {
      if ($('#action_id').length == 1) return;
      newRow = $('<div id="action_id" class="form-group">');
      cols += '<div class="col-sm-7">'
        + '<label class="checkbox-inline"><input type="checkbox" name="action" value="start" id="start">' + $('#action_start').val() + '</label>'
        + '<label class="checkbox-inline"><input type="checkbox" name="action" value="itemregistration" id="itemregistration">' + $('#action_item_registration').val() + '</label>'
        + '<label class="checkbox-inline"><input type="checkbox" name="action" value="itemlink" id="itemlink">' + $('#action_item_link').val() + '</label>'
        + '<label class="checkbox-inline"><input type="checkbox" name="action" value="identifiergrant" id="identifiergrant">' + $('#action_identifier_grant').val() + '</label>'
        + '<label class="checkbox-inline"><input type="checkbox" name="action" value="approval" id="approval">' + $('#action_approval').val() + '</label>'
        + '<label class="checkbox-inline"><input type="checkbox" name="action" value="end" id="end">' + $('#action_end').val() + '</label>'
        // + '<label class="checkbox-inline"><input type="checkbox" name="action" value="oapolicyconfirmation" id="oapolicyconfirmation">' + $('#action_oa_policy_confirmation').val() + '</label>'
        + '</div>';
    } else {
      newRow = $('<div class="form-group">');
      cols += '<div class="col-sm-7"><input type="text" name="' + name + '" class="form-control" value= "' + valueParam + '"></div>';
    }
    cols += '<div class="col-sm-2"><div class="col-sm-8"><button type="button" class="btn btn-danger btn-sm remove_row"><span class="glyphicon glyphicon-remove"></span></button></div></div>';
    newRow.append(cols);
    $("#" + name + '_group').append(newRow);
  }

  $('#btn_send_mail').click(function () {
    if (wf_DataAll.length == 0)
      getUsageReportData();
    else
      startPaging();
  });
  $('#btn_close').click(function () {
    $('#popup_send').removeClass('in').css('display', 'none');
  });
  $('#btn_approve').click(function () {
    $('#apply_spinner').append('<div class="spinner"></div>');
    mail_template = $("#setTemplate").val();
    has_error = false;
    lstSelectCheckboxes.forEach(function (activity_id) {
      $.ajax({
        url: '/workflow/send_mail/' + activity_id + '/' + mail_template,
        method: 'POST',
        success: function (data) {
          if (data.msg == "Error") {
            has_error = true
          }
        }
      });
    });
    setTimeout(function () {
      $('.spinner').remove();
      if (has_error) {
        $('#popup_fail').addClass('in').css('display', 'block');
      } else {
        $('#popup_success').addClass('in').css('display', 'block');
      }
    }, 2000);
    // 15745
  });


  //Click button OK
  $('.btn_ok').click(function () {
    $("#btn_Next").attr('disabled', true);
    $('#popup_success, #popup_approve, #popup_fail').removeClass('in').css('display', 'none');
    $(".checkbox-class, #checkAll").prop('checked', false);
    listCheckbox();
    lstSelectCheckboxes.clear();

  });

  // Whenever SelectBox is changed, re-update list activities
  $('#setTemplate').on('change', function () {
    // Clear all current data
    lstSelectCheckboxes.clear();
    $("#checkAll").prop("checked", false);
    $("#btn_Next").attr('disabled', true);
    var selectedTemplate = $(this).children("option:selected").val();
    // Re-paging by selected mail template
    pagination(pagingOptions, wf_DataFilter[selectedTemplate]);
  })
  //Click button Confirm
  $('#btn_Next').click(function () {
    $('#appendHTML, #label_template').empty();
    listCheckbox();

    $('#popup_approve').addClass('in').css('display', 'block');
    let rows = wf_DataAll.filter(function (activity) {
      return lstSelectCheckboxes.has(activity.activity_id);
    });
    // let rows;
    let i = 1;

    //render html table
    $.each(rows, function (key, val) {
      if (Object.keys(val).length > 0) {
        const { activity_id, item, email } = val;
        const td = `<tr><td>${i}</td>
                    <td>${this.activity_id}</td>
                    <td>${this.item}</td>
                    <td>${this.email}</td></tr>`;
        $('#appendHTML').append(td);
        i++;
      }
    });

    labelTemplate = $("#setTemplate :selected").text();
    $('#label_template').append(labelTemplate);
  });

  //Click button close and Back
  $('#btn_close_pop2, #btn_back').click(function () {
    $('#popup_approve').removeClass('in').css('display', 'none');
  });

  //Click button check all
  $("#checkAll").click(function () {
    if ($(this).is(":checked")) {
      $(".checkbox-class:not(:checked)").prop("checked", true);
      wf_DataFilter[$('#setTemplate').val()].forEach(function (activity) {
        lstSelectCheckboxes.add(activity.activity_id);
      });
      if (lstSelectCheckboxes.size > 0)
        $("#btn_Next").removeAttr("disabled");
    } else {
      $(".checkbox-class").prop("checked", false);
      lstSelectCheckboxes.clear();
      $("#btn_Next").attr('disabled', true);
    }
  });

  listCheckbox();
});


const mailUserGroup = $("#send_mail_user_group").text() ? $("#send_mail_user_group").text() : [];

var lstMailUserGroup = JSON.parse(mailUserGroup);
var lstSelectCheckboxes = new Set();
var wf_DataFilter = {}
var wf_DataAll = []


var req_per_page = parseInt($("#req_per_page").text());
var status_data = $("#action_list").text();
var item_type_name = $("#item_type_name").text();

// on page load collect data to load pagination as well as table
const pagingOptions = { "req_per_page": req_per_page, "page_no": 1 };

// At a time maximum allowed pages to be shown in pagination div

var pagination_visible_pages = parseInt($("#pagination_visible_pages").text());


// hide pages from pagination from beginning if more than pagination_visible_pages
function hide_from_beginning(element) {
  if (element.style.display === "" || element.style.display === "block") {
    element.style.display = "none";
  } else {
    hide_from_beginning(element.nextSibling);
  }
}

// hide pages from pagination ending if more than pagination_visible_pages
function hide_from_end(element) {
  if (element.style.display === "" || element.style.display === "block") {
    element.style.display = "none";
  } else {
    hide_from_end(element.previousSibling);
  }
}

// load data and style for active page
function active_page(element, rows, req_per_page) {
  var current_page = document.getElementsByClassName('active-page');
  var next_link = document.getElementById('next_link');
  var prev_link = document.getElementById('prev_link');
  var next_tab = current_page[0].nextSibling;
  var prev_tab = current_page[0].previousSibling;

  current_page[0].className = current_page[0].className.replace("active-page", "");
  if (element === "next") {
    if (parseInt(next_tab.text).toString() === 'NaN') {
      next_tab.previousSibling.className += " active-page";
      next_tab.setAttribute("onclick", "return false");
    } else {
      next_tab.className += " active-page"
      render_table_rows(rows, parseInt(req_per_page), parseInt(next_tab.text));
      if (prev_link.getAttribute("onclick") === "return false") {
        prev_link.setAttribute("onclick", `active_page('prev',\"${rows}\",${req_per_page})`);
      }
      if (next_tab.style.display === "none") {
        next_tab.style.display = "block";
        hide_from_beginning(prev_link.nextSibling)
      }
    }
  } else if (element === "prev") {
    if (parseInt(prev_tab.text).toString() === 'NaN') {
      prev_tab.nextSibling.className += " active-page";
      prev_tab.setAttribute("onclick", "return false");
    } else {
      prev_tab.className += " active-page";
      render_table_rows(rows, parseInt(req_per_page), parseInt(prev_tab.text));
      if (next_link.getAttribute("onclick") === "return false") {
        next_link.setAttribute("onclick", `active_page('next',\"${rows}\",${req_per_page})`);
      }
      if (prev_tab.style.display === "none") {
        prev_tab.style.display = "block";
        hide_from_end(next_link.previousSibling)
      }
    }
  } else {
    element.className += "active-page";
    render_table_rows(rows, parseInt(req_per_page), parseInt(element.text));
    if (prev_link.getAttribute("onclick") === "return false") {
      prev_link.setAttribute("onclick", `active_page('prev',\"${rows}\",${req_per_page})`);
    }
    if (next_link.getAttribute("onclick") === "return false") {
      next_link.setAttribute("onclick", `active_page('next',\"${rows}\",${req_per_page})`);
    }
  }
}

// Render the table's row in table request-table
function render_table_rows(rows, req_per_page, page_no) {
  const response = JSON.parse(decodeURIComponent(escape(window.atob(rows))));
  const resp = response.slice(req_per_page * (page_no - 1), req_per_page * page_no)
  $('.check_table').empty()
  let count = req_per_page * (page_no - 1) + 1;
  resp.forEach(function (element) {
    if (Object.keys(element).length > 0) {
      const { activity_id, item, work_flow, email } = element;
      let value_checkbox = activity_id;
      if (lstSelectCheckboxes.has(value_checkbox.toString())) {
        const td = `<tr id = "${activity_id}"><td scope="row" class="col_empty"><input class="checkbox-class" type="checkbox" checked value="${value_checkbox}"/></td>
                <td class="col_empty">${count++}</td>
                <td class="activity_id">${activity_id}</a></td>
                <td>${item}</td>

                <td class="col_empty">${work_flow}</td>
                      <td class="col_empty">${status_data}</td>
                <td>${email}</td></tr>`;
        $('.check_table').append(td);
      } else {
        const td = `<tr id = "${activity_id}"><td scope="row" class="col_empty"><input class="checkbox-class" type="checkbox" value="${value_checkbox}"/></td>
                <td class="col_empty">${count++}</td>
                <td class="activity_id">${activity_id}</a></td>
                <td>${item}</td>
                <td class="col_empty">${work_flow}</td>
                      <td class="col_empty">${status_data}</td>
                <td>${email}</td></tr>`;
        $('.check_table').append(td)
      }
    }
  });
  listCheckbox();
}

// Pagination logic implementation
function pagination(data, wf_Data) {
  if (!wf_Data) return;
  const all_data = window.btoa(unescape(encodeURIComponent(JSON.stringify(wf_Data))));
  let $pagination = $(".pagination.table_data");
  $pagination.empty();
  if (data.req_per_page !== 'ALL') {
    let pager = `<a href="#" id="prev_link" onclick=active_page('prev',\"${all_data}\",${data.req_per_page})>&lt;</a>` +
      `<a href="#" class="active-page" onclick=active_page(this,\"${all_data}\",${data.req_per_page})>1</a>`;
    const total_page = Math.ceil(parseInt(wf_Data.length) / parseInt(data.req_per_page));
    if (total_page < pagination_visible_pages) {
      render_table_rows(all_data, data.req_per_page, data.page_no);
      for (let num = 2; num <= total_page; num++) {
        pager += `<a href="#" onclick=active_page(this,\"${all_data}\",${data.req_per_page})>${num}</a>`;
      }
    } else {
      render_table_rows(all_data, data.req_per_page, data.page_no);
      for (let num = 2; num <= pagination_visible_pages; num++) {
        pager += `<a href="#" onclick=active_page(this,\"${all_data}\",${data.req_per_page})>${num}</a>`;
      }
      for (let num = pagination_visible_pages + 1; num <= total_page; num++) {
        pager += `<a href="#" style="display:none;" onclick=active_page(this,\"${all_data}\",${data.req_per_page})>${num}</a>`;
      }
    }
    pager += `<a href="#" id="next_link" onclick=active_page('next',\"${all_data}\",${data.req_per_page})>&gt;</a>`;
    $pagination.append(pager);
  } else {
    render_table_rows(all_data, wf_Data.length, 1);
  }
}

function startPaging() {
  for (mailGroup in lstMailUserGroup) {
    wf_DataFilter[mailGroup] = wf_DataAll.filter(function (activity) {
      return lstMailUserGroup[mailGroup].indexOf(activity.user_role) > -1;
    });
  }
  pagination(pagingOptions, wf_DataFilter[$('#setTemplate').val()]);
  $('#popup_send').addClass('in').css('display', 'block');
}
//Array to hold the checked ids

//Event listener to detect changes
function listCheckbox() {
  $('#appendHTML').empty();
  $('.checkbox-class').change(function () {
    let id = $(this).parents('tr').attr('id');
    if ($(this).is(":checked")) {
      lstSelectCheckboxes.add(id);
      $("#btn_Next").removeAttr('disabled');
    } else {
      lstSelectCheckboxes.delete(id);
      $("#checkAll").prop("checked", false);
      if (lstSelectCheckboxes.size === 0) {
        $("#btn_Next").attr('disabled', true);
      }
    }
  });
}

function loadingController(isStop) {
  if (isStop) {
    $(".lds-ring-background").addClass("hidden");
  }
  else {
    $(".lds-ring-background").removeClass("hidden");
  }
}

function getUsageReportData() {
  loadingController(false);
  var urlPath = '/workflow/usage-report';
  var sURL = window.location.search.substring(1);
  if (!analyzeParams(sURL)) {
    loadingController(true);
    $('#popup_send').addClass('in').css('display', 'block');
    return;
  }
  $.ajax({
    url: urlPath + '?' + sURL,
    method: 'GET',
    success: function (res) {
      wf_DataAll = res.activities;
      startPaging();
      loadingController(true);
    },
    error: function (error) {
      console.error(error);
      loadingController(true);
    }
  });
}
function analyzeParams(sURL) {
  var lstParams = sURL.split('&');
  // In case workflow and status has value but not match target workflow and status, do not exec request
  var checkingConditions = { 'workflow': item_type_name, 'status': 'doing' }
  wfLst = [];
  statusLst = [];
  for (var i = 0; i < lstParams.length; i++) {
    var sParamArr = lstParams[i].split('=');
    if (sParamArr[0].startsWith('workflow')) {
      wfLst.push(decodeURIComponent(sParamArr[1]))
    } else if (sParamArr[0].startsWith('status')) {
      statusLst.push(sParamArr[1])
    }
  }
  return (wfLst.length > 0 ? wfLst.indexOf(checkingConditions.workflow) > -1 : true) &&
    (statusLst.length > 0 ? statusLst.indexOf(checkingConditions.status.toLowerCase()) > -1 : true);
}


//download filtered activities
async function downloadActivities(activity_id=''){
  let paramsAfterFilter = [];
  if (activity_id != '') {
	    let tmp = {};
      tmp.name = "activity_id";
      tmp.value = activity_id;
      paramsAfterFilter.push(tmp);
  } else {

    let params = $('#filter_form').serializeArray();
    jQuery.each(params, function (i, field) {
      if (field.value) {
        field.name += "_" + i;
        field.value = field.value.trim();
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

    for (let key in paramsAfterFilter) {
      paramsAfterFilter[key].name = decodeURIComponent(paramsAfterFilter[key].name.replace(/\+/g, ' '));
      paramsAfterFilter[key].value = decodeURIComponent(paramsAfterFilter[key].value.toString().replace(/\+/g, ' '));
    }
  }
  return  setActivitylogSubmit(paramsAfterFilter);

}

//clear all filtered activities
function clearActivities(){

  downloadActivities().then(()=>{

    let params = $('#filter_form').serializeArray();
    let paramsAfterFilter = [];
    jQuery.each(params, function (i, field) {
      if (field.value) {
        field.name += "_" + i;
        field.value = field.value.trim();
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

    let urlEncodedDataPairs = [];
    for (let key in paramsAfterFilter) {
      paramsAfterFilter[key].name = decodeURIComponent(paramsAfterFilter[key].name.replace(/\+/g, ' '));
      paramsAfterFilter[key].value = decodeURIComponent(paramsAfterFilter[key].value.toString().replace(/\+/g, ' '));
      urlEncodedDataPairs.push(encodeURIComponent(paramsAfterFilter[key].name) + '=' + encodeURIComponent(paramsAfterFilter[key].value));
    }
    clearURL = window.location.pathname + 'clear_activitylog/?' + urlEncodedDataPairs.join('&').replace(/%20/g, '+');

    $.ajax({
      url: clearURL,
      method: 'GET',
      success: function (res) {
        activitylog_tsv = res;
        location.reload();
      },
      error: function (error) {
        console.error(error);
      }
    });
  });


}

//clear seletected activity
function clearActivity(activity_id){

  downloadActivities(activity_id).then(()=>{

    clearURL = window.location.pathname + 'clear_activitylog/?activity_id=' + activity_id;

    $.ajax({
      url: clearURL,
      method: 'GET',
      success: function (res) {
        activitylog_tsv = res;
        location.reload();
      },
      error: function (error) {
        console.error(error);
      }
    });
  });


}

async function setActivitylogSubmit(paramsAfterFilter) {
  let form = document.getElementById("activitylog_file_form");
  let children = [];
  for(let key in paramsAfterFilter){
    const input = document.createElement('input');

    //input要素にtype属性とvalue属性を設定
    input.setAttribute('type', 'hidden');
    input.setAttribute('name', paramsAfterFilter[key].name)
    input.setAttribute('value', paramsAfterFilter[key].value);

    form.appendChild(input);
    children[key] = input;
  }
  $('#activitylog_file_form').submit();
  await setTimeout( 1000 );
  if(form.hasChildNodes()){
    for (let key in children) {
      form.removeChild(children[key]);
    }
  }

}
