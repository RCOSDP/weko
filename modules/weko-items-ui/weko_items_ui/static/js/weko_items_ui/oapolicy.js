/**
 * oapolicy.js
 * OAポリシー取得スクリプト
 *
 * API から OA ポリシー情報を取得し、結果を表示する
 */

$(document).ready(function () {
  let accessToken = null;  // トークンを保存

  /**
   * API URL を取得
   * @returns {string} APIのURL
   */
  function getApiUrl() {
      return $(".input-group").attr("data-api-url");
  }
  /**
   * 以前の OA ポリシー情報をリセット
   */
  function resetPolicyInfo() {
      $("#oaPolicyText, #oaPolicyError").text("");
      $("#oaPolicyUrl").attr("href", "").addClass("d-none");
  }

  /**
   * トークン取得
   * @returns {Promise} アクセストークンの Promise
   */
  function getAccessToken() {
      if (accessToken) {
          console.log("[OAuth2] キャッシュされたトークンを使用:", accessToken);
          return $.Deferred().resolve(accessToken).promise();
      }
      console.log("[OAuth2] トークン取得開始: /items/oauth/token");
      return $.ajax({
        url: "/api/oauth/token",
          type: "POST",
          contentType: "application/json",
          dataType: "json"
      }).done(function (data) {
          accessToken = data.access_token;
          console.log("[OAuth2] 新しいトークン取得成功:", accessToken);
      }).fail(function (xhr) {
          console.error("[ERROR] OAuth2 トークン取得エラー:", xhr);
      });
  }

  /**
   * API を使用して OA ポリシー情報を取得
   * @param {string} issn - ISSN番号
   * @param {string} eissn - eISSN番号
   * @param {string} title - 雑誌名
   */
  function getOaPolicy(issn, eissn, title) {
      let apiUrl = getApiUrl();
      if (!apiUrl) {
          console.error("[ERROR] API URL が取得できません。config.py を確認してください。");
          showError("error_api_generic");
      }

      getAccessToken().done(function (new_access_token) {
          if (!new_access_token) {
              showError("No Token");
              return;
          }

          console.log(`[API] OAポリシー取得リクエスト送信: ${apiUrl}?issn=${issn}&eissn=${eissn}&title=${title}`);

          $.ajax({
              url: apiUrl,
              type: "GET",
              headers: {
                  "Authorization": `Bearer ${new_access_token}`
              },
              data: { issn: issn, eissn: eissn, title: title },
              dataType: "json"
          }).done(function (data) {
              if (data.url) {
                  console.log("[API] OAポリシー取得成功:", data.url);
                  showResult(data.url);
              } else {
                  console.warn("[API] ポリシー情報なし");
                  showError("error_no_policy_found");
              }
          }).fail(function (xhr) {
              console.error("[API] リクエストエラー:", xhr);
              showError("APIリクエストに失敗しました");
          });
      }).fail(function () {
          showError("トークン取得に失敗しました");
      });
  }

  /**
   * OA ポリシー URL を表示
   * @param {string} url - 取得したポリシーのURL
   */
  function showResult(url) {
      console.log("OAポリシー URL 取得成功:", url);
      $("#oaPolicyText").text(url);
      $("#oaPolicyUrl").attr("href", url).removeClass("d-none");
      $("#oaPolicyError").text("");
  }

  /**
   * エラーメッセージを表示
   * @param {string} message - 表示するエラーメッセージ
   */
  function showError(message) {
      $("#oaPolicyError").text(message).css({
          "display": "inline-block",
          "color": "red",
          "font-weight": "bold"
      });
  }

  /**
   * OAポリシー取得ボタンのクリックイベント
   */
  $(document).on("click", "#oapolicyurl", function () {
      console.log("OAポリシーボタンがクリックされました");
      resetPolicyInfo();

      // 識別子タイプの取得
      let identifierType = $("select[name*='subitem_source_identifier_type']").val()?.trim().replace(/^string:/, "") || "";
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

  // **初回読み込み時にトークンを取得**
  getAccessToken().done(function () {
      console.log("初回トークン取得完了");
  }).fail(function () {
      showError("トークン取得に失敗しました。");
  });
});
