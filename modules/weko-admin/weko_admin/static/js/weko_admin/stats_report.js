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
    var statsURL = '/api/stats/' + type + '/' + year + '/' + month;
    var statsReports = {}

    if(type == 'all') { // Get both reports
      $.ajax({
        url: '/api/stats/file_download/' + year + '/' + month,
        type: 'GET',
        contentType: 'application/json',
        success: function (results) {
          statsReports['file_download'] = results;
          $.ajax({
            url: '/api/stats/file_preview/' + year + '/' + month,
            type: 'GET',
            contentType: 'application/json',
            success: function (results) {
              console.log(results);
              statsReports['file_preview'] = results;
              setStatsReportSubmit(statsReports);
            },
            error: function (error) {
              console.log(error);
              $('#error_modal').modal('show');
            }
          });
        },
        error: function (error) {
          console.log(error);
          $('#error_modal').modal('show');
        }
      });
    } else { // Get single report
      $.ajax({
        url: statsURL,
        type: 'GET',
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

