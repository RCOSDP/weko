$(document).ready(function () {
  $('#step_page').focus();
  $('#activity_locked').hide();

  var unlock_activity = function (activity_id, locked_value) {
    var url = '/workflow/activity/unlock/' + activity_id;
    var data = JSON.stringify({
      locked_value: locked_value
    });

    var is_ie = /*@cc_on!@*/false || !!document.documentMode;
    if (is_ie) {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", url, false);
      xhr.send(data);
    } else {
      navigator.sendBeacon(url, data);
    }

    sessionStorage.removeItem('locked_value');
  };

  var locked_value = sessionStorage.getItem('locked_value');
  var activity_id = $('input#activity_id_for_lock').val();
  var cur_step = $('input#cur_step_for_lock').val();
  var permission = $('#hide-res-check').text(); // 0: allow, <> 0: deny

  if ('end_action' !== cur_step && permission == 0) {
    $.ajax({
      type: "POST",
      cache: false,
      data: {
        locked_value: locked_value
      },
      url: '/workflow/activity/lock/' + activity_id,
      success: function (result) {
        locked_value = result.locked_value;
        sessionStorage.setItem('locked_value', locked_value);
      },
      error: function () {
        $('#step_page').hide();
        $('#activity_locked').show();
      }
    });
  } else if (locked_value) {
    unlock_activity(activity_id, locked_value);
  }

  // start: approval page
  $('#btn-return, #btn-reject, #btn-approval, .save-button, .done-button, .next-button').click(function () {
    locked_value = 0;
  });

  window.addEventListener('beforeunload', function () {
    if (locked_value) {
      unlock_activity(activity_id, locked_value);
    }
  });
});
