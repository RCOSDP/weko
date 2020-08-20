require([
  "jquery",
  "bootstrap"
], function () {

  /**
   * Start Loading
   * @param actionButton
   */
  function startLoading(actionButton) {
    actionButton.prop('disabled', true);
    $(".lds-ring-background").removeClass("hidden");
  }

  /**
   * End Loading
   * @param actionButton
   */
  function endLoading(actionButton) {
    actionButton.removeAttr("disabled");
    $(".lds-ring-background").addClass("hidden");
  }

  $('.btn-begin').on('click', function () {
    let _this = $(this);
    startLoading(_this);
    let post_uri = $('#post_uri').text();
    let workflow_id = $(this).data('workflow-id');
    let community = $(this).data('community');
    let post_data = {
      workflow_id: workflow_id,
      flow_id: $('#flow_' + workflow_id).data('flow-id'),
      itemtype_id: $('#item_type_' + workflow_id).data('itemtype-id')
    };
    if (community != "") {
      post_uri = post_uri + "?community=" + community;
    }
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function (data, status) {
        if (0 == data.code) {
          document.location.href = data.data.redirect;
        } else {
          endLoading(_this);
          alert(data.msg);
        }
      },
      error: function (jqXHE, status) {
        endLoading(_this);
      }
    });
  });

  $('#btn-finish').on('click', function () {
    let _this = $(this);
    startLoading(_this);
    let comment = '';
    if ($('#input-comment') && $('#input-comment').val()) {
      comment = $('#input-comment').val();
    }

    let post_uri = $('.cur_step').data('next-uri');
    let post_data = {
      commond: comment,
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 0
    };
    // Get Journal
    if ($('#action-journal')) {
      if ($('#action-journal').text()) {
        post_data['journal'] = $.parseJSON($('#action-journal').text());
      } else {
        if ($("#journal-info").attr("hidden")) {
          if ($('#search-key').val()) {
            post_data['journal'] = {keywords: $('#search-key').val()};
          }
        }
      }
    }

    $.ajax({
      url: post_uri,
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
      error: function (jqXHE, status) {
        endLoading(_this);
        alert('server error');
        $('#myModal').modal('hide');
      }
    });
  });

  $('#btn-draft').on('click', function () {
    let _this = $(this);
    startLoading(_this);
    let comment = ''
    if ($('#input-comment') && $('#input-comment').val()) {
      comment = $('#input-comment').val();
    }

    let post_uri = $('.cur_step').data('next-uri');
    let post_data = {
      commond: comment,
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 1
    };

    // Get Journal
    if ($('#action-journal')) {
      if ($('#action-journal').text()) {
        post_data['journal'] = $.parseJSON($('#action-journal').text());
      } else {
        if ($("#journal-info").attr("hidden")) {
          if ($('#search-key').val()) {
            post_data['journal'] = {keywords: $('#search-key').val()};
          } else {
            post_data['journal'] = {keywords: ''};
          }
        }
      }
    }
    $.ajax({
      url: post_uri,
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
      error: function (jqXHE, status) {
        endLoading(_this);
        alert('server error');
        $('#myModal').modal('hide');
      }
    });
  });

  $('#btn-approval-req').on('click', function () {
    action_id = $('#hide-actionId').text();
    btn_id = "action_" + action_id;
    $('#' + btn_id).click();
  });

  $('#btn-approval').on('click', function () {
    let _this = $(this);
    startLoading(_this);
    let uri_apo = $('.cur_step').data('next-uri');
    let act_ver = $('.cur_step').data('action-version');
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: act_ver
    };
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
      error: function (jqXHE, status) {
        endLoading(_this);
        alert('server error');
      }
    });
  });

  $('#btn-reject').on('click', function () {
    let _this = $(this);
    startLoading(_this);
    let uri_apo = $('.cur_step').data('next-uri');
    let act_ver = $('.cur_step').data('action-version');
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: act_ver
    };
    uri_apo = uri_apo + "/rejectOrReturn/0";
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
      error: function (jqXHE, status) {
        endLoading(_this);
        alert('server error');
      }
    });
  });

  $('#btn-return').on('click', function () {
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
      error: function (jqXHE, status) {
        endLoading(_this);
        alert('server error');
      }
    });
  });

  $('#lnk_item_detail').on('click', function () {
    $('#myModal').modal('show');
  });
})

/*
  Hide preview area show photo.
  Hide html tag <hr> which is next element of preview area show photo.
*/
if(Number($('#preview_count').val()) == 0){
  if($('#main_preview_carousel_panel').length){
    /* 'Approval' step of registed processing */
    $('#main_preview_carousel_panel').next('hr').addClass('hide')
    $('#main_preview_carousel_panel').addClass('hide')
  }
  if($('#modal_preview_carousel_panel').length) {
    /* 'End' step of registed processing */
    $('#modal_preview_carousel_panel').addClass('hide')
    $('#modal_preview_carousel_panel').next().addClass('hide')
  }
}
