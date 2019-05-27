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
        file_download:'file_download',
        file_preview:'file_preview',
        detail_view:'report/record/record_view',
        file_using_per_user:'report/file/file_using_per_user'};
    var statsURL = '/api/stats/' + uriByType[type] + '/' + year + '/' + month;
    var statsReports = {};
    var ajaxReturn = [0,0,0,0];

    if (type == 'all') { // Get both reports
      let options = ['file_download',
        'file_preview',
        'detail_view',
        'file_using_per_user'];
      $.ajax({
        url: '/api/stats/' + options[0] + '/' + year + '/' + month,
        type: 'GET',
        async: false,
        contentType: 'application/json',
        success: function (results) {
          statsReports[options[0]] = results;
        },
        error: function (error) {
          console.log(error);
          $('#error_modal').modal('show');
        }
      });
      $.ajax({
        url: '/api/stats/' + options[1] + '/' + year + '/' + month,
        type: 'GET',
        async: false,
        contentType: 'application/json',
        success: function (results) {
          statsReports[options[1]] = results;
        },
        error: function (error) {
          console.log(error);
          $('#error_modal').modal('show');
        }
      });
      $.ajax({
        url: '/api/stats/' + uriByType[options[2]] + '/' + year + '/' + month,
        type: 'GET',
        async: false,
        contentType: 'application/json',
        success: function (results) {
          statsReports[options[2]] = results;
        },
        error: function (error) {
          console.log(error);
          $('#error_modal').modal('show');
        }
      });
      $.ajax({
        url: '/api/stats/' + uriByType[options[3]] + '/' + year + '/' + month,
        type: 'GET',
        async: false,
        contentType: 'application/json',
        success: function (results) {
          statsReports[options[3]] = results;
        },
        error: function (error) {
          console.log(error);
          $('#error_modal').modal('show');
        }
      });
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
});

function setStatsReportSubmit(statsReports) {
  $('#report_file_input').val(JSON.stringify(statsReports));
  $('#report_file_form').submit();
  $('#report_file_input').val('');
}

