$(document).ready(function () {
  $('#step_page').focus();
  $('#activity_locked').hide();
  $('#locked_msg').hide()
  $('#user_locked_msg').hide()

  var guestEmail = $('#current_guest_email').val();

  var unlock_activity = function (activity_id, locked_value) {
    if (guestEmail) {
      return;
    }
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
  var user_unlock_activity = function (activity_id) {
    if (guestEmail) {
      return;
    }
    var url = '/workflow/activity/user_unlock/' + activity_id;
    
    var data = JSON.stringify({
      is_opened: is_opened
    })
    var is_ie = /*@cc_on!@*/false || !!document.documentMode;
    if (is_ie) {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", url, false)
      xhr.send(data)
    } else {
      navigator.sendBeacon(url, data)
    }
    sessionStorage.removeItem('is_opened');
  }

  var current_user_email = $('input#current_user_email').val();
  var locked_value = sessionStorage.getItem('locked_value');
  var is_opened = sessionStorage.getItem('is_opened')
  var activity_id = $('input#activity_id_for_lock').val();
  var cur_step = $('input#cur_step_for_lock').val();
  var permission = $('#hide-res-check').text(); // 0: allow, <> 0: deny


  var  csrf_token=$('#csrf_token').val();
  $.ajaxSetup({
    beforeSend: function(xhr, settings) {
       if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain){
           xhr.setRequestHeader("X-CSRFToken", csrf_token);
       }
    }
  });

  if ('end_action' !== cur_step && permission == 0 && !guestEmail) {
    $.ajax({
      type: "POST",
      cache: false,
      url: '/workflow/activity/user_lock/' + activity_id,
      success: function (result) {
        if (result.err) {
          $('#step_page').hide();
          $('#activity_locked').show();
          $('#user_locked_msg').show();
          var msg = $('#user_locked_msg').text();
          if (result.locked_by_username) {
            msg = msg.replace('{}', result.locked_by_username);
          } else {
            msg = msg.replace(' ({})', '');
            msg = msg.replace('（{}）', '');
          }
          $('#user_locked_msg').html(msg);
          is_opened=true;
          sessionStorage.setItem('is_opened', is_opened);
        } else {
          is_opened = false
          sessionStorage.setItem('is_opened', is_opened);
        }
      },
      error: function(jqXHR, status){
        alert(jqXHR.responseJSON.msg)
      }
    });
    $.ajax({
      type: "POST",
      cache: false,
      data: {
        locked_value: locked_value
      },
      url: '/workflow/activity/lock/' + activity_id,
      success: function (result) {
        if (result.err) {
          $('#step_page').hide();
          $('#activity_locked').show();
          $('#locked_msg').show()
          var msg = $('#locked_msg').text();
          if (result.locked_by_username) {
            msg = msg.replace('{}', result.locked_by_username);
          } else {
            msg = msg.replace(' ({})', '');
            msg = msg.replace('（{}）', '');
          }
          $('#locked_msg').html(msg);

          if (current_user_email === result.locked_by_email) {
            $("#action_unlock_activity").modal("show");
            // handle popup unlock
            $('#btn_unlock').on('click', function () {
              $("#action_unlock_activity").modal("hide");
              unlock_activity(activity_id, result.locked_value);
              location.reload();
            });
          }
        } else {
          locked_value = result.locked_value;
          sessionStorage.setItem('locked_value', locked_value);
        }
      },
      error: function(jqXHR, status){
        alert(jqXHR.responseJSON.msg)
      }
    });
  } else if (locked_value) {
    unlock_activity(activity_id, locked_value);
  }

  // start: approval page
  $('#btn-return, #btn-reject, #btn-approval, .save-button, .done-button, .next-button').click(function () {
    locked_value = 0;
  });

  window.addEventListener('beforeunload', function (e) {
    if (locked_value) {
      unlock_activity(activity_id, locked_value);
    }
    user_unlock_activity(activity_id);
    console.log(e.type);
    // イベントをキャンセルする
    // e.preventDefault();
    // Chrome では returnValue を設定する必要がある
    e.returnValue = '';
  });

  window.addEventListener('unload', function (e) {
    if (locked_value) {
      unlock_activity(activity_id, locked_value);
    }
    user_unlock_activity(activity_id);
    console.log(e.type);
    // イベントをキャンセルする
    // e.preventDefault();
    // Chrome では returnValue を設定する必要がある
    // e.returnValue = '';
  });
});
