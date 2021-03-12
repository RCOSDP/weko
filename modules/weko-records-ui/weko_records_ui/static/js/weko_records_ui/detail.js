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
    let post_uri = "/api/items/check_record_doi/" + urlHref[4];
    $.ajax({
      url: post_uri,
      method: 'GET',
      async: true,
      success: function (res) {
        if (0 == res.code) {
          $('[role="alert"]').css('display', 'inline-block');
          $('[role="alert"]').text($("#change_publish_message").val());
        } else {
          $("#public_status_form").submit();
        };
      },
      error: function (jqXHE, status) { }
    });
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
          $('[role="alert"]').css('display','inline-block');
          $('[role="alert"]').text(res.msg);
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


  function startWorkflow(workflowId, communityId) {
    let post_uri = $('#post_uri').text();
    let dataType = $("#data_type_title").val();
    let post_data = {
      workflow_id: workflowId,
      flow_id: $('#flow_' + workflowId).data('flow-id'),
      itemtype_id: $('#item_type_' + workflowId).data('itemtype-id'),
      related_title: dataType
    };
    if (typeof communityId !== 'undefined' && communityId !== "") {
      post_uri = post_uri + "?community=" + communityId;
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
  }

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

  $('.btn-start-workflow').on('click', function () {
    let workflowId = $(this).data('workflow-id');
    let communityId = $(this).data('community');
    startWorkflow(workflowId, communityId)
  });

  $('.term_checked').on('click', function () {
    var file_version_id = $('#' + this.id).data('file-version-id');
    let $nextAction = $("#term_next_" + file_version_id);
    if ($('#term_checked_' + file_version_id).prop("checked") == true) {
      $nextAction.removeClass("disabled");
      $(this).attr("checked");
      $nextAction.attr("disabled", false);
    } else {
      $nextAction.addClass("disabled");
      $nextAction.attr("disabled", true);
    }
  });

  $('.btn-start-guest-wf').on('click',function(){
    $("#confirm_email_btn").data("guest_filename_data", $(this).data("guest_filename_data"));
    $("#confirm_email_btn").data("guest_data_type_title", $(this).data("guest_data_type_title"));
    $("#confirm_email_btn").data("guest_record_id", $(this).data("guest_record_id"));
    $("#confirm_email_btn").data("guest_itemtype_id", $(this).data("guest_itemtype_id"));
    $("#confirm_email_btn").data("guest_workflow_id", $(this).data("guest_workflow_id"));
    $("#email_modal").modal("show");
  });

  $('.term_next').on('click', function () {
    var file_version_id = $("#" + this.id).data('file-version-id')
    let isGuest = $("#term_next_" + file_version_id).data("guest");
    if (isGuest == "True") {
      var btnSender = $("#btn-start-guest-wf-" + file_version_id)
      $("#confirm_email_btn").attr("data-guest_filename_data", btnSender.data("guest_filename_data"));
      $("#confirm_email_btn").attr("data-guest_data_type_title", btnSender.data("guest_data_type_title"));
      $("#confirm_email_btn").attr("data-guest_record_id", btnSender.data("guest_record_id"));
      $("#confirm_email_btn").attr("data-guest_itemtype_id", btnSender.data("guest_itemtype_id"));
      $("#confirm_email_btn").attr("data-guest_workflow_id", btnSender.data("guest_workflow_id"));
      $("#confirm_email_btn").attr("data-guest_flow_id", btnSender.data("guest_flow_id"));
      $("#term_and_condtion_modal_"+file_version_id).modal('toggle');
      setTimeout(function () {
        $("#email_modal").modal("show")
      },0);

    } else {
      var file_version_id = $('#' + this.id).data('file-version-id');
      let workflowId = $("#btn-start-workflow-" + file_version_id).data('workflow-id');
      let communityId = $("#btn-start-workflow-" + file_version_id).data('community');
      startWorkflow(workflowId, communityId)
    }
  });

  $(".term-condtion-modal").on("click", function(){
    let modalId = $(this).data("modalId");
    $(modalId).modal("show");
  });


  var current_cite = '';
  $('body').on('DOMSubtreeModified', '#citationResult', function (e) {
    let cite = e.currentTarget.innerHTML;
    if (cite.indexOf('&amp;') !== -1) {
      cite = e.currentTarget.innerText;
    }
    cite = cite.replace(/<br>/g, '<br/>');
    if (cite !== '' && cite !== current_cite) {
      current_cite = cite;
      $('#citationResult').html(current_cite);
    }
  });
});
