$(document).ready(function () {
  var fileDownloadURL = '/admin/report/stats_file_output';
  $('#downloadReport').on('click', function () {
    var year = $("#report_year_select").val();
    var month = $("#report_month_select").val();
    if(year == 'Year') {
      alert('Year is required!');
      return;
    } else if (month == 'Month') {
      alert('Month is required!');
      return;
    }
    $('#report_file_form').submit();
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
      let invalidInputs = Array.from(document.getElementById('email_form').elements).filter(function(element){
        return element.type == 'email' && element.value && !element.checkValidity();
      });
      let invalidEmails = [];
      for (let element of invalidInputs) {
        invalidEmails.push(element.value);
      }
      localStorage.setItem('invalidEmails', JSON.stringify(invalidEmails));
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

function moreEmail(){

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
  deleteButtonLink.addEventListener('click', function() {
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

function IsEmpty(){
  if(document.form['email_form'].inputEmail.value === "")
  {
    alert("empty");
    return false;
  }
    return true;
}
