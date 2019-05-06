require([
  "jquery",
  "bootstrap"
], function() {
  // Handle Quit btn on activity screens
  $("#btn_quit").click(function () {
    $("#action_quit_confirmation").modal("show");
  });

  // Handle Continue btn on modal Quit confirmation
  $('#btn_cancel').on('click', function(){
    $("#action_quit_confirmation").modal("hide");
    let comment = ''
    if ($('#input-comment') && $('#input-comment').val()) {
      comment = $('#input-comment').val();
    }
    let post_uri = $('.cur_step').data('cancel-uri');
    let data = {
      commond: comment,
      action_version: $('.cur_step').data('action-version'),

    };
    send(post_uri, data,
      function(data){
        if (data.code == 0) {
          alert(data.msg);
          //window.location.href = "/itemtypes/register";
        }
      },
      function(errmsg){
        alert('Error: ' + errmsg);
      });
  });

  // call API
  function send(url, data, handleSuccess, handleError){
    $.ajax({
      method: 'POST',
      url: url,
      async: true,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function(data,textStatus){
        handleSuccess(data);
      },
      error: function(textStatus,errorThrown){
        handleError(textStatus);
      }
    });
  }
});
