$('#request_mail_btn')?.on('click', () => {
  const CALCULATION_MESSAGE = document.getElementById("calculation_message_initial").value;
  $("#calculation_message").text(CALCULATION_MESSAGE);
  clear_mail_form()
  // Get captcha and show modal
  load_captcha_image().done((response) => {
    $("#request_mail_dialog").modal("show");
  }).fail((jqXHE, status, msg) => {
    alert(msg);
  });
})

let mail_form = $('#request_mail_form')
 mail_form?.on('submit', (e) => {
  // Get request mail info and post to send email
  e.preventDefault();

  const ttl = $("#ttl").val();
  const dt = $("#dt").val();
  const nowDate = new Date();
  const limitDateSeconds = new Date(dt).setSeconds(new Date(dt).getSeconds() + parseInt(ttl));
  const limitDate = new Date(limitDateSeconds);
  const FAILED_MESSAGE = document.getElementById("failed_message").value;
  const CAPTCHA_IMAGE_TIMEOUT = document.getElementById("captcha_image_timeout").value;

  if (nowDate > limitDate) {
    $("#calculation_message").text(CAPTCHA_IMAGE_TIMEOUT);
    load_captcha_image().done((response) => {
      $("#calculation_result").val("");
    }).fail(function (jqXHE, status, msg) {
      alert(msg);
    });
  } else {
    const webelement = $('#confirm_send_button');
    webelement.prop('disabled', true);
    const authorization_url = '/api/v1/captcha/validate';
    const authorization_body = {
      'key': $('#key').val(),
      'calculation_result': parseInt($('#calculation_result').val(), 10)
    };
    $.ajax({
      url: authorization_url,
      method: 'POST',
      data: JSON.stringify(authorization_body),
      contentType: 'application/json',
      dataType: 'json'
    }).then((response) => {
      const re = /records\/(.+)/;
      const reg_result = re.exec(location.pathname);
      const recid = reg_result[1];
      const url = ['/api/v1/records', recid, 'request-mail'].join('/');
      // write content
      const request_mail_body = {
        'from': $('#request_mail_sender').val(),
        'subject': $('#subject').val(),
        'message': $('#body').val(),
        'key': $('#key').val(),
        'authorization_token': response.authorization_token
      };
      return $.ajax({
        url: url,
        method: 'POST',
        data: JSON.stringify(request_mail_body),
        contentType: 'application/json',
        dataType: 'json'
      });
    }).then((response) => {
      const EMAIL_SENT_SUCCESSFULLY = document.getElementById("email_sent_successfully").value
      webelement.prop('disabled', false);
      alert(EMAIL_SENT_SUCCESSFULLY);
      clear_mail_form()
      $("#calculation_message").val("");
    }).fail((jqXHE, status, msg) => {
      webelement.prop('disabled', false);
      if (jqXHE.status == 500) {
        alert("Internal Server Error.")
      } else {
        alert(FAILED_MESSAGE);
      }
      load_captcha_image().done((response) => {
        const CALCULATION_MESSAGE = document.getElementById("calculation_message_initial").value;
        $("#calculation_result").val("");
        $("#calculation_message").text(CALCULATION_MESSAGE);
      }).fail(function (jqXHE, status, msg) {
        alert(msg);
      });
    });
  }
})

function load_captcha_image() {
  return $.ajax({
    url: '/api/v1/captcha/image',
    async: false,
    method: 'GET'
  }).then((response) => {
    const dt = new Date();
    $("#request_captcha").attr('src', "data:image/png;base64," + response.image)
    $("#key").val(response.key);
    $("#ttl").val(response.ttl);
    $("#dt").val(dt);
  })
}

function clear_mail_form() {
  $('#request_mail_sender').val("");
  $('#subject').val("");
  $('#body').val("");
  $("#calculation_result").val("");
}