$(document).ready(function () {

  // Set the boolean to send email and trigger the create reports event
  $('#confirm_send_email_button').on('click', function () {
    $('#send_email_input').val('True');
    $('#downloadReport').trigger('click');
  });

  // Confirm schedule change
  $('#confirm_schedule_button').on('click', function () {
    let repositorySelect = $('#repository_select').val();
    $('<input>').attr({
      type: 'hidden',
      name: 'repository_select',
      value: repositorySelect
    }).appendTo('#email_sched_form');

    $('#email_sched_form').submit();
  });

  // Change selectable options based on frequency
  $('#email_sched_frequency').on('change', function () {
    var frequency = $(this).val();
    switch (frequency) {
      case 'monthly':
        $('#email_sched_details_weekly').addClass('hidden');
        $('.weekly-option').prop('selected', false);
        $('#email_sched_details_monthly').removeClass('hidden');
        break;
      case 'weekly':
        $('#email_sched_details_monthly').addClass('hidden');
        $('.monthly-option').prop('selected', false);
        $('#email_sched_details_weekly').removeClass('hidden');
        break;
      case 'daily':
        $('#email_sched_details_weekly').addClass('hidden');
        $('#email_sched_details_monthly').addClass('hidden');
        $('#sched_details_label').addClass('hidden');
        $('.monthly-option').prop('selected', false);
        $('.weekly-option').prop('selected', false);
    }
  });
});
