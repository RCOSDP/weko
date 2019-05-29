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
        file_download:'report/file/file_download',
        file_preview:'report/file/file_preview',
        detail_view:'report/record/record_view',
        file_using_per_user:'report/file/file_using_per_user',
        top_page_access:'top_page_access'};
    var statsURL = '/api/stats/' + uriByType[type] + '/' + year + '/' + month;
    var statsReports = {};
    var ajaxReturn = [0,0,0,0];

    if (type == 'all') { // Get both reports
      let options = ['file_download',
        'file_preview',
        'detail_view',
        'file_using_per_user',
        'top_page_access'];
      for (let item in options) {
        statsReports[options[item]] = ajaxGetTSV(uriByType[options[item]], year, month);
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
});

function ajaxGetTSV(keyword, year, month) {
  let result;
  $.ajax({
    url: '/api/stats/' + keyword + '/' + year + '/' + month,
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

