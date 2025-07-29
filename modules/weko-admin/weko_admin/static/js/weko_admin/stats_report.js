$(document).ready(function () {
  var fileDownloadURL = '/admin/report/stats_file_output';
  $('#repository_select').change(function () {
    var selectedRepo = $(this).val();
    var currentUrl = new URL(window.location.href);

    if (selectedRepo) {
      currentUrl.searchParams.set('repo_id', selectedRepo);
    } else {
      currentUrl.searchParams.delete('repo_id');
    }

    window.location.href = currentUrl.toString();
  });

  $('#downloadReport').on('click', function () {
    var year = $("#report_year_select").val();
    var month = $("#report_month_select").val();
    var type = $("#report_type_select").val();
    if (year == 'Year') {
      alert('Year is required!');
      return;
    } else if (month == 'Month') {
      alert('Month is required!');
      return;
    }
    let uriByType = {
      file_download: '/api/stats/report/file/file_download',
      file_preview: '/api/stats/report/file/file_preview',
      billing_file_download: '/api/stats/report/file/billing_file_download',
      billing_file_preview: '/api/stats/report/file/billing_file_preview',
      index_access: '/api/stats/report/record/record_view_per_index',
      detail_view: '/api/stats/report/record/record_view',
      file_using_per_user: '/api/stats/report/file/file_using_per_user',
      top_page_access: '/api/stats/top_page_access',
      search_count: '/api/stats/report/search_keywords',
      user_roles: '/admin/report/user_report_data',
      site_access: '/api/stats/site_access'
    };

    var statsURL = (type == 'user_roles' ? uriByType[type] : uriByType[type] + '/' + year + '/' + month);
    var statsReports = {};
    var ajaxReturn = [0, 0, 0, 0];

    if (type == 'all') { // Get both reports
      let options = ['file_download',
        'file_preview',
        'billing_file_download',
        'billing_file_preview',
        'detail_view',
        'index_access',
        'file_using_per_user',
        'top_page_access',
        'search_count',
        'user_roles',
        'site_access'];
      for (let item in options) {
        var url = (options[item] == 'user_roles' ? uriByType[options[item]] : uriByType[options[item]] + '/' + year + '/' + month);
        statsReports[options[item]] = ajaxGetFile(url);
      }
      setStatsReportSubmit(statsReports);
    } else { // Get single report
      $.ajax({
        url: statsURL,
        type: 'GET',
        async: false,
        contentType: 'application/json',
        data: {
          repository_id: $('#repository_select').val()
        },
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
    if (document.getElementById('email_form').checkValidity()) {
      moreEmail();
    }
    else {
      addAlert('Please check email input fields.');
    }
  });

  $('#saveEmail').on('click', function () {
    // save any invalid addresses
    let invalidInputs = Array.from(document.getElementById('email_form').elements).filter(function (element) {
      return element.type == 'email' && element.value && !element.checkValidity();
    });
    let invalidEmails = [];
    for (let element of invalidInputs) {
      invalidEmails.push(element.value);
    }
    localStorage.setItem('invalidEmails', JSON.stringify(invalidEmails));

    // add repository select
    let repositorySelect = $('#repository_select').val();
    $('<input>').attr({
      type: 'hidden',
      name: 'repository_select',
      value: repositorySelect
    }).appendTo('#email_form');

    $('#email_form').submit();
  });

  // check before parsing to prevent error in case of empty string
  if (localStorage.getItem('invalidEmails')) {
    // load invalid address if saved
    let invalidEmails = JSON.parse(localStorage.getItem('invalidEmails'));
    for (let email of invalidEmails) {
      document.getElementById('inputEmail_0').value = email;
      moreEmail();
    }
    // one time only
    localStorage.setItem('invalidEmails', '');
  }
});

function ajaxGetFile(endpoint) {
  let result;
  $.ajax({
    url: endpoint,
    type: 'GET',
    async: false,
    contentType: 'application/json',
    data: {
      repository_id: $('#repository_select').val()
    },
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
  let flashMessage = document.createElement('div');
  for (let className of ['alert', 'alert-error', 'alert-dismissable']) {
    flashMessage.classList.add(className);
  }

  flashMessage.textContent = message;

  let dismissButton = document.createElement('button');
  dismissButton.type = 'button';
  dismissButton.classList.add('close');
  dismissButton.dataset.dismiss = 'alert';
  dismissButton.textContent = 'x';

  flashMessage.appendChild(dismissButton);

  let contentHeader = document.getElementsByClassName('content-header')[0]
  contentHeader.insertBefore(flashMessage, contentHeader.firstChild)
}

function moreEmail() {

  let removableEmailField = document.createElement('div');

  let emailInputDiv = document.createElement('div');
  emailInputDiv.classList.add('col-md-5');
  emailInputDiv.classList.add('col-md-offset-3');

  let emailInput = document.createElement('input');
  emailInput.type = 'email';
  emailInput.classList.add('form-control');
  emailInput.classList.add('inputEmail');
  emailInput.pattern = '[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$';
  emailInput.name = 'inputEmail';
  emailInput.id = 'inputEmail';
  emailInput.placeholder = 'Enter email address.';
  emailInput.required = true;

  let mainEmailInput = document.getElementById('inputEmail_0');
  emailInput.value = mainEmailInput.value;
  mainEmailInput.value = '';

  let lineBreak = document.createElement('br');

  emailInputDiv.appendChild(emailInput);
  emailInputDiv.appendChild(lineBreak);
  removableEmailField.appendChild(emailInputDiv);

  let deleteButtonDiv = document.createElement('div');
  deleteButtonDiv.classList.add('col-md-1');

  let deleteButtonLink = document.createElement('a');
  deleteButtonLink.classList.add('btn-default');
  deleteButtonLink.classList.add('remove-button');
  deleteButtonLink.addEventListener('click', function () {
    removableEmailField.parentElement.removeChild(removableEmailField);
  });

  let deleteButtonSpan = document.createElement('span');
  deleteButtonSpan.classList.add('glyphicon');
  deleteButtonSpan.classList.add('glyphicon-remove');

  deleteButtonLink.appendChild(deleteButtonSpan);
  deleteButtonDiv.appendChild(deleteButtonLink);
  removableEmailField.appendChild(deleteButtonDiv);


  document.getElementById('newEmail').appendChild(removableEmailField);

}

function IsEmpty() {
  if (document.form['email_form'].inputEmail.value === "") {
    alert("empty");
    return false;
  }
  return true;
}
