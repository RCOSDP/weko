$(document).ready(function () {
  $('#activity_detail').focus();
  $('#activity_locked').hide();
  var locked_value = sessionStorage.getItem('locked_value');
  var activity_id = $('input#activity_id_for_lock').val();
  var cur_step = $('input#cur_step_for_lock').val();
  if ('end_action' !== cur_step) {
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
      error: function (result) {
        $('#activity_detail').hide();
        $('#activity_locked').show();
      }
    });
  } else {
    sessionStorage.removeItem('locked_value');
  }

  // start: approval page
  $('#btn-return').click(function () {
    locked_value = 0;
  });

  $('#btn-reject').click(function () {
    locked_value = 0;
  });

  $("#btn-approval").click(function () {
    locked_value = 0;
  });

  $(".save-button").click(function () {
    locked_value = 0;
  });
  // end: approval page

  $(".done-button").click(function () {
    locked_value = 0;
  });

  $(".next-button").click(function () {
    locked_value = 0;
  });

  window.addEventListener('beforeunload', function (e) {
    if (locked_value) {
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
    }
  });
});
