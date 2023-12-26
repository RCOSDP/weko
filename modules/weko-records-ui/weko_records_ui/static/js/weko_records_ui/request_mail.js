$('#request_mail_btn')?.on('click', () => {
    const dt = new Date();
    const CALCULATION_MESSAGE = document.getElementById("calculation_message_initial").value;
    $("#calculation_message").text(CALCULATION_MESSAGE);
    // Get captcha and show modal
    $.ajax({
        url: '/api/v1/captcha/image',
        async: false,
        method: 'GET',
        success: function (response) {
            $("#request_captcha").attr('src', "data:image/png;base64," + response.image)
            $("#request_mail_dialog").modal("show");
            $('#request_mail_sender').val("");
            $('#subject').val("");
            $('#body').val("");
            $("#calculation_message").val("");
            $("#key").val(response.key);
            $("#ttl").val(response.ttl);
            $("#dt").val(dt);
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
        'key': $('#key').val(),
        'calculation_result': parseInt($('#calculation_result').val(), 10)
    }

    const ttl = $("#ttl").val();
    const dt = $("#dt").val();
    const nowDate = new Date();
    const limitDateSeconds =new Date(dt).setSeconds(new Date(dt).getSeconds() + parseInt(ttl));
    const limitDate = new Date(limitDateSeconds);
    const FAILED_MESSAGE = document.getElementById("failed_message").value;
    const CAPTCHA_IMAGE_TIMEOUT = document.getElementById("captcha_image_timeout").value;
  
    if(nowDate > limitDate){
      const dt = new Date();
      $.ajax({
        url: '/api/v1/captcha/image',
        async: false,
        method: 'GET',
        success: function (response) {
            $("#request_captcha").attr('src', "data:image/png;base64," + response.image);
            $("#key").val(response.key);
            $("#calculation_result").val(CAPTCHA_IMAGE_TIMEOUT);
            $("#calculation_message").text();
            $("#dt").val(dt);
        },
        error: function (jqXHE, status ,msg) {
          alert(msg);
        }
      });
    }else{
    current_path_pattern = /records\/(.+)/.exec(location.pathname)
    url = ['/api/v1/records', current_path_pattern[1], 'request-mail'].join('/')
    const webelement = $('#confirm_send_button');
    const EMAIL_SENT_SUCCESSFULLY =  document.getElementById("email_sent_successfully").value
    webelement.prop('disabled' ,true);
    $.ajax({
      url: url,
      method: 'POST',
      data: JSON.stringify(body_data),
      contentType:'application/json',
      dataType: 'json',
      success: function (response) {
        webelement.prop('disabled',false);
        alert(EMAIL_SENT_SUCCESSFULLY);
        $("#request_mail_sender").val("");
        $("#subject").val("");
        $("#body").val("");
        $("#calculation_result").val("");
        $("#calculation_message").val("");
      },
      error: function (jqXHE, status ,msg) {
        webelement.prop('disabled',false);
        alert(FAILED_MESSAGE);
      }
    });
    }
})