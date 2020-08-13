require([
  "jquery",
  "bootstrap"
], function() {

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
        endLoading(_this);
        if (data.code == 0) {
          if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            parent.document.location.href = data.data.redirect;
          } else {
            let redirectUrl = "/workflow/activity/detail/" + $("#activity_id").text().trim();
            if (community_id) {
              redirectUrl += '?community=' + community_id;
            }
            parent.document.location.href = redirectUrl;
          }
        } else {
          $('#action_quit_confirmation').modal('show');
          $('.modal-body').html(data.msg);
          $("#btn_cancel").attr('style', 'display: none;');
        }
      },
      error: function (jqXHE, status) {
        endLoading(_this);
        $('#action_quit_confirmation').modal('show');
        $('.modal-body').html('Server error.');
        $("#btn_cancel").attr('style', 'display: none;');
        parent.document.location.href = "/workflow/activity/detail/" + $("#activity_id").text().trim();
      }
    });
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
            let redirectUrl = "/workflow/activity/detail/" + $("#activity_id").text().trim();
            parent.document.location.href = redirectUrl;
          }
        } else {
          $('#action_quit_confirmation').modal('show');
          $('.modal-body').html(data.msg);
          $("#btn_cancel").attr('style', 'display: none;');
        }
      },
      error: function (jqXHE, status) {
        endLoading(_this);
        $('#action_quit_confirmation').modal('show');
        $('.modal-body').html('Server error.');
        $("#btn_cancel").attr('style', 'display: none;');
        parent.document.location.href = "/workflow/activity/detail/" + $("#activity_id").text().trim();
      }
    });
  });
});
