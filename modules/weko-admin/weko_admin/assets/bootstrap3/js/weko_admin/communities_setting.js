import $ from 'jquery';
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('settings_form');  // フォームを取得
    const iconInput = document.getElementById('icon');  // アイコン入力フィールドのIDを取得
    const titleInput = document.getElementById('title');  // タイトル入力フィールドのIDを取得
    const iconDrawButton = document.getElementById('icon-draw-button');
    const iconPreview = document.getElementById('icon_preview');  // アイコンプレビューを表示する要素を取得
    const iconWarningDiv = document.getElementById('icon_warning');  // アイコンエラーメッセージ要素を取得
    const titleWarningDiv = document.getElementById('community_title_warning');  // タイトルエラーメッセージ要素を取得
  
    // FontAwesome のアイコンクラスが有効かどうかを確認する関数
    function isValidFontAwesomeIcon(iconClass) {
      const testElement = document.createElement('i');
      testElement.className = `${iconClass}`;
      testElement.style.position = 'absolute'; // 画面外に配置
      testElement.style.left = '-9999px'; // 画面外に配置
      testElement.style.fontSize = '24px'; // サイズを設定して確実にアイコンが表示されるようにする
      document.body.appendChild(testElement);
  
      // アイコンのスタイルを取得
      const computedStyle = window.getComputedStyle(testElement);
      const fontFamily = computedStyle.getPropertyValue('font-family');
      const content = computedStyle.getPropertyValue('content');
  
      // テスト用要素を削除
      document.body.removeChild(testElement);
  
      // FontAwesome アイコンの確認
      const isValidFontAwesome = (fontFamily.includes('Font Awesome') || fontFamily.includes('FontAwesome'));
  
      if (!isValidFontAwesome || content === 'none' || content === '') {
        // アイコンが有効でないか、content が 'none' または '' の場合は処理を中止
        return false;
      }
  
      // アイコンが有効で、content が適切な場合は true を返す
      return true;
    }
  
    if (form && iconInput && iconPreview && iconWarningDiv && titleWarningDiv) {
  
      form.addEventListener('submit', function (event) {
        // ボタンが押されたときの処理
        const submitter = event.submitter;
        if (submitter && submitter.id === 'icon-save-button') {
          const iconClass = iconInput.value.trim();
          const titleValue = titleInput.value.trim(); // タイトルフィールドの値を取得
  
          let hasError = false;  // エラーフラグ
  
          // タイトルが未入力の場合
          if (!titleValue) {
            titleWarningDiv.classList.remove('hide');  // タイトルエラーメッセージを表示
            titleInput.focus();  // タイトル入力フィールドにフォーカス
            hasError = true;  // エラーフラグを立てる
          } else {
            titleWarningDiv.classList.add('hide');  // タイトルエラーメッセージを隠す
          }
  
          // アイコンが入力されていた場合
          if (iconClass) {
            if (isValidFontAwesomeIcon(iconClass)) {
              iconWarningDiv.classList.add('hide');  // アイコンエラーメッセージを隠す
            } else {
              event.preventDefault();  // フォームの送信をキャンセル
              iconPreview.innerHTML = '';  // アイコンが無効な場合、プレビューを消す
              iconWarningDiv.classList.remove('hide');  // アイコンエラーメッセージを表示
              iconInput.focus();  // アイコン入力フィールドにフォーカス
              hasError = true;  // エラーフラグを立てる
            }
          }
  
          if (hasError) {
            event.preventDefault();  // フォームの送信をキャンセル
          }
        }
      });
  
      // アイコン入力フィールドの値が変更されたときにプレビューを更新
      iconDrawButton.addEventListener('click', function (event) {
        const iconClass = iconInput.value.trim();
        if (iconClass && isValidFontAwesomeIcon(iconClass)) {
          iconWarningDiv.classList.add('hide');  // アイコンエラーメッセージを隠す
          iconPreview.innerHTML = `<i class="${iconClass}"></i>`;  // 有効なアイコンが指定された場合、プレビューに表示
        } else {
          iconPreview.innerHTML = '';  // アイコンが無効な場合、プレビューを消す
          iconWarningDiv.classList.remove('hide');  // アイコンエラーメッセージを表示
          iconInput.focus();  // アイコン入力フィールドにフォーカス
        }
      });
    } else {
      console.error('フォーム、入力フィールド、またはアイコンプレビュー要素が見つかりません');
    }
  });
  
  $(document).ready(function () {
    // 初期状態で container-ja を非表示
    $('#container-ja').hide();

    // 初期状態のチェック
    toggleButton();

    // タイトル追加ボタンがクリックされたときの処理
    $('#title-add-btn').click(function (event) {
        event.preventDefault(); // デフォルトの動作をキャンセル
        $('#container-ja').show(); // #container-ja を表示
        toggleButton(); // ボタンの状態を更新
    });

    // 削除ボタンがクリックされたら input-container_ja を非表示にし、ボタンの状態を更新
    $('#delete-ja').click(function (event) {
        event.preventDefault(); // デフォルトの動作をキャンセル
        $('#container-ja').hide(); // 非表示にする
        toggleButton(); // ボタンの状態を更新
    });

    // input-container_ja の表示状態に基づいてボタンの活性/非活性を切り替える関数
    function toggleButton() {
        if ($('#container-ja').is(':visible')) {
            $('#title-add-btn').prop('disabled', true);  // 非活性にする
        } else {
            $('#title-add-btn').prop('disabled', false);  // 活性にする
        }
    }
});