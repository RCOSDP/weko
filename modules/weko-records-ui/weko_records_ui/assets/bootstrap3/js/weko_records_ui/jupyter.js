// ページ読み込み時のチェックボックス初期化(戻る対策))
window.addEventListener('DOMContentLoaded', function () {
  var $checkbox = $('input[type="checkbox"]');
  $checkbox.removeAttr('checked').prop('checked', false).change();
});

$(document).ready(function(){
  // ページ読み込み完了時にリンク先の頭だけ取得しておく
  var link_text = $('#jupyter_multiple').attr('href');

  $('.file-check').click(function() {
    var check_filelist = '';
    var jupyter_link = '';
    // チェック状態のボタンの値を全て取得
    $('#file_checkbox:checked').each(function() {
      var filechack_val = $(this).val();
      // ファイルリストのカンマ区切り文字列を生成
      if (check_filelist === '') {
        check_filelist += filechack_val ;
      } else {
        check_filelist += "," + filechack_val ;
      }
    })
    // Jupyterボタンの活性制御
    if (check_filelist != '') {
      $('#jupyter_multiple').removeClass('disabled');
    } else {
      $('#jupyter_multiple').addClass('disabled');
    }
    // 連結したファイル名をhrefに追加
    var jupyter_link = link_text + check_filelist;
    $('#jupyter_multiple').attr('href', jupyter_link);
  });

  // ファイル全選択ボタン
  $('#all_file_checkbox').click(function() {
    var all_checked = $('#all_file_checkbox').prop("checked");
    if (all_checked) {
      $('.file-check').each(function() {
        $(this).prop('checked', true).change();
      })
      $('#jupyter_multiple').removeClass('disabled');
    }
    else {
      $('.file-check').each(function() {
        $(this).prop('checked', false).change();
      })
      $('#jupyter_multiple').addClass('disabled');
    }
  });
})