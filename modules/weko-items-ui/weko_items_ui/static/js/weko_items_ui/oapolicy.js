document.addEventListener("DOMContentLoaded", function () {
  // ボタンクリック時に get_oa_policy を実行
  document.getElementById("oapolicyurl").addEventListener("click", function () {
      get_oa_policy('1234-5678', '8765-4321', 'Sample Journal');
  });
});

/**
* APIを呼び出して OA ポリシーのURLを取得
* @param {string} issn - ISSN
* @param {string} eissn - eISSN
* @param {string} title - 雑誌名
*/
function get_oa_policy(issn, eissn, title) {
  console.log("OAポリシー取得開始:", issn, eissn, title);

  if (!issn && !eissn && !title) {
      showError("ISSN、eISSN、または雑誌名を入力してください。");
      return;
  }

  var apiUrl = "/api/oa_policies?";
  var params = [];

  if (issn) params.push('issn=' + encodeURIComponent(issn));
  if (eissn) params.push('eissn=' + encodeURIComponent(eissn));
  if (title) params.push('title=' + encodeURIComponent(title));

  var fullUrl = apiUrl + params.join('&');
  console.log("API へリクエスト送信:", fullUrl);

  // API 呼び出し
  fetch(fullUrl)
      .then(response => {
          if (!response.ok) {
              if (response.status === 400) {
                  throw new Error("パラメータが不正です。");
              } else if (response.status === 404) {
                  throw new Error("一致するポリシー情報が見つかりませんでした。");
              } else if (response.status === 500) {
                  throw new Error("サーバー内部のエラーが発生しました。");
              } else {
                  throw new Error("エラーが発生しました。");
              }
          }
          return response.json();
      })
      .then(data => {
          if (data.oa_url) {
              showResult(data.oa_url);
          } else {
              showError("一致するポリシー情報が見つかりませんでした。");
          }
      })
      .catch(error => {
          console.error("OAポリシー API エラー:", error);
          showError(error.message);
      });
}

/**
* 結果を表示する関数
*/
function showResult(url) {
  var policyText = document.getElementById("oaPolicyText");
  var policyUrl = document.getElementById("oaPolicyUrl");
  var policyError = document.getElementById("oaPolicyError");

  policyText.textContent = url;
  policyUrl.href = url;
  policyUrl.style.display = "inline";
  policyError.textContent = "";
}

/**
* エラーメッセージを表示する関数
*/
function showError(message) {
  var policyText = document.getElementById("oaPolicyText");
  var policyUrl = document.getElementById("oaPolicyUrl");
  var policyError = document.getElementById("oaPolicyError");

  policyText.textContent = "";
  policyUrl.style.display = "none";
  policyError.textContent = message;
}
