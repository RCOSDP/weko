require([
  "jquery",
  "bootstrap"
], function () {
  $('.btn-begin').on('click', function () {
      let post_uri = $('#post_uri').text();
      let workflow_id = $(this).data('workflow-id');
      let community = $(this).data('community');
      let post_data = {
          workflow_id: workflow_id,
          flow_id: $('#flow_' + workflow_id).data('flow-id'),
          itemtype_id: $('#item_type_' + workflow_id).data('itemtype-id')
      };
      if(community != ""){
        post_uri = post_uri+"?community="+ community;
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
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {}
      });
  });
  $('#btn-finish').on('click', function(){
    let post_uri = $('.cur_step').data('next-uri');
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 0
    };
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
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
  });
  $('#btn-draft').on('click', function(){
    let post_uri = $('.cur_step').data('next-uri');
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 1
    };
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
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
  });
  $('#btn-approval-req').on('click', function () {
      action_id = $('#hide-actionId').text();
      btn_id = "action_" + action_id;
      $('#' + btn_id).click();
  });
  $('#btn-approval').on('click', function () {
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
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
              alert('server error');
          }
      });
  });
  $('#btn-reject').on('click', function () {
      let uri_apo = $('.cur_step').data('next-uri');
      let act_ver = $('.cur_step').data('action-version');
      let post_data = {
          commond: $('#input-comment').val(),
          action_version: act_ver
      };
      uri_apo = uri_apo+"/rejectOrReturn/0";
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
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
              alert('server error');
          }
      });
  });
  $('#btn-return').on('click', function () {
      let uri_apo = $('.cur_step').data('next-uri');
      let act_ver = $('.cur_step').data('action-version');
      let post_data = {
          commond: $('#input-comment').val(),
          action_version: act_ver
      };
      uri_apo = uri_apo+"/rejectOrReturn/1";
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
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
              alert('server error');
          }
      });
  });
  $('#lnk_item_detail').on('click', function () {
    $('#myModal').modal('show');
  })
})
