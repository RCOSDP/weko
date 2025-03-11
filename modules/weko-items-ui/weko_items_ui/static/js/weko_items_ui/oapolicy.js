$(document).ready(function () {
  const USE_API = false; // API を有効にする場合は true, Mock を使う場合は false
  const API_URL = "/api/oa_policies";
  /*保留
  // OAuth2 認証用URL
  const TOKEN_URL = "http://127.0.0.1:5000/oauth/token";
  const CLIENT_ID = "your_client_id"; // クライアントID
  const CLIENT_SECRET = "your_client_secret"; // クライアントシークレット
  */

  $(document).on("click", "#oapolicyurl", function () {

    let issn = $("#subitem_source_identifier").val()?.trim() || "";
    let eissn = $("#subitem_source_identifier").val()?.trim() || "";
    let title = $("#subitem_source_title").val()?.trim() || "";

    console.log("取得したパラメータ:", { issn, eissn, title });

    if (!issn && !eissn && !title) {
      showError("error_missing_input");
      return;
    }

    $("#oaPolicyError").text("").hide();

    if (USE_API) {
      get_oa_policy_api(issn, eissn, title);
    } else {
      get_oa_policy_mock(issn, eissn, title);
    }
  });

  // **API を使用して OA ポリシー情報を取得**
  function get_oa_policy_api(issn, eissn, title) {
    console.log("[API] OAポリシー取得開始:", { issn, eissn, title });

    getAccessToken().then(token => {
      $.ajax({
        url: API_URL,
        type: "GET",
        headers: {
          "Authorization": "Bearer " + token
        },
        data: { issn, eissn, title },
        dataType: "json",
        success: function (data) {
          if (data.url) {
            console.log("[API] OAポリシー取得成功:", data.url);
            showResult(data.url);
          } else {
            showError("error_no_policy_found");
          }
        },
        error: function (xhr) {
          console.error("[API] エラー:", xhr);
          let errorMessageId = "error_api_generic";
          if (xhr.status === 400) errorMessageId = "error_api_400";
          else if (xhr.status === 404) errorMessageId = "error_api_404";
          else if (xhr.status === 500) errorMessageId = "error_api_500";

          showError(errorMessageId);
        }
      });
    }).catch(error => {
      console.error("[OAuth2] トークン取得エラー:", error);
      showError("error_api_auth");
    });
  }

  /*保留
  // **OAuth2 のアクセストークンを取得**
  function getAccessToken() {
    return new Promise((resolve, reject) => {
      $.ajax({
        url: TOKEN_URL,
        type: "POST",
        data: {
          grant_type: "client_credentials",
          client_id: CLIENT_ID,
          client_secret: CLIENT_SECRET
        },
        dataType: "json",
        success: function (data) {
          resolve(data.access_token);
        },
        error: function (xhr) {
          reject(xhr);
        }
      });
    });
  }
  */

  // ** Mock (テスト用)**
  function get_oa_policy_mock(issn, eissn, title) {
    console.log("[MOCK] OAポリシー取得開始:", { issn, eissn, title });

    setTimeout(function () {
      if (issn === "12345678" || eissn === "23456789" || title.includes("Journal")) {
        console.log("[MOCK] OAポリシー取得成功！");
        showResult("https://www.springer.com/gp/open-access/publication-policies/copyright-transfer");
      } else {
        console.error("[MOCK] 一致するポリシー情報が見つかりませんでした。");
        showError("error_no_policy_found");
      }
    }, 1000);
  }

  function showResult(url) {
    console.log("OAポリシー URL 取得成功:", url);
    $("#oaPolicyText").text(url);
    $("#oaPolicyUrl").attr("href", url).show();
    $("#oaPolicyError").text("");
  }

  function showError(messageId) {
    let translatedMessage = gettext(messageId);
    console.warn("🔹 エラー:", translatedMessage);

    $("#oaPolicyText").text("");
    $("#oaPolicyUrl").attr("href", "").hide();

    $("#oaPolicyError").text(translatedMessage).css({
      "display": "inline-block",
      "color": "red",
      "font-weight": "bold",
      "min-width": "200px",
      "margin-left": "10px",
      "vertical-align": "middle"
    });
  }
});
