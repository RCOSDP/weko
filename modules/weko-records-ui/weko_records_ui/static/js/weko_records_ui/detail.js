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
              url = url + "?community=" + community;
            }
            $('[role="alert"]').append('<a href=' + url + '>' + res.activity_id + '</a>')
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
      post_uri = post_uri + "?community=" + communityId;
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

    // シークレットURL作成フォーム
    // link_name フィールドの入力を検証
    const MAX_LENGTH=50;
    const linkNameInput = document.querySelector('#link_name');
    if (linkNameInput) {
      linkNameInput.maxLength = MAX_LENGTH;
    }

    // APIエンドポイントから設定を取得
    fetch('/get-secret-settings')
      .then(response => {
        if (!response.ok) {
          throw new Error(`Network response was not ok: ${response.statusText}`);
        }
        return response.json();
      })
      .then(data => {
        // APIからのデータをフォームに反映
        const secretDownloadLimit = data.secret_download_limit;
        const secretExpirationDate = data.secret_expiration_date;
        const maxSecretExpirationDate = data.max_secret_expiration_date;
        const maxSecretDownloadLimit = data.max_secret_download_limit;

        // 今日の日付を取得
        const today = new Date();
        const todayFormatted = today.toISOString().split('T')[0];

        // secret_expiration_date を使用して日付を計算
        const expirationDate = new Date();
        expirationDate.setDate(today.getDate() + parseInt(secretExpirationDate, 10));
        const formattedDate = expirationDate.toISOString().split('T')[0];

        // maxSecretExpirationDate を適切な日付形式に変換
        const maxDate = new Date();
        maxDate.setDate(maxDate.getDate() + parseInt(maxSecretExpirationDate, 10));
        const maxFormattedDate = maxDate.toISOString().split('T')[0];

        // <input type="date">要素に設定
        const expirationDateInput = document.querySelector('#expiration_date');
        if (expirationDateInput) {
          expirationDateInput.value = formattedDate;
          expirationDateInput.max = maxFormattedDate;
          expirationDateInput.min = todayFormatted;
        }
        // フォームのフィールドに値を設定
        const downloadLimitInput = document.querySelector('#download_limit');
        if (downloadLimitInput) {
          downloadLimitInput.value = secretDownloadLimit;
          // maxSecretDownloadLimit 以上の入力を制御
          downloadLimitInput.addEventListener('input', function () {
            if (parseInt(downloadLimitInput.value, 10) > maxSecretDownloadLimit) {
              downloadLimitInput.value = maxSecretDownloadLimit;
            }
          });
        }
        // 有効期限の下に表示するメッセージを設定
        const maxExpirationData = document.querySelector('#max_date_display');
        if (maxExpirationData) {
          const translationDate = maxExpirationData.dataset.expirationDate;
          maxExpirationData.textContent = ` ※${translationDate} ${maxFormattedDate}`;
        }
        // ダウンロード制限の下に表示するメッセージを設定
        const maxDownloadDisplay = document.querySelector('#max_download_display');
        if (maxDownloadDisplay) {
          const downloadcount = maxDownloadDisplay.dataset.downloadCount;
          maxDownloadDisplay.textContent = ` ※${downloadcount} ${maxSecretDownloadLimit}`;
        }
      })
      .catch(error => {
        console.error('Error fetching secret settings:', error);
      });
  });


  $("#secret_url").click(function() {
    $("#secret_url_section").toggle();
  });

  $('#create_secret_url')?.on('click', function(event) {
    event.preventDefault();
    const webelement = $('#create_secret_url');
    if (webelement) {
      const url = webelement.attr('url');
      const linkName = $('#link_name').val();
      const expirationDate = $('#expiration_date').val();
      const downloadLimit = $('#download_limit').val();
      const sendEmail = $('#send_email').is(':checked');
      const linkNameError = $('#link_name_error');
      const expirationDateError = $('#expiration_date_error');
      const downloadLimitError = $('#download_limit_error');
  
      let hasError = false;

      // エラーチェック関数
      function checkError(input, errorElement) {
        if (!input) {
          errorElement.css('display', 'block'); // エラーメッセージを表示
          hasError = true;
        } else {
          errorElement.css('display', 'none'); // エラーメッセージを非表示
        }
      }

      // 各項目のエラーチェック
      checkError(linkName, linkNameError);
      checkError(expirationDate, expirationDateError);
      checkError(downloadLimit, downloadLimitError);

      // エラーがある場合は処理を停止
      if (hasError) {
        return;
      }

      $.ajax({
        url: url,
        method: 'POST',
        contentType: 'application/json',
        dataType: 'json',
        data: JSON.stringify({
          link_name: linkName,
          expiration_date: expirationDate,
          download_limit: downloadLimit,
          send_email: sendEmail
        }),
        success: function(response) {
          webelement.prop('disabled', false);
          alert(response.message || "Success!");
        },
        error: function(jqXHR, status, msg) {
          webelement.prop('disabled', false);
          alert("Error: " + (jqXHR.responseJSON?.message || msg));
        }
      });
    }
  });

  $('#print-btn')?.on('click',() => {
    const iframe = document.createElement('iframe');
    iframe.srcdoc = "<!DOCTYPE html>"
    document.body.appendChild(iframe);
    iframe.onload = () => {
      iframe.contentDocument.body.appendChild(document.getElementById('terms').cloneNode(true));
      iframe.contentWindow.print();
    }
  })


