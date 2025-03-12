/**
 * oapolicy.js
 * OAポリシー取得スクリプト
 */

$(document).ready(function () {
  const USE_API = false; // API を有効にする場合は true, Mock を使う場合は false
  const API_URL = "/api/oa_policies"; // バックエンド API のエンドポイント

  /**
   * OAポリシー取得ボタンのクリックイベント
   * @event click
   */
  $(document).on("click", "#oapolicyurl", function () {
    console.log("OAポリシーボタンがクリックされました");

    // ** 取得前に前のデータをリセット **
    resetPolicyInfo();

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
      getOaPolicyApi(issn, eissn, title);
    } else {
      getOaPolicyMock(issn, eissn, title);
    }
  });

  /**
   * 以前の OA ポリシー情報をリセット
   * @function resetPolicyInfo
   */
  function resetPolicyInfo() {
    $("#oaPolicyText").text(""); // URL 表示をクリア
    $("#oaPolicyUrl").attr("href", "").hide(); // リンクを非表示
    $("#oaPolicyError").text("").hide(); // エラーメッセージをクリア
  }

  /**
   * API を使用して OA ポリシー情報を取得
   * @function getOaPolicyApi
   * @param {string} issn - ISSN番号
   * @param {string} eissn - eISSN番号
   * @param {string} title - 雑誌名
   */
  function getOaPolicyApi(issn, eissn, title) {

    console.log(`[API] OAポリシー取得リクエスト送信: ${API_URL}?issn=${issn}&eissn=${eissn}&title=${title}&lang=${lang}`);

    $.ajax({
      url: `${API_URL}?issn=${issn}&eissn=${eissn}&title=${title}&lang=${lang}`,
      type: "GET",
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
        } else if (xhr.status === 404) {
          errorMessage = getErrorMessage("error_api_404");
        } else if (xhr.status === 500) {
          errorMessage = getErrorMessage("error_api_500");
        } else {
          errorMessage = getErrorMessage("error_api_generic");
        }

        showError(errorMessage);
      }
    });
  }

  /**
   * Mock データを使用して OA ポリシー情報を取得（テスト用）
   * @function getOaPolicyMock
   */
  function getOaPolicyMock(issn, eissn, title) {
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

  /**
   * OA ポリシー URL を表示
   * @function showResult
   */
  function showResult(url) {
    console.log("OAポリシー URL 取得成功:", url);
    $("#oaPolicyText").text(url);
    $("#oaPolicyUrl").attr("href", url).show();
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
    let message = errorElement ? errorElement.value : "エラーが発生しました。";

    return message;
  };
});
