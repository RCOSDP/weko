require([
  "jquery",
  "bootstrap",
  "typeahead.js",
  "bloodhound",
  "node_modules/angular/angular",

  // "node_modules/invenio-csl-js/dist/invenio-csl-js",
], function (typeahead, Bloodhound) {
  $('#btn_back').on('click', function () {
    window.history.back();
  });

  $('#public_status_btn').on('click', function () {
    var status = $(this).val();
    var data = { 'public_status': status };
    var urlHref = window.location.href.split('/')
    const url = urlHref[0] + '//' + urlHref[2] + '/records/' + urlHref[4] + '/pubstatus'
    $.ajax({
      url: url,
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(data),
      dataType: 'json'
    });
    if (status == 'Public') {
      $(this).text('Change to Public');
      $(this).val('Private');
      $('#public_status').text('Private');
    } else {
      $(this).text('Change to Private');
      $(this).val('Public');
      $('#public_status ').text('Public');
    };
  });

  $('a#btn_edit').on('click', function () {
    let post_uri = "/api/items/prepare_edit_item";
    let pid_val = $(this).data('pid-value');
    let community = $(this).data('community');
    let post_data = {
      pid_value: pid_val
    };
    if (community) {
      post_uri = post_uri + "?community=" + community;
    }
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function (res, status) {
        if (0 == res.code) {
          let uri = res.data.redirect.replace('api/', '')
          document.location.href = uri;
        } else {
          if (res.code = -13) {
            $('[role="alert"]').css('display','inline-block');
          } else {
            alert(res.msg);
          }
        }
      },
      error: function (jqXHE, status) { }
    });
  });

  $('button#btn_close_alert').on('click', function () {
    $('[role="alert"]').hide();
  });

  angular.element(document).ready(function () {
    angular.bootstrap(document.getElementById("invenio-csl"), [
      'invenioCsl',
    ]
    );
  });

  $('.btn-start-workflow').on('click', function () {
    let post_uri = $('#post_uri').text();
    let workflow_id = $(this).data('workflow-id');
    let community = $(this).data('community');
    let itemTitle = $(this).data('itemtitle');
    let post_data = {
      workflow_id: workflow_id,
      flow_id: $('#flow_' + workflow_id).data('flow-id'),
      itemtype_id: $('#item_type_' + workflow_id).data('itemtype-id')
    };
    if (typeof community !== 'undefined' && community !== "") {
      post_uri = post_uri + "?community=" + community;
    }
    if (typeof itemTitle !== 'undefined' && itemTitle !== "") {
        post_uri = post_uri + "?itemtitle=" + itemTitle;
    }

    let record_id = $('#recid').text();
    let file_name = $('#file_name').text();
    $.ajax({
      url: post_uri,
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function (data) {
        if (0 === data.code) {
          let activity_url = data.data.redirect.split('/').slice(-1)[0];
          let activity_id = activity_url.split('?')[0];
          init_permission(record_id, file_name, activity_id);
          document.location.href = data.data.redirect;
        } else {
          alert(data.msg);
        }
      },
      error: function (jqXHE, status) {
      }
    });

    function init_permission(record_id, file_name, activity_id) {
      let init_permission_uri = '/records/permission/';

      init_permission_uri = init_permission_uri + record_id;
      let post_data_permission = {
        file_name: file_name,
        activity_id: activity_id
      };
      $.ajax({
        url: init_permission_uri,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(post_data_permission),
        success: function (data, status) {
        },
        error: function (jqXHE, status) {
        }
      });
    }
  });
});
