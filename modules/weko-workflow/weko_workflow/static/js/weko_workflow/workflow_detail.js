require([
  "jquery",
  "bootstrap"
],function() {
  $('.btn-begin').on('click', function(){
    let post_uri = $('#post_uri').text();
    let workflow_id = $(this).data('workflow-id');
    let post_data = {
      workflow_id: workflow_id,
      flow_id: $('#flow_'+workflow_id).data('flow-id'),
      itemtype_id: $('#item_type_'+workflow_id).data('itemtype-id')
    };
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function(data, status) {
        if(0 == data.code) {
          document.location.href=data.data.redirect;
        } else {
          alert(data.msg);
        }
      },
      error: function(jqXHE, status) {
      }
    });
  });
  $('.action-name').on('click', function(){
    $('#myModalLabel').text($(this).text());
    $('#hide-action-version').text($(this).data('action-version'));
    $('#hide-post-uri').text($(this).data('next-uri'));
    $('#myModal').modal('show');
  });
  $('#btn-finish').on('click', function(){
    let post_uri = $('#hide-post-uri').text();
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $('#hide-action-version').text()
    };
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function(data, status) {
        if(0 == data.code) {
          document.location.href=data.data.redirect;
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
})
