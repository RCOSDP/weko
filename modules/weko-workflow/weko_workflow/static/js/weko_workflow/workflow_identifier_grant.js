require([
  "jquery",
  "bootstrap"
], function () {
  data_global = {
    post_uri: '',
    post_data: {}
  }

  // prepare data for sending
  function preparePostData(tmp_save) {
    data_global.post_uri = $('.cur_step').data('next-uri');
    data_global.post_data = {
      identifier_grant: $("input[name='identifier_grant']:checked").val(),
      action_version: $('.cur_step').data('action-version'),
      temporary_save: tmp_save
    };
  }

  // send
  function send() {
    $.ajax({
      url: data_global.post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(data_global.post_data),
      success: function(data, status) {
        if(0 == data.code) {
          if(data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href=data.data.redirect;
          } else {
            document.location.reload(true);
          }
        } else {
          alert(data.msg);
        }
      },
      error: function(jqXHE, status) {
        alert('server error');
        $('#myModal').modal('hide');
      }
    });
  }

  // click button Next
  $('#btn-finish').on('click', function(){
    preparePostData(0);
    send();
  });

  // click button Save
  $('#btn-draft').on('click', function(){
    preparePostData(1);
    send();
  });

  $('#lnk_item_detail').on('click', function () {
    $('#myModal').modal('show');
  })
})
