// ページ読み込み時のチェックボックス初期化(戻る対策))
window.addEventListener('DOMContentLoaded', function () {
  var checkbox = $('input[type="checkbox"]');
  checkbox.prop('checked', false).change();
});

$(document).ready(function () {
  // ページ読み込み完了時にリンク先の頭だけ取得しておく
  var link_text = $('#jupyter_multiple').attr('href');

  $('.file-check').change(function () {
    var check_filelist = '';
    var jupyter_link = '';
    // チェック状態のボタンの値を全て取得
    $('.file-check:checked').each(function () {
      var filechack_val = $(this).val();
      // ファイルリストのカンマ区切り文字列を生成
      if (check_filelist === '') {
        check_filelist += filechack_val;
      } else {
        check_filelist += "," + filechack_val;
      }
    })
    // 全てのファイルがチェック済みならヘッダのチェックボックスをONにする
    var not_check_exitst = $(".file-check:not(:checked)").size();
    if (!not_check_exitst) {
      $('#all_file_checkbox').prop('checked', true).change();
    } else {
      $('#all_file_checkbox').prop('checked', false).change();
    }
    // 選択したファイルが一つでもあればJupyterボタンの活性制御
    if (check_filelist != '') {
      $('#jupyter_multiple').removeClass('disabled');
    } else {
      $('#jupyter_multiple').addClass('disabled');
    }
    // 連結したファイル名をhrefに追加
    var jupyter_link = link_text + check_filelist;
    $('#jupyter_multiple').attr('href', jupyter_link);
  });

  // ヘッダーでファイル全選択
  $('.checkbox-th, .checkbox-th input[type=checkbox]').click(function () {
    var all_checked = $('#all_file_checkbox').prop("checked");
    if (!all_checked) {
      $('#all_file_checkbox').prop('checked', true).change();
      $('.file-check').each(function () {
        $(this).prop('checked', true).change();
      })
      $('#jupyter_multiple').removeClass('disabled');
    } else {
      $('#all_file_checkbox').prop('checked', false).change();
      $('.file-check').each(function () {
        $(this).prop('checked', false).change();
      })
      $('#jupyter_multiple').addClass('disabled');
    }
    // チェックボックス自体のイベントは伝播させない
    // $('.checkbox-th input[type=checkbox]').on('click', function(e){
    //   e.stopPropagation();
    // });
  });

  // ファイル名の領域をクリックした時チェックON
  $('.filecheck-td, .filename-td').click(function () {
    var checkbox = $(this).parent('tr').find('.file-check');
    if (!checkbox.prop('checked')) {
      checkbox.prop('checked', true).change();
    } else {
      checkbox.prop('checked', false).change();
    }
    // チェックボックス自体のイベントは伝播させない
    $('.filecheck-td input[type=checkbox]').on('click', function (e) {
      e.stopPropagation();
    });
  });

  // ファイルごとのプレビューボタンを押した時、プレビュー領域ON
  $('.preview-button').click(function () {
    var parentPanel = $('.panel');
    if (parentPanel.find('.preview-panel-body').hasClass('hidden')) {
      $(this).find('.preview-arrow-right').addClass('hidden');
      parentPanel.find('.preview-panel-body').removeClass('hidden');
      $(this).find('.preview-arrow-down').removeClass('hidden');
    }
  });

  function showMessage(message) {
    $("#inputModal").html(message);
    $("#allModal").modal("show");
  }

  $('.non-role-btn').click(function () {
    let errorMessage = $('#non-role-msg').val()
    showMessage(errorMessage);
  });



  function validateUserEmail(email, confirmEmail) {
      let regex = /^([a-zA-Z0-9_.+-])+@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;
      return (email && confirmEmail && email === confirmEmail && regex.test(email))
    }

  function validatePassword(password, confirmPassword){
    let password_checkflag = document.getElementById("password_checkflag").value;
    let regex = /^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[@!#\$%&=\-\+\*\/\.,:;\[\]\|])[a-zA-Z0-9@!#\$%&=\-\+\*\/\.,:;\[\]\|]{8,}$/;
    if (password_checkflag == "True"){
      return (password && confirmPassword && password === confirmPassword && regex.test(password))
    }else{
      return true;
    }
  }

  $('#confirm_email_btn').click(function () {
    let userMailElement = $('#user_mail');
    let userMailConfirmElement = $('#user_mail_confirm');
    let user_mail = userMailElement.val();
    let user_mail_confirm = userMailConfirmElement.val();
    let passwordElement = $('#password_for_download');
    let passwordConfirmElement = $('#password_for_download_confirm');
    let password_checkflag = document.getElementById("password_checkflag").value;
    var password_check = true;
    if(password_checkflag == "True"){
      var password_for_download = passwordElement.val();
      var password_for_download_confirm = passwordConfirmElement.val();
      password_check = validatePassword(password_for_download, password_for_download_confirm);
    }
    if (validateUserEmail(user_mail, user_mail_confirm) && password_check) {
      let fileName = $(this).data("guest_filename_data");
      let dataType = $(this).data("guest_data_type_title");
      let recordID = $(this).data("guest_record_id");
      let itemTypeId = $(this).data("guest_itemtype_id");
      let workflowId = $(this).data("guest_workflow_id");
      let flowId = $(this).data("guest_flow_id");

      const post_uri = '/workflow/activity/init-guest';
      let post_data = {
        guest_mail: user_mail,
        password_for_download: password_for_download,
        file_name: fileName,
        guest_item_title: dataType,
        record_id: recordID.toString(),
        item_type_id: itemTypeId.toString(),
        workflow_id: workflowId.toString(),
        flow_id: flowId.toString(),
      }
      $.ajax({
        url: post_uri,
        method: 'POST',
        async: true,
        contentType: 'application/json',
        data: JSON.stringify(post_data),
        success: function (res) {
          userMailElement.val('');
          userMailConfirmElement.val('');
          passwordElement.val('');
          passwordConfirmElement.val('');
          $('#email_modal').modal('hide');
          if(1 === res.code && res.data.is_download){
            const url = new URL(res.data.redirect, document.location.origin);
            url.searchParams.append('terms_of_use_only',true);
            document.location.href = url;
            return;
          }
          $("#modalSendEmailSuccess #inputModal").html(res.msg);
          $("#modalSendEmailSuccess").modal("show");
        },
        error: function (jqXHE, status) {
        }
      });
    }
  });

  $('#user_mail, #user_mail_confirm').on('input', function () {
    let user_mail = $('#user_mail').val();
    let user_mail_confirm = $('#user_mail_confirm').val();
    if (validateUserEmail(user_mail, user_mail_confirm)) {
      $('.user-mail').removeClass('has-error');
      let password_check = true;
      let password_checkflag = document.getElementById("password_checkflag").value;
      if (password_checkflag == "True"){
        let password_for_download = $('#password_for_download').val();
        let password_for_download_confirm = $('#password_for_download_confirm').val();
        password_check = validatePassword(password_for_download, password_for_download_confirm);
      }
      if (password_check){
        $("#confirm_email_btn").removeAttr("disabled");
      }
    } else {
      $("#confirm_email_btn").attr("disabled", true);
      $('.user-mail').addClass('has-error');
    }
  });

  $('#password_for_download, #password_for_download_confirm').on('input', function () {
    let user_mail = $('#user_mail').val();
    let user_mail_confirm = $('#user_mail_confirm').val();
    let password_for_download = $('#password_for_download').val();
    let password_for_download_confirm = $('#password_for_download_confirm').val();
    if (validatePassword(password_for_download, password_for_download_confirm)) {
      $('.password').removeClass('has-error');
      if (validateUserEmail(user_mail, user_mail_confirm)){
        $("#confirm_email_btn").removeAttr("disabled");
      }
    } else {
      $("#confirm_email_btn").attr("disabled", true);
      $('.password').addClass('has-error');
    }
  });
});
