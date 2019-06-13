$(document).ready(function () {
  var fileDownloadURL = '/admin/report/stats_file_tsv';
  $('#downloadReport').on('click', function () {
    var year = $("#report_year_select").val();
    var month = $("#report_month_select").val();
    var type = $("#report_type_select").val();
    if(year == 'Year') {
      alert('Year is required!');
      return;
    } else if (month == 'Month') {
      alert('Month is required!');
      return;
    }
    let uriByType = {
        file_download:'/api/stats/report/file/file_download',
        file_preview:'/api/stats/report/file/file_preview',
        index_access:'/api/stats/report/record/record_view_per_index',
        detail_view:'/api/stats/report/record/record_view',
        file_using_per_user:'/api/stats/report/file/file_using_per_user',
        top_page_access:'/api/stats/top_page_access',
        search_count:'/api/stats/report/search_keywords',
        user_roles: '/admin/report/user_report_data',
        site_access: '/api/stats/site_access'
    };

    var statsURL = (type == 'user_roles' ? uriByType[type] : uriByType[type] + '/' + year + '/' + month);
    var statsReports = {};
    var ajaxReturn = [0,0,0,0];

    if (type == 'all') { // Get both reports
      let options = ['file_download',
        'file_preview',
        'detail_view',
        'index_access',
        'file_using_per_user',
        'top_page_access',
        'search_count',
        'user_roles',
        'site_access'];
      for (let item in options) {
        var url = (options[item] == 'user_roles' ? uriByType[options[item]] : uriByType[options[item]] + '/' + year + '/' + month);
        statsReports[options[item]] = ajaxGetTSV(url);
      }
      setStatsReportSubmit(statsReports);
    } else { // Get single report
      $.ajax({
        url: statsURL,
        type: 'GET',
        async: false,
        contentType: 'application/json',
        success: function (results) {
          statsReports[type] = results;
          setStatsReportSubmit(statsReports);
        },
        error: function (error) {
          console.log(error);
          $('#error_modal').modal('show');
        }
      });
    }
  });

  // Confirm Schedule Change
  $('#confirm_schedule_button').on('click', function () {
    $('#email_sched_form').submit();
  });

  $('#addEmail').on('click', function () {
        $(moreEmail());
   });

  $('#saveEmail').on('click', function () {
      $('#email_form').submit();
  });
});

function ajaxGetTSV(endpoint) {
  let result;
  $.ajax({
    url: endpoint,
    type: 'GET',
    async: false,
    contentType: 'application/json',
    success: function (results) {
      result = results;
    },
    error: function (error) {
      console.log(error);
      $('#error_modal').modal('show');
    }
  });
  return result
}

function setStatsReportSubmit(statsReports) {
  $('#report_file_input').val(JSON.stringify(statsReports));
  $('#report_file_form').submit();
  $('#report_file_input').val('');
}

function addAlert(message) {
    $('#alerts').append(
        '<div class="alert alert-light" id="alert-style">' +
        '<button type="button" class="close" data-dismiss="alert">' +
        '&times;</button>' + message + '</div>');
}

function moreEmail(){
  $('#newEmail').append(
       '<div id="emailID">'
       +'<div class="col-md-5 col-md-offset-3" id="emailAdd">'
       +'<input type="email" class="form-control inputEmail" pattern="[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$"'
       +' name="inputEmail" id="inputEmail"'
       +'placeholder="Enter email address." value="" required/></br>'
       +'</div>'
       +'<div class="col-md-1">'
       +'<a class="btn-default remove-button" onclick="$(\'#emailID\').remove();"  id="remove_button">'
       +'<span class="glyphicon glyphicon-remove"></span>'
       +'</a>'
       +'</div>'
       +'</div>'
  );
}

function IsEmpty(){
  if(document.form['email_form'].inputEmail.value === "")
  {
    alert("empty");
    return false;
  }
    return true;
}
