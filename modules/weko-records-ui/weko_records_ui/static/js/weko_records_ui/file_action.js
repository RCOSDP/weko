// ページ読み込み時のチェックボックス初期化(戻る対策))
window.addEventListener('DOMContentLoaded', function () {
  var checkbox = $('input[type="checkbox"]');
  checkbox.prop('checked', false).change();
});

$(document).ready(function(){
  // ページ読み込み完了時にリンク先の頭だけ取得しておく
  var link_text = $('#jupyter_multiple').attr('href');

  $('.file-check').change(function() {
    var check_filelist = '';
    var jupyter_link = '';
    // チェック状態のボタンの値を全て取得
    $('.file-check:checked').each(function() {
      var filechack_val = $(this).val();
      // ファイルリストのカンマ区切り文字列を生成
      if (check_filelist === '') {
        check_filelist += filechack_val ;
      } else {
        check_filelist += "," + filechack_val ;
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
  $('.checkbox-th, .checkbox-th input[type=checkbox]').click(function() {
    var all_checked = $('#all_file_checkbox').prop("checked");
    if (!all_checked) {;
      $('#all_file_checkbox').prop('checked', true).change();
      $('.file-check').each(function() {
        $(this).prop('checked', true).change();
      })
      $('#jupyter_multiple').removeClass('disabled');
    }
    else {
      $('#all_file_checkbox').prop('checked', false).change();
      $('.file-check').each(function() {
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
  $('.filecheck-td, .filename-td').click(function() {
    var checkbox = $(this).parent('tr').find('.file-check');
    if (!checkbox.prop('checked')){
      checkbox.prop('checked', true).change();
    } else {
      checkbox.prop('checked', false).change();
    }
    // チェックボックス自体のイベントは伝播させない
    $('.filecheck-td input[type=checkbox]').on('click', function(e){
      e.stopPropagation();
    });
  });

  // ファイルごとのプレビューボタンを押した時、プレビュー領域ON
  $('.preview-button').click(function() {
    var parentPanel = $('.panel');
    if(parentPanel.find('.preview-panel-body').hasClass('hidden')) {
      $(this).find('.preview-arrow-right').addClass('hidden');
      parentPanel.find('.preview-panel-body').removeClass('hidden');
      $(this).find('.preview-arrow-down').removeClass('hidden');
    }
  });
});