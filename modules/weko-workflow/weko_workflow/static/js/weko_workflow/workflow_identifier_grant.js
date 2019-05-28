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
      identifier_grant_jalc_doi_suffix: getVal($("input[name='idf_grant_input_1']")),
      identifier_grant_jalc_doi_link: $("span[name='idf_grant_link_1']").text() + getVal($("input[name='idf_grant_input_1']")),
      identifier_grant_jalc_cr_doi_suffix: getVal($("input[name='idf_grant_input_2']")),
      identifier_grant_jalc_cr_doi_link: $("span[name='idf_grant_link_2']").text() + getVal($("input[name='idf_grant_input_2']")),
      identifier_grant_jalc_dc_doi_suffix: getVal($("input[name='idf_grant_input_3']")),
      identifier_grant_jalc_dc_doi_link: $("span[name='idf_grant_link_3']").text() + getVal($("input[name='idf_grant_input_3']")),
      identifier_grant_crni_link: $("span[name='idf_grant_link_4']").text(),
      action_version: $('.cur_step').data('action-version'),
      commond: '',
      temporary_save: tmp_save
    };
  }

  function getVal(inObject) {
    val = inObject.val();

    if (val === undefined) {
      return '';
    } else {
      return val;
    }
  }

  // send
  function send() {
    $.ajax({
      url: data_global.post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(data_global.post_data),
      success: function (data, status) {
        if (0 == data.code) {
          if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href = data.data.redirect;
          } else {
            document.location.reload(true);
          }
        } else {
          alert(data.msg);
        }
      },
      error: function (jqXHE, status) {
        alert('Server error');
        $('#myModal').modal('hide');
      }
    });
  }

  // click button Next
  $('#btn-finish').on('click', function () {
    preparePostData(0);
    send();
  });

  // click button Save
  $('#btn-draft').on('click', function () {
    preparePostData(1);
    send();
  });

  $('#btn_withdraw_confirm').on('click', function () {
    $('#action_withdraw_confirmation').modal('show');
  });

  $('#lnk_item_detail').on('click', function () {
    $('#myModal').modal('show');
  });
})
