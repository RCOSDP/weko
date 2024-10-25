const { useState, useEffect } = React;

// ドキュメントの読み込みが完了したら実行される関数
$(function() {
  const initDataElement = document.getElementById("init_data");

  // 必要な要素が見つからない場合のエラーハンドリング
  if (!initDataElement) {
    console.error("Required elements not found in the DOM.");
    return;
  }

  // 初期データの取得とコンソールへの出力
  const initValue = initDataElement.value;

  // Reactコンポーネントのレンダリング
  ReactDOM.render(
    <ProfilesList profileItemList ={JSON.parse(initValue)} />,
    document.getElementById('root')
  );
});

function ProfileItem({ profileFieldKey, profileFieldValue, onLabelChange, onCheckboxChange, onTypeChange, onSelectChange }) {
  const {label_name, format, visible, options, ...rest} = profileFieldValue;
  const format_options = JSON.parse(document.getElementById("format_options").value);

  let optionsDisplay = "";
  if (format === "select") {
    optionsDisplay = (!profileFieldValue.options ? [] : profileFieldValue.options).join('|');
  }

  return (
    <div key={profileFieldKey} className="item-group">
      <h3>{profileFieldKey}</h3>
      <div>
        <input type="text" value={label_name}
          onChange={(e) => onLabelChange(e.target.value)} />
        <select value={format}
          onChange={(e) => onTypeChange(e.target.value)}>
            {format_options.map((typeOption, index) => (
              <option key={index} value={typeOption}>{typeOption}</option>
            ))}
        </select>
        <label>
          <input
            type="checkbox"
            checked={visible}
            onChange={(e) => onCheckboxChange(e.target.checked)}
          />
          Display
        </label>
      </div>
      {format === "select" && (
        <input
          type="text"
          className="select-textbox"
          value={optionsDisplay}
          onChange={(e) => onSelectChange(e.target.value)}
          placeholder="separate option with the | character"
        />
      )}
    </div>
  );
}

// ProfilesListコンポーネントの定義
function ProfilesList({ profileItemList }) {
  const [profileSettings , setProfileSettings] = useState(profileItemList);

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
      '<div class="' + className + '">' + closeButton + message + '</div>'
    );
  }

  // ラベル名の変更ハンドラー
  const handleLabelNameChange = (fieldKey, newValue) => {
    const newProfiles = {...profileSettings};
    newProfiles[fieldKey].label_name = newValue;
    setProfileSettings(newProfiles);
  };

  // 表示設定の変更ハンドラー
  const handleVisibleChange = (fieldKey, newValue) => {
    const newProfiles = {...profileSettings};
    newProfiles[fieldKey].visible = newValue;
    setProfileSettings(newProfiles);
  };

  // 入力方法の変更ハンドラー
  const handleFormatChange = (fieldKey, newValue) => {
    const newProfiles = {...profileSettings};
    newProfiles[fieldKey].format = newValue;
    setProfileSettings(newProfiles);
  };

  // オプションの変更ハンドラー
  const handleOptionsChange = (fieldKey, newValue) => {
    const newProfiles = {...profileSettings};
    newProfiles[fieldKey].options = newValue.split('|').map(option => option.trim());
    setProfileSettings(newProfiles);
  };

  // 表示する項目の順序を指定する配列
  const sortedProfileSettings = Object.keys(profileSettings).map(key => ({ key: key, value: profileSettings[key] })).sort((a, b) => (a.value.order - b.value.order));

  // 保存ボタンのクリックハンドラー
  const handleSave = () => {
    const URL = "/api/admin/profile_settings/save";

    // エラーチェック
    if (Object.keys(profileSettings).some((key) => {
      const item = profileSettings[key];
      return !item.label_name || (item.format === "select" && (!item.options || !item.options.every(option => option)));
    })) {
      addAlert('Failed to update settings.', 1);
      return;
    }

    let data = {
      profiles_templates: profileSettings
    };

    // AJAXリクエストを送信
    $.ajax({
      url: URL,
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data)
    }).done((result) => {
      if (result.status==="success") {
        addAlert(result.msg, 2);
      } else {
        addAlert(result.msg, 1);
      }
      if (result.data) {
        setProfileSettings (result.data);
      }
    }).fail((jqXHR, textStatus, errorThrown) => {
        addAlert('Profile Settings Update Failed.', 1);
    });
  };

  return (
    // プロファイル設定の表示
    <div className="container">
      <div id="alertContainer"></div> {/* アラートメッセージを表示するためのコンテナ */}
      {sortedProfileSettings.map((profileFieldSetting) => {
        if (!profileFieldSetting.key || !profileFieldSetting.value) return null;
        return <ProfileItem
          profileFieldKey={profileFieldSetting.key}
          profileFieldValue={profileFieldSetting.value}
          onLabelChange={(newValue) => handleLabelNameChange(profileFieldSetting.key, newValue)}
          onCheckboxChange={(newValue) => handleVisibleChange(profileFieldSetting.key, newValue)}
          onTypeChange={(newValue) => handleFormatChange(profileFieldSetting.key, newValue)}
          onSelectChange={(newValue) => handleOptionsChange(profileFieldSetting.key, newValue)}
        />
      })}
      <button onClick={handleSave} className="btn btn-primary">
        <span className="glyphicon glyphicon-save" aria-hidden="true">SAVE</span>
      </button> {/* 保存ボタンにアイコンを追加 */}
    </div>
  );
}
