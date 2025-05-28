$(document).ready(function () {
  /**
   * 以前の OA ポリシー情報をリセット
   */

  function resetPolicyInfo() {
      $("#oaPolicyText, #oaPolicyError").text("");
      $("#oaPolicyUrl").attr("href", "").addClass("d-none");
  }

  /**
   * エラーメッセージを表示
   * @param {string} errorKey - エラーコードに対応する
   */
  function showError(msgText="") {
      let message = msgText || $("#error_api_generic").val();
      $("#oaPolicyError").text(message).css({
          "display": "inline-block",
          "color": "red",
          "font-weight": "bold",
          "min-width": "200px",
          "margin-left": "10px",
          "vertical-align": "middle"
      });
  }

  /**
   * OAポリシー URL を表示
   * @param {string} url - 取得したポリシーのURL
   */
  function showResult(url) {
      $("#oaPolicyText").text(url);
      $("#oaPolicyUrl").attr("href", url).removeClass("d-none");
      $("#oaPolicyError").text("").css("display", "none");
  }

  /**
   * OAポリシー取得ボタンのクリックイベント
   */
  $(document).on("click", "#oapolicyurl", function () {
      resetPolicyInfo();

      // メタデータ入力ISSN, eISSN, 雑誌名を取得
      let identifierType = $("select[name*='subitem_source_identifier_type']").val()?.trim().replace(/^string:/, "") || "";
      let identifierValue = $("#subitem_source_identifier").val()?.trim() || "";

      let issn = identifierType === "ISSN" ? identifierValue : "";
      let eissn = identifierType === "EISSN" ? identifierValue : "";
      let title = $("#subitem_source_title").val()?.trim() || "";

      // 入力チェック
      if (!issn && !eissn && !title) {
          showError($("#error_missing_input").val());
          return;
      }

      // バックエンドへリクエストを送信
      $.ajax({
        url: "/items/api/oa_policies",
        type: "GET",
        data: { issn: issn, eissn: eissn, title: title },
        dataType: "json"
      }).done(function (data) {
          if (data.policy_url) {
              showResult(data.policy_url);
          } else {
              showError($("#error_no_policy_found").val());
          }
      }).fail(function (xhr) {
        let errMsg = "";
        try {
            const res = JSON.parse(xhr.responseText);
            errMsg = res.error || $("#error_api_generic").val();
        } catch (e) {
            // parse error, fallback to generic message
            errMsg = $("#error_api_generic").val();
        }
        showError(errMsg);
      });
  });
});
