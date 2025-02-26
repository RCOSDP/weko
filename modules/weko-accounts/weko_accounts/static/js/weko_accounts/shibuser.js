$(document).ready(function () {
  // 各設定欄を生成
  const setLanguage = $("#shib_form").data("value");
  createDefaultRoleSettingArea(setLanguage);
  createAttrMapSettingArea(null);
  createBlockUserSettingArea(null);
});

/**
 * 既定のロール設定欄を生成
 * @param {string} setLanguage 言語設定 ja|en
 */
function createDefaultRoleSettingArea(setLanguage) {
  const defaultRoleList = $("#default-role-list").data("value");

  const roleElements = [
    { id: "#gakunin-role-list", index: 0 },
    { id: "#orthros-role-list", index: 1 },
    { id: "#extra-role-list", index: 2 },
  ];

  roleElements.forEach((roleElement) => {
    const roleList = $(roleElement.id);
    const roleValue = roleList.data("value");
    roleList.append(
      createSelectList(
        roleElement.index,
        "role-lists",
        roleValue,
        defaultRoleList,
        setLanguage
      )
    );
  });
}

/**
 * 属性マッピング設定欄を生成
 */
function createAttrMapSettingArea() {
  const attrList = $("#attr-list").data("value");

  const attrElements = [
    { id: "#eppn-attr-list", index: 0 },
    { id: "#role-authority-attr-list", index: 1 },
    { id: "#mail-attr-list", index: 2 },
    { id: "#user-attr-list", index: 3 },
  ];

  attrElements.forEach((attrElement) => {
    const attrListElement = $(attrElement.id);
    const attrValue = attrListElement.data("value");
    attrListElement.append(
      createSelectList(attrElement.index, "attr-lists", attrValue, attrList)
    );
  });
}

/**
 * ブロックユーザー設定欄を生成
 */
function createBlockUserSettingArea() {
  const userePPNList = $("#block-user-list");
  const blockEPPNList = userePPNList.data("value");
  const ePPNList = createSelectList(
    "",
    "block-user-lists",
    blockEPPNList,
    blockEPPNList
  );
  const deleteButton = $("#btn_delete_block_eppn");
  userePPNList.append(ePPNList);
  userePPNList.append(deleteButton);
  updateBlockUserList();
}

/**
 * select要素を生成
 * @param {number} id インデックス
 * @param {string} kinds リストの種類
 * @param {string} value 選択中の値
 * @param {Array} defaultList 選択肢作成に使用するデフォルトリスト
 * @param {string} setLanguage 言語設定 ja|en
 * @returns
 */
function createSelectList(id, kinds, value, defaultList, setLanguage = null) {
  const select = $("<select>", {
    id: `${kinds}${id}`,
    name: `${kinds}${id}`,
    css: { width: kinds === "block-user-lists" ? "75%" : "60%" },
  });

  if (kinds === "block-user-lists") {
    select.attr("size", 5);
    select.attr("multiple", true);
  }

  const selectLists = JSON.parse(defaultList.replace(/'/g, '"'));

  selectLists.forEach((sel) => {
    const optionText =
      kinds === "role-lists" && sel === "None" && setLanguage === "ja"
        ? "(ロール無)"
        : sel;
    select.append(
      $("<option>", {
        value: sel,
        text: optionText,
        selected: sel === value,
      })
    );
  });
  return select;
}

/**
 * ブロックユーザー一覧を更新
 */
function updateBlockUserList() {
  let blockUserEPPNList = [];
  const selectBox = $("#block-user-lists");
  const optionValues = selectBox
    .find("option")
    .map((_, option) => option.value)
    .get();
  blockUserEPPNList.push(...optionValues);
  $("#block-eppn-option-list").val(JSON.stringify(blockUserEPPNList));
}
