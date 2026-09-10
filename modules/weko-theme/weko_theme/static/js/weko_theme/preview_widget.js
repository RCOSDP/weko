/**
 * プレビュー機能の要件に基づき、情報取得元をサーバからローカルストレージへ意図的に変更（オーバーライド）
 * Get Widget design setting.
 */
function getWidgetDesignSetting() {
  setTimeout(() => {
    // If the current page is a widget page get
    const widgetListLocal = localStorage.getItem("widget_setting_data");
    const widgetListLocalJson = JSON.parse(widgetListLocal);
    widgetList = widgetListLocalJson["widget-settings"];
    if (Array.isArray(widgetList) && widgetList.length) {
      $("#page_body").removeClass("hidden");
      $("#" + MAIN_CONTENTS).addClass("grid-stack-item");
      $("#header").addClass("grid-stack-item no-scroll-bar");
      $("#footer").addClass("grid-stack-item no-scroll-bar");
      // Check browser/tab is active
      if (!document.hidden) {
        buildWidget();
      } else {
        // In case browser/tab is inactive,
        // create an event build widget when browser/tab active
        window.addEventListener("focus", buildWidget);
      }
    } else {
      // Pages are able to not have main content, so hide if widget is not present
      if (community_id !== DEFAULT_REPOSITORY) {
        $("#community_header").removeAttr("hidden");
        $("footer > #community_footer").removeAttr("hidden");
        $("#page_body").removeClass("hidden");
      }
    }

    if (!document.hidden) {
      toggleWidgetUI();
    } else {
      window.addEventListener("focus", toggleWidgetUI);
    }
  }, 0)
}
