/**
 * oapolicy.js
 * OAポリシー取得スクリプト
 *
 * API から OA ポリシー情報を取得し、結果を表示する
 *
 */
function getApiUrl() {
  return $(".input-group").attr("data-api-url");
}

/**
 * OAポリシー取得ボタンのクリックイベント
 * @event click
 */
$(document).on("click", "#oapolicyurl", function () {
  console.log("OAポリシーボタンがクリックされました");

  // ** 取得前に前のデータをリセット **
  resetPolicyInfo();

  // 識別子タイプの取得
  let identifierTypeElement = $("select[name*='subitem_source_identifier_type']");
  let identifierType = identifierTypeElement.val()?.trim().replace(/^string:/, "") || "";
  let identifierValue = $("#subitem_source_identifier").val()?.trim() || "";

  // ISSN / EISSN の判別
  let issn = identifierType === "ISSN" ? identifierValue : "";
  let eissn = identifierType === "EISSN" ? identifierValue : "";

  // 雑誌名の取得
  let title = $("#subitem_source_title").val()?.trim() || "";

  if (!issn && !eissn && !title) {
    showError("error_missing_input");
    return;
  }

  $("#oaPolicyError").text("").hide();

  getOaPolicy(issn, eissn, title);
});

/**
 * 以前の OA ポリシー情報をリセット
 * @function resetPolicyInfo
 */
function resetPolicyInfo() {
  $("#oaPolicyText, #oaPolicyError").text("");
  $("#oaPolicyUrl").attr("href", "").addClass("d-none");
}

/**
 * OAuth2 トークンを取得し、API リクエスト時に使用
 */
function getAccessToken() {
  return new Promise((resolve, reject) => {
    // `client_secret` を取得
    $.ajax({
      url: "/api/get-client-secret",
      type: "GET",
      dataType: "json",
      success: function (data) {
        if (!data.client_secret || !data.client_id) {
          console.warn("[WARN] クライアントシークレットまたは Client ID が見つかりません");
          reject("Client secret or client_id not found");
          return;
        }

        let client_secret = data.client_secret;
        let client_id = data.client_id;
        console.log("[INFO] Client Secret 取得成功:", client_secret);

        // `/api/oauth/token` へリクエストを送信して `access_token` を取得
        $.ajax({
          url: "/api/oauth/token",
          type: "POST",
          contentType: "application/json",
          data: JSON.stringify({
            grant_type: "client_credentials",
            client_id: client_id,
            client_secret: client_secret
          }),
          dataType: "json",
          success: function (data) {
            console.log("[OAuth2] トークン取得成功:", data.access_token);
            resolve(data.access_token);  // 取得したトークンを返す
          },
          error: function (xhr) {
            console.error("[ERROR] OAuth2 トークン取得エラー:", xhr);
            reject(xhr);
          }
        });
      },
      error: function (xhr) {
        console.error("[ERROR] Client Secret 取得エラー:", xhr);
        reject(xhr);
      }
    });
  });
}
/**
 * API を使用して OA ポリシー情報を取得
 * @function getOaPolicy
 * @param {string} issn - ISSN番号
 * @param {string} eissn - eISSN番号
 * @param {string} title - 雑誌名
 */
function getOaPolicy(issn, eissn, title) {

  let apiUrl = getApiUrl();

  if (!apiUrl) {
    console.error("[ERROR] API URL が取得できません。config.py を確認してください。");
    showError("error_api_generic");
    return;
  }

  getAccessToken()
    .then(token => {
      console.log(`[API] OAポリシー取得リクエスト送信: ${apiUrl}?issn=${issn}&eissn=${eissn}&title=${title}`);

      $.ajax({
        url: `${apiUrl}?issn=${issn}&eissn=${eissn}&title=${title}`,
        type: "GET",
        headers: {
          "Authorization": `Bearer ${token}`  // `client_secret` をトークンとして使用
        },
        dataType: "json",
        success: function (data) {
          if (data.url) {
            console.log(`[API] OAポリシー取得成功: ${data.url}`);
            showResult(data.url);
          } else {
            console.warn("[API] ポリシー情報なし");
            showError("error_no_policy_found");
          }
        },
        error: function (xhr) {
          console.error("[API] リクエストエラー:", xhr);

          let errorMessage;
          if (xhr.responseJSON?.error) {
            errorMessage = xhr.responseJSON.error;
          } else if (xhr.status === 400) {
            errorMessage = getErrorMessage("error_api_400");
          } else if (xhr.status === 401) {
            errorMessage = getErrorMessage("error_api_401");
          } else if (xhr.status === 404) {
            errorMessage = getErrorMessage("error_api_404");
          } else if (xhr.status === 429) {
            errorMessage = getErrorMessage("error_api_429");
          } else if (xhr.status === 500) {
            errorMessage = getErrorMessage("error_api_500");
          }
          showError(errorMessage);
        }
      });
    })
}

/**
 * OA ポリシー URL を表示
 * @function showResult
 */
function showResult(url) {
  console.log("OAポリシー URL 取得成功:", url);
  $("#oaPolicyText").text(url);
  $("#oaPolicyUrl").attr("href", url).removeClass("d-none");
  $("#oaPolicyError").text("");
}

/**
* エラーメッセージを表示
* @function showError
* @param {string} messageId - エラーの識別キー
*/
window.showError = function (messageId) {
  let errorMessage = getErrorMessage(messageId);

  $("#oaPolicyError").text(errorMessage).css({
    "display": "inline-block",
    "color": "red",
    "font-weight": "bold"
  });
};

/**
 * HTML のエラーメッセージを取得
 * @function getErrorMessage
 * @param {string} messageId - エラーの識別キー
 * @returns {string} 翻訳されたエラーメッセージ
 */
window.getErrorMessage = function (messageId) {
  let errorElement = document.getElementById(messageId);
  let message = errorElement ? errorElement.value : "An unknown error occurred";

  return message;
};
