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
    if ($('#input-comment') && $('#input-comment').val()) {
      comment = $('#input-comment').val();
    }
    let post_uri = $('.cur_step').data('cancel-uri');
    let request_uri = $('#post_url').text();
    let data = {
      commond: comment,
      action_version: $('.cur_step').data('action-version'),
      pid_value: request_uri.substring(request_uri.lastIndexOf("/") + 1, request_uri.length),
    };
    send(post_uri, data,
      function (data) {
        if (data && data.code == 0) {
          if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href = data.data.redirect;
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
        handleSuccess(data);
      },
      error: function (textStatus, errorThrown) {
        handleError(textStatus);
      }
    });
  };
});