$('#close_btn, #modal_close_btn').on('click', function () {
  document.location.href = location.pathname;
  })
$('#mailcheck_download_modal').on('hidden.bs.modal', function () {
  document.location.href = location.pathname;
})
$('#mailaddress_confirm_download').click(function () {
 let mailaddress = document.getElementById('mail_form').value;
 let password_checkflag = document.getElementById("password_checkflag").value;
 var input_password;
 var post_data = {};
 if(password_checkflag == "True"){
  input_password = document.getElementById('input_password').value;
  post_data = {'input_password': input_password};
}
 let input_error = document.getElementById('input_error_messsge').value;
 let url_element = document.getElementById('url_element');
 let onetime_file_url = url_element.dataset.onetime_file_url;
 const get_uri =  onetime_file_url + '&mailaddress='+ mailaddress + '&isajax=true';
 let item_detailes_url = location.pathname;
 if(mailaddress == null || mailaddress == ""){
   alert(input_error);
   document.location.href = onetime_file_url;
 }else{
    $.ajax({
      url: get_uri,
      method: 'POST',
      async: true,
      data: JSON.stringify(post_data),
      contentType: 'application/json',
      success: function (response) {
          let link = document.createElement("a");
          link.download = "";
          if (!!response.guest_token) {
            link.href = get_uri + "&guest-token=" + response.guest_token;
          } else {
            link.href = get_uri;
          }
          link.click();
          $('#mailcheck_download_modal').modal('hide');
          document.location.href = item_detailes_url;
        },
      error: function (error) {
          response_text = error['responseText'];
          alert(response_text);
          $('#mailcheck_download_modal').modal('hide');
          document.location.href = item_detailes_url;
        }
      })
  }
});


document.addEventListener('DOMContentLoaded', function() {
  // 日付をフォーマットする関数
  function formatDate(dateString) {
      // Dateオブジェクトを作成
      const date = new Date(dateString);
      const year = date.getFullYear();
      const month = ('0' + (date.getMonth() + 1)).slice(-2);
      const day = ('0' + date.getDate()).slice(-2);
      return `${year}-${month}-${day}`;
  }

  // .date-format クラスを持つすべての要素を取得
  const dateElements = document.querySelectorAll('.date-format');

  // 各要素の日付をフォーマット
  dateElements.forEach(function(element) {
      const originalDate = element.textContent;
      element.textContent = formatDate(originalDate);
  });
});

// 確認メッセージを取得
const deleteConfirmationMessage = $('#delete-confirmation-message').data('message');
const deleteSuccssesMessage = $('#delete-success-message').data('message');
const copyMassage = $('#copy-message').data('message');

$(document).ready(function() {
  // 共通のAJAXリクエスト関数
  function handleAjaxRequest($button, url, method, successMessage, clipboardText, finalMessage) {
    $button.prop('disabled', true);
    $.ajax({
      url: url,
      method: method,
      contentType: 'application/json',
      dataType: 'json',
      success: function(response) {
        $button.prop('disabled', false);
        if (clipboardText) {
          navigator.clipboard.writeText(response.url)
            .catch(function(err) {
              alert('Could not copy URL: ', err);
            });
        } else {
          location.reload(); // 画面をリロード
        }
        if (finalMessage) {
          alert(finalMessage);
        }
      },
      error: function(jqXHR, status, msg) {
        $button.prop('disabled', false);
        alert("Error: " + (jqXHR.responseJSON?.message || msg));
      }
    });
  }

  // シークレットURLの削除
  $('.delete_secret_url').on('click', function(event) {
    event.preventDefault();
    const $button = $(this);
    const url = $button.attr('url');

    // 確認ポップアップを表示
    if (confirm(deleteConfirmationMessage)) {
      handleAjaxRequest($button, url, 'DELETE', "Success!", false, deleteSuccssesMessage);
    }
  });

  // シークレットURLのコピー
  $('.copy_secret_url').on('click', function(event) {
    event.preventDefault();
    const $button = $(this);
    const url = $button.attr('url');
    handleAjaxRequest($button, url, 'GET', "Success!", true, copyMassage);
  });

  // ワンタイムURLの削除
  $('.delete_onetime_url').on('click', function(event) {
    event.preventDefault();
    const $button = $(this);
    const url = $button.attr('url');

    // 確認ポップアップを表示
    if (confirm(deleteConfirmationMessage)) {
      handleAjaxRequest($button, url, 'DELETE', "Success!", false, deleteSuccssesMessage);
    }
  });

  // ワンタイムURLのコピー
  $('.copy_onetime_url').on('click', function(event) {
    event.preventDefault();
    const $button = $(this);
    const url = $button.attr('url');
    handleAjaxRequest($button, url, 'GET', "Success!", true, copyMassage);
  });
});

