require([
  "jquery",
  "bootstrap"
], function() {
  /*
  $(function(){
    history.pushState(null,null,null)
    window.addEventListener('popstate', function(e) {
      $('a.back-button')[0].click()
    });
  })
  */

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

  $("#step_item_login", parent.document).attr('height', '240px');

  $('#btn-back').on('click', function () {
    let redirectUri = null
    let guestRegistrationUrlInput = $('#current_guest_url')
    if (guestRegistrationUrlInput != null && guestRegistrationUrlInput.val() != null) {
      redirectUri = guestRegistrationUrlInput.val()
    } else {
      let origin = new URL(window.location.href).origin;
      redirectUri = origin + "/workflow/activity/detail/" + $("#activity_id").text().trim();
    }

    if (redirectUri != null) {
      document.location.href = redirectUri;
    } else {
      console.log("Item registration url cannot get.")
    }
  });

  $('#btn-finish').on('click', function(){
    let _this = $(this);
    startLoading(_this);
    let post_uri = $(".cur_step", parent.document).data('next-uri');
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $(".cur_step", parent.document).data('action-version'),
      temporary_save: 0
    };
    let community_id = $('#community_id').text();
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function (data, status) {
        if (data.code == 0) {
          if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            parent.document.location.href = data.data.redirect;
          } else {
            let redirectUrl = $('#current_guest_url').val();
            if (!redirectUrl) {
              redirectUrl = "/workflow/activity/detail/" + $("#activity_id").text().trim();
              if (community_id) {
                redirectUrl += '?c=' + community_id;
              }
            }
            parent.document.location.href = redirectUrl;
          }
        } else {
          endLoading(_this);
          $('#action_quit_confirmation').modal('show');
          $('.modal-body').html(data.msg);
          $("#btn_cancel").attr('style', 'display: none;');
        }
      },
      error: function (jqXHR, status) {
        endLoading(_this);
        $('#action_quit_confirmation').modal('show');
        if (jqXHR.responseJSON && jqXHR.responseJSON.msg) {
          $('.modal-body').html(jqXHR.responseJSON.msg);
        } else {
          $('.modal-body').html('Server error.');
        }
        $("#btn_cancel").attr('style', 'display: none;');
        parent.document.location.href = "/workflow/activity/detail/" + $("#activity_id").text().trim();
      }
    });
  });

  $('#link_record_detail').on('click', function () {
    $('#myModal').modal('show');
  });

  $('#btn-draft').on('click', function () {
    let _this = $(this);
    startLoading(_this);
    let post_uri = $(".cur_step", parent.document).data('next-uri');
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $(".cur_step", parent.document).data('action-version'),
      temporary_save: 1
    };
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function (data, status) {
        endLoading(_this);
        if (0 == data.code) {
          if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            parent.document.location.href = data.data.redirect;
          } else {
            $('#alerts').append(
              '<div id="alert-style" class="alert alert-light">' +
              '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
              '&times;</button>' + 'Model save success' + '</div>');
          }
        } else {
          $('#action_quit_confirmation').modal('show');
          $('.modal-body').html(data.msg);
          $("#btn_cancel").attr('style', 'display: none;');
        }
      },
      error: function (jqXHR, status) {
        endLoading(_this);
        $('#action_quit_confirmation').modal('show');
        if (jqXHR.responseJSON && jqXHR.responseJSON.msg) {
          $('.modal-body').html(jqXHR.responseJSON.msg);
        } else {
          $('.modal-body').html('Server error.');
        }
        $("#btn_cancel").attr('style', 'display: none;');
        parent.document.location.href = "/workflow/activity/detail/" + $("#activity_id").text().trim();
      }
    });
  });
});
