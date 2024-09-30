const { useState, useEffect } = React;

// ドキュメントの読み込みが完了したら実行される関数
$(function() {
  const initDataElement = document.getElementById("init_data");

  // 必要な要素が見つからない場合のエラーハンドリング
  if (!initDataElement) {
    console.error("Required elements not found in the DOM.");
    return;
  }

  // 空の項目テンプレート
  const EMPTY_TERM = {
    key: "",
    flag: false,
    content: {
      "item": '',   // 項目名
      "visible": '',    // 表示設定
      "label_name": '',  // ラベル名
      "select": '',     // 入力方法
      "option": ''      // オプション
    }
  };

  // 初期データの取得とコンソールへの出力
  const initValue = initDataElement.value;

  // Reactコンポーネントのレンダリング
  ReactDOM.render(
    <ProfilesList termList={JSON.parse(initValue)} />,
    document.getElementById('root')
  );
});

// ProfilesListコンポーネントの定義
function ProfilesList({ termList }) {
  const [terms, setTerms] = useState(termList);

  // メッセージを表示する関数の定義
  function addAlert(message, type) {
    let className = "alert alert-success alert-dismissible alert-profile-settings";
    let closeButton = '<button type="button" class="close" data-dismiss="alert">&times;</button>';
    if (type === 1) {
      className = "alert alert-danger alert-dismissible alert-profile-settings";
    }
    if (type === 2) {
      className = "alert alert-info alert-dismissible alert-profile-settings";
    }
    $('#alertContainer').append(
      '<div class="' + className + '">'
      + closeButton + message + '</div>'
    );
  }

  // ラベル名の変更ハンドラー
  const handleLabelChange = (itemKey, newValue) => {
    setTerms(prevTerms => ({
      ...prevTerms,
      [itemKey]: {
        ...prevTerms[itemKey],
        label_name: newValue
      }
    }));
  };

  // 表示設定の変更ハンドラー
  const handleCheckboxChange = (itemKey, newValue) => {
    setTerms(prevTerms => ({
      ...prevTerms,
      [itemKey]: {
        ...prevTerms[itemKey],
        visible: newValue
      }
    }));
  };

  // 入力方法の変更ハンドラー
  const handleTypeChange = (itemKey, newValue) => {
    setTerms(prevTerms => ({
      ...prevTerms,
      [itemKey]: {
        ...prevTerms[itemKey],
        current_type: newValue
      }
    }));
  };

  // オプションの変更ハンドラー
  const handleSelectChange = (itemKey, newValue) => {
    setTerms(prevTerms => ({
      ...prevTerms,
      [itemKey]: {
        ...prevTerms[itemKey],
        select: newValue.split(',').map(option => option.trim())
      }
    }));
  };

  // プロファイル設定をグループ化する関数
  const groupedTemplates = groupProfileSettings(terms);

  function groupProfileSettings(templates) {
    const grouped = {};
    Object.keys(templates).forEach(key => {
      const itemValue = templates[key];
      if (!grouped[key]) {
        grouped[key] = {
          type: itemValue["type"], // 入力方法の設定
          select: itemValue["select"], // 選択肢の設定
          visible: itemValue["visible"],  // 表示設定
          label_name: itemValue["label_name"], // ラベル名の設定
          current_type: itemValue["current_type"], // 入力方法の初期値を設定
          items: []
        };
      }
    });
    return grouped;
  }

  // 表示する項目の順序を指定する配列
  const order = ["fullname", "university", "department", "position", ...Array.from({ length: 16 }, (_, i) => `item${i + 1}`)];

  // 保存ボタンのクリックハンドラー
  const handleSave = () => {
    const URL = "/api/admin/profile_settings/save";

    // エラーチェック
    for (let itemKey of order) {
      const item = terms[itemKey];
      if (!item) continue; // 項目が存在しない場合はスキップ

      // label_nameが空の場合エラー
      if (!item.label_name || (item.current_type === "select" && (!item.select || !item.select.every(option => option)))) {
        addAlert('Failed to update settings.', 1);
        return;
      }
    }
      

    let data = {
      profiles_templates: terms
    };

    // AJAXリクエストを送信
    $.ajax({
      url: URL,
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function (result) {
        console.log("AJAXリクエスト成功:", result);
        if (result.status==="success") {
          addAlert(result.msg, 2);
        } else {
          addAlert(result.msg, 1);
        }
        if (result.data) {
          setTerms(result.data);
        }
      },
      error: function (error) {
        console.log("AJAXリクエストエラー:", error);
        addAlert('Profile Settings Update Failed.', 1);
      }
    });
  };

  return (
    <div className="container">
      <div id="alertContainer"></div> {/* アラートメッセージを表示するためのコンテナ */}
      {order.map(itemKey => {
        const item = terms[itemKey];
        if (!item) return null; // 項目が存在しない場合はスキップ
        return (
          <div key={itemKey} className="item-group">
            <h3>{itemKey}</h3>
            <div>
              <input
                type="text"
                value={item.label_name}
                onChange={(e) => handleLabelChange(itemKey, e.target.value)}
              />
              <select
                value={item.current_type}
                onChange={(e) => handleTypeChange(itemKey, e.target.value)}
              >
                {item.type.map((typeOption, index) => (
                  <option key={index} value={typeOption}>{typeOption}</option>
                ))}
              </select>
              <label>
                <input
                  type="checkbox"
                  checked={item.visible}
                  onChange={(e) => handleCheckboxChange(itemKey, e.target.checked)} // チェックボックスの設定
                />
                表示
              </label>
            </div>
            {item.current_type === "select" && (
              <input
                type="text"
                className="select-textbox"
                value={item.select.join(', ')}
                onChange={(e) => handleSelectChange(itemKey, e.target.value)}
                placeholder="separate option with the | character" // placeholder属性を追加
              />
            )}
          </div>
        );
      })}
      <button onClick={handleSave} className="btn btn-primary">
        <span className="glyphicon glyphicon-save" aria-hidden="true"></span> 保存
      </button> {/* 保存ボタンにアイコンを追加 */}
    </div>
  );
}
