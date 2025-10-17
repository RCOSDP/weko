require([
  "jquery",
  "bootstrap"
], function () {
  // Handle Quit btn on activity screens
  $("#btn_quit").click(function () {
    $("#action_quit_confirmation").modal("show");
  });

  // Handle Continue btn on modal Quit confirmation
  $('#btn_cancel').on('click', function () {
    $("#action_quit_confirmation").modal("hide");
    $("#btn_quit").attr("disabled", true);
    let comment = ''
    let community = $('#community_id').text();
    let community_para = ''
    if (community) {
      community_para = '?c=' + community;
    }
    if ($('#input-comment') && $('#input-comment').val()) {
      comment = $('#input-comment').val();
    }
    let post_uri = $('.cur_step').data('cancel-uri');
    let request_uri = $('#post_url').text();
    let pid_val = request_uri.substring(request_uri.lastIndexOf("/") + 1, request_uri.length)
    if (!pid_val) {
      let pid_value_data = JSON.parse(sessionStorage.getItem("pid_value_data"))
      if (pid_value_data && pid_value_data.activity_id == $('#activity_id').text()) {
        pid_val = pid_value_data.pid_value_temp
      }
    }
    let data = {
      commond: comment,
      action_version: $('.cur_step').data('action-version'),
      pid_value: pid_val,
    };
    if(!validateSession())
      return;
    send(post_uri, data,
      function (data) {
        if (data && data.code == 0) {
          if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href = data.data.redirect + community_para;
          } else {
            document.location.reload(true);
          }
        } else {
          alert(data.msg);
          $("#btn_quit").attr("disabled", false);
        }
      },
      function (errmsg) {
        alert('Server error.');
      });
  });

  // call API
  function send(url, data, handleSuccess, handleError) {
    $.ajax({
      method: 'POST',
      url: url,
      async: true,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function (data, textStatus) {
        if(data.unauthorized){
          alert(data.msg);
          window.location.assign("/login/?next=" + window.location.pathname);
          return;
      }
        handleSuccess(data);
      },
      error: function (textStatus, errorThrown) {
        handleError(textStatus);
      }
    });
  };
});
function validateSession() {
  var isValid = true;
  if ($('#current_guest_email').val()) {
    return isValid;
  }
  $.ajax({
    url: '/items/sessionvalidate',
    method: 'POST',
    contentType: "application/json",
    async: false,
    success: function (data, status) {
      if (!data.unauthorized) {
        alert(data.msg)
        window.location.assign("/login/?next=" + window.location.pathname);
        isValid = false;
      } else {
        isValid = true;
      }
    },
    error: function (data, status) {
      var modalcontent = data;
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
      isValid = false;
    }
  });
  return isValid;
}
