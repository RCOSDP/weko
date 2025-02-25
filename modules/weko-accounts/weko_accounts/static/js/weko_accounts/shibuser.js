document.addEventListener("DOMContentLoaded", index);

function index() {
  // 各設定欄を生成
  createDefaultRoleSettingArea();
  createAttrMapSettingArea();
  createBlockUserSettingArea();
}

// デフォルトロール設定欄を生成
function createDefaultRoleSettingArea() {
  const defaultRoleList = document
    .getElementById("default-role-list")
    .getAttribute("data-value1");
  const setLanguage = document
    .getElementById("default-role-list")
    .getAttribute("data-value2");

  const gakuninRoleList = document.getElementById("gakunin-role-list");
  const gakuninRoleValue = gakuninRoleList.getAttribute("data-value");
  gakuninRoleList.appendChild(
    createSelectList(
      0,
      "role-lists",
      gakuninRoleValue,
      defaultRoleList,
      setLanguage
    )
  );

  const orthrosRoleList = document.getElementById("orthros-role-list");
  const orthrosRoleValue = orthrosRoleList.getAttribute("data-value");
  orthrosRoleList.appendChild(
    createSelectList(
      1,
      "role-lists",
      orthrosRoleValue,
      defaultRoleList,
      setLanguage
    )
  );

  const othersRoleList = document.getElementById("others-role-list");
  const othersRoleValue = othersRoleList.getAttribute("data-value");
  othersRoleList.appendChild(
    createSelectList(
      2,
      "role-lists",
      othersRoleValue,
      defaultRoleList,
      setLanguage
    )
  );
}

// 属性マッピング設定欄を生成
function createAttrMapSettingArea() {
  const attrList = document
    .getElementById("attr-list")
    .getAttribute("data-value");

  const eppnAttrList = document.getElementById("eppn-attr-list");
  const eppnAttrValue = eppnAttrList.getAttribute("data-value");
  eppnAttrList.appendChild(
    createSelectList(0, "attr-lists", eppnAttrValue, attrList)
  );

  const roleAuthorityAttrList = document.getElementById(
    "role-authority-attr-list"
  );
  const roleAuthorityAttrValue =
    roleAuthorityAttrList.getAttribute("data-value");
  roleAuthorityAttrList.appendChild(
    createSelectList(1, "attr-lists", roleAuthorityAttrValue, attrList)
  );

  const mailAttrList = document.getElementById("mail-attr-list");
  const mailAttrValue = mailAttrList.getAttribute("data-value");
  mailAttrList.appendChild(
    createSelectList(2, "attr-lists", mailAttrValue, attrList)
  );

  const userAttrList = document.getElementById("user-attr-list");
  const userAttrValue = userAttrList.getAttribute("data-value");
  userAttrList.appendChild(
    createSelectList(3, "attr-lists", userAttrValue, attrList)
  );
}

// ブロックユーザー設定欄を生成
function createBlockUserSettingArea() {
  const blockEPPNList = document
    .getElementById("block-user-list")
    .getAttribute("data-value");

  const userePPNList = document.getElementById("block-user-list");
  const userePPNValue = userePPNList.getAttribute("data-value");
  const ePPNList = createSelectList(
    "",
    "block-user-lists",
    userePPNValue,
    blockEPPNList
  );
  userePPNList.appendChild(ePPNList);
  const deleteButton = document.getElementById("btn_delete_block_eppn");
  userePPNList.insertBefore(ePPNList, deleteButton);
  updateBlockUserList();
}

// select要素を生成
function createSelectList(id, kinds, value, defaultList, setLanguage = null) {
  const select = document.createElement("select");
  select.id = kinds + `${id}`;
  select.name = kinds + `${id}`;
  const selectLists = JSON.parse(defaultList.replace(/'/g, '"'));

  if (kinds === "block-user-lists") {
    select.style.width = "75%";
    select.size = "5";
    select.multiple = "multiple";
  } else {
    select.style.width = "60%";
  }

  selectLists.forEach((sel) => {
    const option = document.createElement("option");
    option.value = sel;

    if (sel === value) {
      option.selected = true;
    }
    if (kinds === "role-lists" && sel === "None" && setLanguage === "ja") {
      sel = "(ロール無)";
    }
    option.text = sel;
    select.appendChild(option);
  });
  return select;
}

// ブロックユーザー一覧を更新
function updateBlockUserList() {
  let blockUserEPPNList = [];
  const selectBox = document.getElementById("block-user-lists");
  const optionValues = Array.from(selectBox.options).map(
    (option) => option.value
  );
  blockUserEPPNList = optionValues;
  document.getElementById("block-eppn-option-list").value =
    JSON.stringify(blockUserEPPNList);
}
