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
    var data = {'public_status': status};
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
        }
      },
      error: function (jqXHE, status) {
      }
    });
  });

  $('a#btn_edit').on('click', function () {
    $('[role="alert"]').hide();
    $(this).attr("disabled", true);
    $('#btn_delete').attr("disabled", true);
    $('#btn_ver_delete').attr("disabled", true);
    $('[role="msg"]').css('display', 'inline-block');
    let post_uri = "/items/prepare_edit_item";
    let pid_val = $(this).data('pid-value');
    let community = $(this).data('community');
    let post_data = {
      pid_value: pid_val
    };
    if (community) {
      post_uri = post_uri + "?c=" + community;
    }
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function (res, status) {
        $('[role="msg"]').hide();
        if (0 == res.code) {
          let uri = res.data.redirect.replace('api/', '')
          document.location.href = uri;
        } else {
          $('#btn_edit').removeAttr("disabled");
          $('#btn_delete').removeAttr("disabled");
          $('#btn_ver_delete').removeAttr("disabled");
          $('[role="alert"]').css('display', 'inline-block');
          $('[role="alert"]').text(res.msg);
          if ("activity_id" in res) {
            url = "/workflow/activity/detail/"+res.activity_id;
            if (community) {
              url = url + "?c=" + community;
            }
            $('[role="alert"]').append(' <a href=' + url + '>' + res.activity_id + '</a>')
          }
        }
      },
      error: function (jqXHE, status) {
        $('[role="msg"]').hide();
        $('#btn_edit').removeAttr("disabled");
        $('#btn_delete').removeAttr("disabled");
        $('#btn_ver_delete').removeAttr("disabled");
        $('[role="alert"]').css('display', 'inline-block');
        $('[role="alert"]').text("INTERNAL SERVER ERROR");
      }
    });
  });

  const del_msg = document.getElementById('del_msg').textContent;
  const del_ver_msg = document.getElementById('del_ver_msg').textContent;
  $('a#btn_delete').on('click', function () {
    $('#confirm_delete_content').text(del_msg);
    $('#confirm_delete').modal('show');
  });
  $('a#btn_ver_delete').on('click', function () {
    $('#confirm_ver_delete_content').text(del_ver_msg);
    $('#confirm_ver_delete').modal('show');
  });

  $('#confirm_delete_button').on('click', function () {
    $('#confirm_delete').modal('hide');
    $('[role="alert"]').hide();
    $('#btn_edit').attr("disabled", true);
    $('#btn_delete').attr("disabled", true);
    $('#btn_ver_delete').attr("disabled", true);
    $('[role="msg"]').css('display', 'inline-block');
    let post_uri = "/items/prepare_delete_item";
    let pid_val = $(this).data('pid-value');
    let community = $(this).data('community');
    let post_data = {
      pid_value: pid_val
    };
    if (community) {
      post_uri = post_uri + "?c=" + community;
    }
    // Added DOI check process
    let check_doi_uri = "/api/items/check_record_doi/" + pid_val;
    $.ajax({
      url: check_doi_uri,
      method: 'GET',
      async: true,
      success: function (res) {
        if (0 == res.code) {
          $('[role="msg"]').hide();
          $('[role="alert"]').css('display', 'inline-block');
          $('[role="alert"]').text($("#delete_message").val());
          $('#btn_edit').removeAttr("disabled");
          $('#btn_delete').removeAttr("disabled");
          $('#btn_ver_delete').removeAttr("disabled");
        } else {
          $.ajax({
            url: post_uri,
            method: 'POST',
            async: true,
            contentType: 'application/json',
            data: JSON.stringify(post_data),
            success: function (res, status) {
              $('[role="msg"]').hide();
              if (0 == res.code) {
                let uri = res.data.redirect.replace('api/', '')
                document.location.href = uri;
              } else {
                $('#btn_edit').removeAttr("disabled");
                $('#btn_delete').removeAttr("disabled");
                $('#btn_ver_delete').removeAttr("disabled");
                $('[role="alert"]').css('display', 'inline-block');
                $('[role="alert"]').text(res.msg);
                if ("activity_id" in res) {
                  url = "/workflow/activity/detail/"+res.activity_id;
                  if (community) {
                    url = url + "?c=" + community;
                  }
                  $('[role="alert"]').append(' <a href=' + url + '>' + res.activity_id + '</a>')
                }
              }
            },
            error: function (jqXHE, status) {
              $('[role="msg"]').hide();
              $('#btn_edit').removeAttr("disabled");
              $('#btn_delete').removeAttr("disabled");
              $('#btn_ver_delete').removeAttr("disabled");
              $('[role="alert"]').css('display', 'inline-block');
              $('[role="alert"]').text("INTERNAL SERVER ERROR");
            }
          });
        }
      },
      error: function (jqXHE, status) {
        $('[role="msg"]').hide();
        $('#btn_edit').removeAttr("disabled");
        $('#btn_delete').removeAttr("disabled");
        $('#btn_ver_delete').removeAttr("disabled");
        $('[role="alert"]').css('display', 'inline-block');
        $('[role="alert"]').text("Error api /api/items/check_record_doi/");
      }
    });
  });

  $('#confirm_ver_delete_button').on('click', function () {
    $('#confirm_ver_delete').modal('hide');
    $('[role="alert"]').hide();
    $('#btn_edit').attr("disabled", true);
    $('#btn_delete').attr("disabled", true);
    $('#btn_ver_delete').attr("disabled", true);
    $('[role="msg"]').css('display', 'inline-block');
    let post_uri = "/items/prepare_delete_item";
    let pid_val = $(this).data('pid-value');
    let community = $(this).data('community');
    let post_data = {
      pid_value: pid_val
    };
    if (community) {
      post_uri = post_uri + "?c=" + community;
    }
    // Extract PID
    // pid_val has del_ver and version information, so remove them here
    let pidParts = pid_val.split('_');
    let pidWithVer = pidParts[pidParts.length - 1];
    let pid = pidWithVer.split('.')[0];
    // Added DOI check process
    let check_doi_uri = "/api/items/check_record_doi/" + pid;
    $.ajax({
      url: check_doi_uri,
      method: 'GET',
      async: true,
      success: function (res) {
        if (0 == res.code) {
          $('[role="msg"]').hide();
          $('[role="alert"]').css('display', 'inline-block');
          $('[role="alert"]').text($("#delete_message").val());
          $('#btn_edit').removeAttr("disabled");
          $('#btn_delete').removeAttr("disabled");
          $('#btn_ver_delete').removeAttr("disabled");
        } else {
          $.ajax({
            url: post_uri,
            method: 'POST',
            async: true,
            contentType: 'application/json',
            data: JSON.stringify(post_data),
            success: function (res, status) {
              $('[role="msg"]').hide();
              if (0 == res.code) {
                let uri = res.data.redirect.replace('api/', '')
                document.location.href = uri;
              } else {
                $('#btn_edit').removeAttr("disabled");
                $('#btn_delete').removeAttr("disabled");
                $('#btn_ver_delete').removeAttr("disabled");
                $('[role="alert"]').css('display', 'inline-block');
                $('[role="alert"]').text(res.msg);
                if ("activity_id" in res) {
                  url = "/workflow/activity/detail/"+res.activity_id;
                  if (community) {
                    url = url + "?c=" + community;
                  }
                  $('[role="alert"]').append(' <a href=' + url + '>' + res.activity_id + '</a>')
                }
              }
            },
            error: function (jqXHE, status) {
              $('[role="msg"]').hide();
              $('#btn_edit').removeAttr("disabled");
              $('#btn_delete').removeAttr("disabled");
              $('#btn_ver_delete').removeAttr("disabled");
              $('[role="alert"]').css('display', 'inline-block');
              $('[role="alert"]').text("Error api /api/items/check_record_doi/");
            }
          });
        }
      }
    });
  });

  $('button#btn_close_msg').on('click', function () {
    $('[role="msg"]').hide();
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


  function startWorkflow(workflowId, communityId, recordId, fileName, itemTitle) {
    let post_uri = $('#post_uri').text();
    let dataType = $("#data_type_title").val();
    let post_data = {
      workflow_id: workflowId,
      flow_id: $('#flow_' + workflowId).data('flow-id'),
      itemtype_id: $('#item_type_' + workflowId).data('itemtype-id'),
      related_title: dataType,
      extra_info:  {
        file_name: fileName,
        record_id: recordId,
        is_restricted_access: true,
        user_mail: $("#current_user_email").val(),
        related_title : itemTitle
      }
    };
    if (typeof communityId !== 'undefined' && communityId !== "") {
      post_uri = post_uri + "?c=" + communityId;
    }
    var deferred = new $.Deferred();
    $.ajax({
      url: post_uri,
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(post_data),
    }).done(function (data) {
      if (0 === data.code) {
        let activity_url = data.data.redirect.split('/').slice(-1)[0];
        let activity_id = activity_url.split('?')[0];
        init_permission(recordId, fileName, activity_id);
        document.location.href = data.data.redirect;
      } else if(1 === data.code && data.data.is_download){
        const url = new URL(data.data.redirect , document.location.origin);
        url.searchParams.append('terms_of_use_only',true);
        document.location.href = url;
      } else {
        alert(data.msg);
      }
    }).fail(function (jqXHE, status) {
      console.log('fail:{}', jqXHE.message);
    }).always(function() {
      deferred.resolve();
    })
    return deferred;
  };

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
    let recordId = $(this).data('record-id');
    let fileName = $(this).data('filename');
    let itemTitle = $(this).data('itemtitle');
    startWorkflow(workflowId, communityId, recordId, fileName, itemTitle);
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

  $('.term_of_use_checked').on('click', function () {
    let $nextAction = $("#next_to_analysis");
    if ($('#term_of_use_checked').prop("checked") == true) {
      $nextAction.removeClass("disabled");
      $(this).attr("checked");
      $nextAction.attr("disabled", false);
    } else {
      $nextAction.addClass("disabled");
      $nextAction.attr("disabled", true);
    }
  });

  $('.btn-start-guest-wf').on('click', function () {
    let $confirmEmailBtn = $("#confirm_email_btn");
    $confirmEmailBtn.data("guest_filename_data", $(this).data("guest_filename_data"));
    $confirmEmailBtn.data("guest_data_type_title", $(this).data("guest_data_type_title"));
    $confirmEmailBtn.data("guest_record_id", $(this).data("guest_record_id"));
    $confirmEmailBtn.data("guest_itemtype_id", $(this).data("guest_itemtype_id"));
    $confirmEmailBtn.data("guest_workflow_id", $(this).data("guest_workflow_id"));
    $confirmEmailBtn.data("guest_flow_id", $(this).data("guest_flow_id"));
    $("#email_modal").modal("show");
  });

  $('.term_next').on('click', function () {
    var file_version_id = $("#" + this.id).data('file-version-id')
    let isGuest = $("#term_next_" + file_version_id).data("guest");
    if (isGuest == "True") {
      let $confirmEmailBtn = $("#confirm_email_btn");
      let btnSender = $("#btn-start-guest-wf-" + file_version_id)
      $confirmEmailBtn.attr("data-guest_filename_data", btnSender.data("guest_filename_data"));
      $confirmEmailBtn.attr("data-guest_data_type_title", btnSender.data("guest_data_type_title"));
      $confirmEmailBtn.attr("data-guest_record_id", btnSender.data("guest_record_id"));
      $confirmEmailBtn.attr("data-guest_itemtype_id", btnSender.data("guest_itemtype_id"));
      $confirmEmailBtn.attr("data-guest_workflow_id", btnSender.data("guest_workflow_id"));
      $confirmEmailBtn.attr("data-guest_flow_id", btnSender.data("guest_flow_id"));
      $("#term_and_condtion_modal_" + file_version_id).modal('toggle');
      setTimeout(function () {
        $("#email_modal").modal("show");
      }, 0);

    } else {
      let $btnStartWorkflow = $("#btn-start-workflow-" + file_version_id);
      let workflowId = $btnStartWorkflow.data('workflow-id');
      let communityId = $btnStartWorkflow.data('community');
      let recordId = $btnStartWorkflow.data('record-id');
      let fileName = $btnStartWorkflow.data('filename');
      let itemTitle =$btnStartWorkflow.data('itemtitle');
      var deferred = startWorkflow(workflowId, communityId, recordId, fileName, itemTitle);
      deferred.done(function(){
        $("#term_and_condtion_modal_" + file_version_id).modal("hide");
      });
    }
  });

  $('.next_to_analysis').on('click', function () {
    let analysis_url = $('#analysis_url').text();
    let permalink_uri = $('#permalink_uri').text();
    //let analysis_version = '/HEAD';
	let analysis_version =  '/' + new Date().getTime().toString(16)  + Math.floor(1000*Math.random()).toString(16);
    analysis_url = analysis_url + encodeURIComponent(permalink_uri) + analysis_version;
    window.open(analysis_url);
    $("#show_rights_info").modal("hide");
  });

  $(".term-condtion-modal").on("click", function () {
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

  $('#secret_url')?.on('click', function(){
    const webelement = $('#secret_url');
    if (webelement){
      const url = webelement.attr('url');
      webelement.prop('disabled' ,true);
      $.ajax({
        url: url,
        method: 'POST',
        contentType: 'application/json',
        data: null,
        success: function (responce) {
          webelement.prop('disabled',false);
          alert(responce);
        },
        error: function (jqXHE, status ,msg) {
          webelement.prop('disabled',false);
          alert(msg);
        }
      });
    }
  });
});
