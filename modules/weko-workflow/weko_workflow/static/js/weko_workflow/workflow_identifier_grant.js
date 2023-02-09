require([
  "jquery",
  "bootstrap"
], function () {
  data_global = {
    post_uri: '',
    post_data: {}
  }
  var withdraw_form = $('form[name$=withdraw_doi_form]');
  const item_id = $('#item_id').val()

  /**
   * Start Loading
   * @param actionButton
   */
  function startLoading(actionButton) {
    if (actionButton) {
      actionButton.prop('disabled', true);
    }
    $(".lds-ring-background").removeClass("hidden");
  }

  /**
   * End Loading
   * @param actionButton
   */
  function endLoading(actionButton) {
    if (actionButton) {
      actionButton.removeAttr("disabled");
    }
    $(".lds-ring-background").addClass("hidden");
  }

  // click button Next
  $('#btn-finish').on('click', function () {
    startLoading($(this));
    if (callCheckRestrictDoiIndexes($(this))) return;
    if (preparePostData(0, $(this))) {
      sendQuitAction($(this));
    }
  });

  // click button Save
  $('#btn-draft').on('click', function () {
    startLoading($(this));
    if (callCheckRestrictDoiIndexes($(this))) return;
    if (preparePostData(1, $(this))) {
      sendQuitAction($(this));
    }
  });

  // click button Withdraw
  $('#btn_withdraw').on('click', function () {
    $('#action_withdraw_confirmation').modal('show');
  });

  $('#link_record_detail').on('click', function () {
    $('#myModal').modal('show');
  });

  $('button#btn_close_alert').on('click', function () {
    $('#pwd').parent().removeClass('has-error');
    $('#error-info').parent().hide();
  });

  // prepare data for sending
  function preparePostData(tmp_save, actionButton) {
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
    let identifier_grant_ndl_jalc_doi_link = $("span[name='idf_grant_link_4']").text() + getVal($("input[name='idf_grant_input_4']"));
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
      isSuffixFormat = validateLengDoi(arrayDoi, actionButton);
    } else {
      switch (identifier_grant) {
        case "0":
        case "4":
        default:
          break;
        case "1":
          isSuffixFormat = isDOISuffixFormat(identifier_grant_jalc_doi_link, identifier_grant_jalc_doi_suffix, actionButton);
          break;
        case "2":
          isSuffixFormat = isDOISuffixFormat(identifier_grant_jalc_cr_doi_link, identifier_grant_jalc_cr_doi_suffix, actionButton);
          break;
        case "3":
          isSuffixFormat = isDOISuffixFormat(identifier_grant_jalc_dc_doi_link, identifier_grant_jalc_dc_doi_suffix, actionButton);
          break;
      }
    }

    return isSuffixFormat;
  }

  function validateLengDoi(arrayDoi, actionButton) {
    let msg = '';
    let result = true;
    for (index = 0; index < arrayDoi.length; ++index) {
      if (arrayDoi[index].length > 255) {
        msg = $('#msg_length_doi').val();
        result = false;
      }
    }
    if (!result) {
      endLoading(actionButton);
      alert(msg);
    }
    return result;
  }

  function isDOISuffixFormat(doi_link, doi_suffix, actionButton) {

    //let regexDOI = /^[_\-.;()\/A-Za-z0-9]+$/gi;
    let regexDOI = /^.+$/gi;
    let msg = '';
    let result = true;

    if (doi_suffix == "" || doi_suffix == null) {
      endLoading(actionButton);
      msg = $('#msg_required_doi').val();
      result = false;
    } else if (!regexDOI.test(doi_suffix)) {
      endLoading(actionButton);
      msg = $('#msg_format_doi').val();
      result = false;
    } else if (doi_link.length > 255) {
      endLoading(actionButton);
      msg = $('#msg_length_doi').val();
      result = false;
    } else {
      let isExistDOI = checkDOIExisted(doi_link)
      if (isExistDOI) {
        msg = isExistDOI;
        result = false;
      }
    }

    if (!result) {
      endLoading(actionButton);
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

  $('#btnContinue').on('click', function () {
    let activity_id = $("#activity_id").text().trim();
    let action_id = $("#hide-actionId").text().trim();
    let cancel_uri = '/workflow/activity/action/' + activity_id + '/' + action_id + '/cancel'
    let cancel_data = {
      commond: 'Auto cancel because workflow setting be changed.',
      action_version: '',
      pid_value: ''
    };
    $.ajax({
      method: 'POST',
      url: cancel_uri,
      async: true,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(cancel_data),
      success: function (data, textStatus) {
        if (data && data.code == 0) {
          document.location.href = '/workflow';
        } else {
          alert(data.msg);
        }
      },
      error: function (jqXHR, textStatus, errorThrown) {
        if (jqXHR.responseJSON && jqXHR.responseJSON.code==-1){
          alert(jqXHR.responseJSON.msg);
        }else {
          alert('Server error.');
        }
      }
    });
  });

  // send
  function sendQuitAction(actionButton) {
    let post_uri = data_global.post_uri;
    if (!post_uri) {
      let error_msg = $('#AutoCancelMsg').text();
      $('#cancelModalBody').text(error_msg);
      $('#cancelModal').modal('show');
    }
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
        } else if (-2 == data.code) {
          let error_msg = $('#AutoCancelMsg').text();
          $('#cancelModalBody').text(error_msg);
          $('#cancelModal').modal('show');
        } else {
          endLoading(actionButton);
          if (data.msg) {
            alert(data.msg);
          }
        }
      },
      error: function (jqXHE, status) {
        endLoading(actionButton);
        alert('Server error');
        $('#myModal').modal('hide');
      }
    });
  }

  withdraw_form.submit(function (event) {
    let withdrawBtn = $('#btn_withdraw_continue');
    startLoading(withdrawBtn);
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
          endLoading(withdrawBtn);
          $('#pwd').parent().addClass('has-error');
          $('#error-info').html(data.msg);
          $('#error-info').parent().show();
        }
      },
      error: function (jqXHR, status) {
        if (jqXHR.status === 500) {
          var response = JSON.parse(jqXHR.responseText);
          alert(response.msg);
        } else {
          alert('Server error');
        }
        endLoading(withdrawBtn);
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

  function checkRestrictDoiIndexes(doi = 0, actionButton) {
    let result = true;
    startLoading(actionButton);
    $.ajax({
      url: '/api/items/check_record_doi_indexes/' + item_id + '?doi=' + doi,
      method: 'GET',
      async: false,
      contentType: 'application/json; charset=UTF-8',
      dataType: "json",
      success: function (data, status) {
        if (-1 === data.code) {
          $("#restrict_doi_modal").modal("show");
          endLoading(actionButton);
        } else {
          result = false;
        }
      },
      error: function (jqXHE, status) {
        alert('Server error');
        endLoading(actionButton);
      }
    });
    return result;
  }

  function callCheckRestrictDoiIndexes(actionButton) {
    let identifier_grant = $("input[name='identifier_grant']:checked").val();
    if (identifier_grant > 0) {
      return checkRestrictDoiIndexes(identifier_grant, actionButton);
    } else if ($('#btn_withdraw').length > 0) {
      return checkRestrictDoiIndexes(0, actionButton);
    }
    return false;
  }

  $('#restrict_doi_button').click(function () {
    $("#restrict_doi_modal").modal("hide");
    let _this = $(this);
    startLoading(_this);
    let uri_apo = $('.cur_step').data('next-uri');
    let act_ver = $('.cur_step').data('action-version');
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: act_ver
    };
    uri_apo = uri_apo + "/rejectOrReturn/1";
    $.ajax({
      url: uri_apo,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function (data, status) {
        if (0 == data.code) {
          if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href = data.data.redirect;
          } else {
            document.location.reload(true);
          }
        } else {
          endLoading(_this);
          alert(data.msg);
        }
      },
      error: function (jqXHR, status) {
        if ((-2 == jqXHR.responseJSON.code) || (-1 == jqXHR.responseJSON.code)){
          endLoading(_this);
          alert(jqXHR.responseJSON.msg);
        } else {
          endLoading(_this);
          alert('server error');
        }
      }
    });
  });
})
