require([
  "jquery",
  "bootstrap"
], function () {
  data_global = {
    post_uri: '',
    post_data: {}
  }
  var withdraw_form = $('form[name$=withdraw_doi_form]');

  // click button Next
  $('#btn-finish').on('click', function () {
    if (preparePostData(0)) {
      sendQuitAction();
    }
  });

  // click button Save
  $('#btn-draft').on('click', function () {
    if (preparePostData(1)) {
      sendQuitAction();
    }
  });

  // click button Withdraw
  $('#btn_withdraw').on('click', function () {
    $('#action_withdraw_confirmation').modal('show');
  });

  $('#lnk_item_detail').on('click', function () {
    $('#myModal').modal('show');
  });

  $('button#btn_close_alert').on('click', function () {
    $('#pwd').parent().removeClass('has-error');
    $('#error-info').parent().hide();
  });

  // prepare data for sending
  function preparePostData(tmp_save) {
    let isSuffixFormat = true;
    data_global.post_uri = $('.cur_step').data('next-uri');

    let identifier_grant = $("input[name='identifier_grant']:checked").val();
    let identifier_grant_jalc_doi_suffix = getVal($("input[name='idf_grant_input_1']"));
    let identifier_grant_jalc_doi_link = $("span[name='idf_grant_link_1']").text() + getVal($("input[name='idf_grant_input_1']"));
    let identifier_grant_jalc_cr_doi_suffix = getVal($("input[name='idf_grant_input_2']"));
    let identifier_grant_jalc_cr_doi_link = $("span[name='idf_grant_link_2']").text() + getVal($("input[name='idf_grant_input_2']"));
    let identifier_grant_jalc_dc_doi_suffix = getVal($("input[name='idf_grant_input_3']"));
    let identifier_grant_jalc_dc_doi_link = $("span[name='idf_grant_link_3']").text() + getVal($("input[name='idf_grant_input_3']"));
    let identifier_grant_ndl_jalc_doi_suffix = getVal($("input[name='idf_grant_input_4']"));
    let identifier_grant_ndl_jalc_doi_link = $("span[name='idf_grant_link_4']").text() + getVal($("input[name='idf_grant_input_5']"));
    let identifier_grant_crni_link = $("span[name='idf_grant_link_5']").text();

    data_global.post_data = {
      identifier_grant: identifier_grant,
      identifier_grant_jalc_doi_suffix: identifier_grant_jalc_doi_suffix,
      identifier_grant_jalc_doi_link: identifier_grant_jalc_doi_link,
      identifier_grant_jalc_cr_doi_suffix: identifier_grant_jalc_cr_doi_suffix,
      identifier_grant_jalc_cr_doi_link: identifier_grant_jalc_cr_doi_link,
      identifier_grant_jalc_dc_doi_suffix: identifier_grant_jalc_dc_doi_suffix,
      identifier_grant_jalc_dc_doi_link: identifier_grant_jalc_dc_doi_link,
      identifier_grant_ndl_jalc_doi_suffix: identifier_grant_ndl_jalc_doi_suffix,
      identifier_grant_ndl_jalc_doi_link: identifier_grant_ndl_jalc_doi_link,
      identifier_grant_crni_link: identifier_grant_crni_link,
      action_version: $('.cur_step').data('action-version'),
      commond: '',
      temporary_save: tmp_save
    };

    let idf_grant_method = $('#idf_grant_method').val();
    if (tmp_save == 1 || idf_grant_method == 0) {
      let arrayDoi = [identifier_grant_jalc_doi_link, identifier_grant_jalc_cr_doi_link, identifier_grant_jalc_dc_doi_link];
      isSuffixFormat = validateLengDoi(arrayDoi);
    } else {
      switch (identifier_grant) {
        case "0":
        case "4":
        default:
          break;
        case "1":
          isSuffixFormat = isDOISuffixFormat(identifier_grant_jalc_doi_link, identifier_grant_jalc_doi_suffix);
          break;
        case "2":
          isSuffixFormat = isDOISuffixFormat(identifier_grant_jalc_cr_doi_link, identifier_grant_jalc_cr_doi_suffix);
          break;
        case "3":
          isSuffixFormat = isDOISuffixFormat(identifier_grant_jalc_dc_doi_link, identifier_grant_jalc_dc_doi_suffix);
          break;
      };
    }

    return isSuffixFormat;
  }

  function validateLengDoi(arrayDoi) {
    let msg = '';
    let result = true;
    for (index = 0; index < arrayDoi.length; ++index) {
      if (arrayDoi[index].length > 255) {
        msg = $('#msg_length_doi').val();
        result = false;
      }
    }
    if (!result) {
      alert(msg);
    }
    return result;
  }

  function isDOISuffixFormat(doi_link, doi_suffix) {

    let regexDOI = /^[_\-.;()\/A-Za-z0-9]+$/gi;
    let msg = '';
    let result = true;

    if (doi_suffix == "" || doi_suffix == null) {
      msg = $('#msg_required_doi').val();
      result = false;
    } else if (!regexDOI.test(doi_suffix)) {
      msg = $('#msg_format_doi').val();
      result = false;
    } else if (doi_link.length > 255) {
      msg = $('#msg_length_doi').val();
      result = false;
    } else {
      isExistDOI = checkDOIExisted(doi_link)
      if (isExistDOI) {
        msg = isExistDOI;
        result = false;
      }
    }

    if (!result) {
      alert(msg);
    }
    return result;
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
  function sendQuitAction() {
    $.ajax({
      url: data_global.post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(data_global.post_data),
      success: function (data, status) {
        if (0 == data.code) {
          if (data.hasOwnProperty('data') &&
            data.data.hasOwnProperty('redirect')) {
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

  withdraw_form.submit(function (event) {
    $('#btn_withdraw_continue').prop('disabled', true);
    let form = withdraw_form;
    let withdraw_uri = form.attr('action');
    let post_data = {
      passwd: $('#pwd').val()
    };
    $.ajax({
      url: withdraw_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function (data, status) {
        if (0 == data.code) {
          if (data.hasOwnProperty('data') &&
            data.data.hasOwnProperty('redirect')) {
            document.location.href = data.data.redirect;
          } else {
            document.location.reload(true);
          }
        } else {
          $('#pwd').parent().addClass('has-error');
          $('#error-info').html(data.msg);
          $('#error-info').parent().show();
        }
        $('#btn_withdraw_continue').prop('disabled', false);
      },
      error: function (jqXHE, status) {
        alert('Server error');
        $('#btn_withdraw_continue').prop('disabled', false);
      }
    });
    event.preventDefault();
  });

  function checkDOIExisted(doi_link) {
    let getUrl = '/workflow/findDOI';
    let data = {
      'doi_link': doi_link
    };
    let isExistedDOI = false;
    $.ajax({
      type: 'POST',
      url: getUrl,
      contentType: 'application/json; charset=UTF-8',
      async: false,
      data: JSON.stringify(data),
      dataType: "json",
      success: function (data, status) {
        if (0 == data.code) {
          if (data.isExistDOI || data.isWithdrawnDoi) {
            isExistedDOI = data.msg;
          }
        }
      },
      error: function (jqXHE, status) {
        alert('Server error');
      }
    });

    return isExistedDOI;
  }
})
