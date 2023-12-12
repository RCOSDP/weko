$('#request_mail_btn')?.on('click', () => {
    // Get captcha and show modal
    $.ajax({
        url: '/api/v1/captcha/image',
        async: false,
        method: 'GET',
        success: function (response) {
            $("#request_captcha").attr('src', "data:image/png;base64," + response.image)
            $("#request_mail_dialog").modal("show");
        },
        error: function (jqXHE, status ,msg) {
          alert(msg);
        }
      });
})

$('#reload_captcha_btn')?.on('click', () => {
    // Reload captcha and show modal
    $.ajax({
        url: '/api/v1/captcha/image',
        async: false,
        method: 'GET',
        success: function (response) {
            $("#request_captcha").attr('src', "data:image/png;base64," + response.image)
        },
        error: function (jqXHE, status ,msg) {
          alert(msg);
        }
      });
})

let mail_form = $('#request_mail_form')
mail_form?.on('submit', (e) => {
    // Get request mail info and post to send email
    e.preventDefault();
    // write content
    const body_data = {
        'from': $('#request_mail_sender').val(),
        'subject': $('#subject').val(),
        'message': $('#body').val(),
        'key': 'test',
        'calculation_result': parseInt($('#calculation_result').val(), 10)
    }

    current_path_pattern = /records\/(.+)/.exec(location.pathname)
    url = ['/api/v1/records', current_path_pattern[1], 'request-mail'].join('/')
    const webelement = $('#confirm_send_button');
    webelement.prop('disabled' ,true);
    $.ajax({
      url: url,
      method: 'POST',
      data: JSON.stringify(body_data),
      contentType:'application/json',
      dataType: 'json',
      success: function (response) {
        webelement.prop('disabled',false);
        alert(response);
      },
      error: function (jqXHE, status ,msg) {
        webelement.prop('disabled',false);
        alert(msg);
      }
    });
})