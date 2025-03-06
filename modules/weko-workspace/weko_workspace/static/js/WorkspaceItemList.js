// WorkspaceItemList.js
document.addEventListener('DOMContentLoaded', function () {
  let workspaceItemList = window.workspaceItemList || [];
  const defaultConditions = window.defaultconditions || {};
  const filterContainer = document.getElementById('filter-container');
  const toggleButton = document.getElementById('toggleButton');
  const filterContent = document.getElementById('filter-content');
  const detailSearchBtn = document.getElementById('detail-search-btn');
  const clearSearchBtn = document.getElementById('clear-search-btn');
  const saveSearchBtn = document.getElementById('save-search-btn');
  const resetSearchBtn = document.getElementById('reset-search-btn');
  const saveSuccess = document.getElementById('savaResult-success');
  const saveFail = document.getElementById('savaResult-fail');
  const sortItemSelect = document.getElementById('sort_item');
  const sortOrderSelect = document.getElementById('sort_order');
  const itemsPerPageSelect = document.getElementById('items_per_page');
  const groupYearButton = document.getElementById('groupYearicon');
  const itemListContainer = document.getElementById('itemListContainer');
  const pagination = document.querySelector('.pagination');

  // 必要な要素のチェック
  if (!filterContainer || !toggleButton || !filterContent || !detailSearchBtn || !clearSearchBtn || !saveSearchBtn || !resetSearchBtn || !saveSuccess || !saveFail || !sortItemSelect || !sortOrderSelect || !itemsPerPageSelect || !groupYearButton || !itemListContainer || !pagination) {
    console.error('必要な要素が見つかりません: ', {
      filterContainer: !!filterContainer,
      toggleButton: !!toggleButton,
      filterContent: !!filterContent,
      detailSearchBtn: !!detailSearchBtn,
      clearSearchBtn: !!clearSearchBtn,
      saveSearchBtn: !!saveSearchBtn,
      resetSearchBtn: !!resetSearchBtn,
      saveSuccess: !!saveSuccess,
      saveFail: !!saveFail,
      sortItemSelect: !!sortItemSelect,
      sortOrderSelect: !!sortOrderSelect,
      itemsPerPageSelect: !!itemsPerPageSelect,
      groupYearButton: !!groupYearButton,
      itemListContainer: !!itemListContainer,
      pagination: !!pagination,
    });
    return;
  }

  const filterOrder = [
    'resource_type',
    'peer_review',
    'related_to_paper',
    'related_to_data',
    'funder_name',
    'award_title',
    'file_present',
    'favorite',
  ];

  const singleSelectFilters = [
    'peer_review',
    'related_to_paper',
    'related_to_data',
    'file_present',
    'favorite',
  ];

  const alwaysEmptyFilters = ['funder_name', 'award_title'];

  let currentPage = 1;
  let itemsPerPage = parseInt(itemsPerPageSelect.value) || 20;
  let isGroupedByYear = false;
  let items = [...workspaceItemList]; // 一覧データのコピー

  // SearchBar コンポーネント
  const SearchBar = ({ items, onFilter }) => {
    const [query, setQuery] = React.useState('');
    const [suggestions, setSuggestions] = React.useState([]);
    const [isPopupOpen, setIsPopupOpen] = React.useState(false);
    const [showNoResults, setShowNoResults] = React.useState(false);

    // あいまい検索関数
    const fuzzyMatch = (query, item) => {
      const lowerQuery = query.toLowerCase();
      return (
        (item.title?.toLowerCase() || '').includes(lowerQuery) ||
        (item.magazineName?.toLowerCase() || '').includes(lowerQuery) ||
        (item.conferenceName?.toLowerCase() || '').includes(lowerQuery) ||
        (item.funderName?.toLowerCase() || '').includes(lowerQuery) ||
        (item.awardTitle?.toLowerCase() || '').includes(lowerQuery) ||
        (item.doi?.toLowerCase() || '').includes(lowerQuery)
      );
    };

    // マッチするフィールドを判断する補助関数
    const getMatchedField = (query, item) => {
      const lowerQuery = query.toLowerCase();
      if ((item.title?.toLowerCase() || '').includes(lowerQuery)) return 'title';
      if ((item.magazineName?.toLowerCase() || '').includes(lowerQuery)) return 'magazineName';
      if ((item.conferenceName?.toLowerCase() || '').includes(lowerQuery)) return 'conferenceName';
      if ((item.funderName?.toLowerCase() || '').includes(lowerQuery)) return 'funderName';
      if ((item.awardTitle?.toLowerCase() || '').includes(lowerQuery)) return 'awardTitle';
      if ((item.doi?.toLowerCase() || '').includes(lowerQuery)) return 'doi';
      return 'title'; // デフォルトで title に戻る
    };

    // 入力が変化したときに提案を更新
    const handleInputChange = (e) => {
      const value = e.target.value;
      setQuery(value);
      setShowNoResults(false);

      if (value.trim()) {
        const filtered = workspaceItemList
          .filter(item => fuzzyMatch(value, item))
          .slice(0, 6) // 最大 6 個
          .map(item => ({
            item,
            matchedField: getMatchedField(value, item),
          }));
        setSuggestions(filtered);
        setIsPopupOpen(true);
      } else {
        setSuggestions([]);
        setIsPopupOpen(false);
      }
    };

    // 提案項目をクリックしたときにマッチしたフィールド値を入力
    const handleSuggestionClick = (suggestion) => {
      const { item, matchedField } = suggestion;
      setQuery(item[matchedField]);
      setSuggestions([]);
      setIsPopupOpen(false);
      const filteredItems = workspaceItemList.filter(i => fuzzyMatch(item[matchedField], i));
      setShowNoResults(filteredItems.length === 0);
      onFilter(item[matchedField]);
    };

    // Enter キーを押したときにフィルタリング
    const handleKeyDown = (e) => {
      if (e.key === 'Enter') {
        const filteredItems = workspaceItemList.filter(item => fuzzyMatch(query, item));
        setShowNoResults(filteredItems.length === 0);
        setIsPopupOpen(false);
        onFilter(query);
      }
    };

    return React.createElement(
      'div',
      { style: { position: 'relative', marginBottom: '20px', maxWidth: '300px' } },
      React.createElement('input', {
        type: 'text',
        id: 'search-input',
        style: { marginBottom: '10px', width: '100%', textAlign: 'left' },
        placeholder: '入力後、Enterを押下し検索してください',
        value: query,
        onChange: handleInputChange,
        onKeyDown: handleKeyDown,
      }),
      isPopupOpen && suggestions.length > 0 && React.createElement(
        'div',
        {
          style: {
            position: 'absolute',
            top: '100%',
            left: 0,
            width: '100%',
            backgroundColor: '#fff',
            border: '1px solid #ccc',
            borderRadius: '4px',
            boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
            zIndex: 1000,
            padding: '5px',
            fontSize: '12px', // フォントサイズを調整して 6 個の内容に適応
          },
        },
        suggestions.map(({ item, matchedField }) => React.createElement(
          'div',
          {
            key: item.recid,
            onClick: () => handleSuggestionClick({ item, matchedField }),
            style: {
              padding: '4px 8px', // パディングを減らしてより多くの内容に適応
              cursor: 'pointer',
              borderBottom: '1px solid #eee',
            },
          },
          item[matchedField] // マッチしたフィールドの値を表示
        ))
      ),
      showNoResults && React.createElement(
        'div',
        {
          style: {
            color: 'red',
            marginTop: '5px',
            fontSize: '14px',
            whiteSpace: 'nowrap',
          },
        },
        '検索条件と十分に一致する結果が見つかりません'
      )
    );
  };

  // フィルタコンポーネント
  const FilterItem = ({ filterKey, filter, selectedOptions, onSelectionChange }) => {
    const handleCheckboxChange = (option) => {
      let newSelection;
      if (singleSelectFilters.includes(filterKey)) {
        newSelection = selectedOptions.includes(option) ? [] : [option];
      } else {
        newSelection = selectedOptions.includes(option)
          ? selectedOptions.filter((item) => item !== option)
          : [...selectedOptions, option];
      }
      onSelectionChange(filterKey, newSelection);
    };

    if (filter.options.length === 0 && (filterKey === 'funder_name' || filterKey === 'award_title')) {
      return null;
    }

    const checkboxes = filter.options.map((option) =>
      React.createElement(
        'label',
        { key: option },
        React.createElement('input', {
          type: 'checkbox',
          checked: selectedOptions.includes(option),
          onChange: () => handleCheckboxChange(option),
        }),
        option
      )
    );

    const isExcludedFilter = filterKey === 'funder_name' || filterKey === 'award_title';
    const note = isExcludedFilter
      ? React.createElement(
          'small',
          { style: { color: '#888', fontSize: '12px', display: 'block', marginTop: '5px' } },
          '※この項目はデフォルト条件の保存対象外です'
        )
      : null;

    return React.createElement(
      'tr',
      null,
      React.createElement('th', null, filter.label),
      React.createElement(
        'td',
        null,
        React.createElement('div', { className: 'checkbox-group' }, checkboxes),
        note
      )
    );
  };

  const FilterTable = ({ filters }) => {
    const [selections, setSelections] = React.useState(
      Object.fromEntries(filterOrder.map((key) => [key, filters[key]?.default || []]))
    );

    const selectionsRef = React.useRef(selections);
    React.useEffect(() => {
      selectionsRef.current = selections;
    }, [selections]);

    const handleSelectionChange = (filterKey, newSelection) => {
      setSelections((prev) => ({
        ...prev,
        [filterKey]: newSelection,
      }));
    };

    const clearSelections = () => {
      setSelections(
        Object.fromEntries(filterOrder.map((key) => [key, []]))
      );
    };

    const generateJsonTemplate = () => {
      const currentSelections = selectionsRef.current;
      const result = {};
      for (const key of filterOrder) {
        if (filters[key]) {
          if (singleSelectFilters.includes(key)) {
            const selection = currentSelections[key] || [];
            result[key] = selection.includes('あり') ? true : selection.includes('なし') ? false : null;
          } else if (alwaysEmptyFilters.includes(key)) {
            result[key] = [];
          } else {
            result[key] = currentSelections[key] || [];
          }
        }
      }
      return result;
    };

    const closeFilter = () => {
      filterContent.classList.remove('expanded');
      filterContent.style.display = 'none';
    };

    const refreshPage = async (url, method, body = null) => {
      try {
        const response = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          ...(body && { body: JSON.stringify(body) }),
        });
        if (!response.ok) throw new Error('API呼び出しに失敗しました');
        const html = await response.text();
        document.open();
        document.write(html);
        document.close();
      } catch (error) {
        console.error('ページ更新エラー:', error);
        throw error;
      }
    };

    const fetchJsonResponse = async (url, method, body = null) => {
      try {
        const response = await fetch(url, {
          method,
          headers: { 'Content-Type': 'application/json' },
          ...(body && { body: JSON.stringify(body) }),
        });
        if (!response.ok) throw new Error('API呼び出しに失敗しました');
        return await response.json();
      } catch (error) {
        console.error('JSON取得エラー:', error);
        throw error;
      }
    };

    React.useEffect(() => {
      const handleClear = (e) => {
        e.preventDefault();
        clearSelections();
      };

      const handleFilter = async (e) => {
        e.preventDefault();
        const jsonTemplate = generateJsonTemplate();
        await refreshPage('/workspace/get_workspace_itemlist', 'POST', jsonTemplate);
        closeFilter();
      };

      const handleSave = async (e) => {
        e.preventDefault();
        const jsonTemplate = generateJsonTemplate();
        try {
          const data = await fetchJsonResponse('/workspace/save_filters', 'POST', jsonTemplate);
          alert(data.message || 'デフォルト条件を保存しました。');
          closeFilter();
          await refreshPage('/workspace/get_workspace_itemlist', 'GET');
        } catch (error) {
          alert(error.message || '保存に失敗しました');
          closeFilter();
          await refreshPage('/workspace/get_workspace_itemlist', 'GET');
          console.error('保存エラー:', error);
        }
      };

      const handleReset = async (e) => {
        e.preventDefault();
        if (confirm('フィルタ条件を削除しますか？')) {
          try {
            const data = await fetchJsonResponse('/workspace/reset_filters', 'DELETE');
            alert(data.message || 'デフォルト条件をリセットしました。');
            closeFilter();
            await refreshPage('/workspace/get_workspace_itemlist', 'GET');
          } catch (error) {
            alert(error.message || 'リセットに失敗しました');
            closeFilter();
            await refreshPage('/workspace/get_workspace_itemlist', 'GET');
            console.error('リセットエラー:', error);
          }
        } else {
          console.log('リセットがキャンセルされました');
        }
      };

      clearSearchBtn.addEventListener('click', handleClear);
      detailSearchBtn.addEventListener('click', handleFilter);
      saveSearchBtn.addEventListener('click', handleSave);
      resetSearchBtn.addEventListener('click', handleReset);

      return () => {
        clearSearchBtn.removeEventListener('click', handleClear);
        detailSearchBtn.removeEventListener('click', handleFilter);
        saveSearchBtn.removeEventListener('click', handleSave);
        resetSearchBtn.removeEventListener('click', handleReset);
      };
    }, []);

    const rows = filterOrder
      .filter((key) => filters[key])
      .map((key) =>
        React.createElement(FilterItem, {
          key: key,
          filterKey: key,
          filter: filters[key],
          selectedOptions: selections[key],
          onSelectionChange: handleSelectionChange,
        })
      )
      .filter((row) => row !== null);

    return React.createElement(
      'div',
      { className: 'row row-4' },
      React.createElement(
        'table',
        null,
        React.createElement('tbody', null, rows)
      )
    );
  };

  // お気に入りボタンコンポーネント
  const FavoriteButton = ({ itemRecid, initialFavoriteSts, type }) => {
    const [isFavorite, setIsFavorite] = React.useState(initialFavoriteSts);
    const handleFavoriteToggle = async () => {
      try {
        const response = await fetch('/workspace/updateStatus', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ itemRecid, favoriteSts: !isFavorite, type }),
        });
        if (response.ok) {
          setIsFavorite(!isFavorite);
          const item = items.find((i) => i.recid === itemRecid);
          if (item) item.favoriteSts = !isFavorite;
          updateDisplay();
        }
      } catch (error) {
        console.error('お気に入りステータスの更新に失敗しました:', error);
      }
    };

    return React.createElement(
      'a',
      { href: '#', onClick: (e) => { e.preventDefault(); handleFavoriteToggle(); } },
      isFavorite
        ? React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '20', height: '20', fill: 'currentColor', className: 'bi bi-star-fill', viewBox: '0 0 16 16' },
            React.createElement('path', { d: 'M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z' })
          )
        : React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '20', height: '20', fill: 'currentColor', className: 'bi bi-star', viewBox: '0 0 16 16' },
            React.createElement('path', { d: 'M2.866 14.85c-.078.444.36.791.746.593l4.39-2.256 4.389 2.256c.386.198.824-.149.746-.592l-.83-4.73 3.522-3.356c.33-.314.16-.888-.282-.95l-4.898-.696L8.465.792a.513.513 0 0 0-.927 0L5.354 5.12l-4.898.696c-.441.062-.612.636-.283.95l3.523 3.356-.83 4.73zm4.905-2.767-3.686 1.894.694-3.957a.56.56 0 0 0-.163-.505L1.71 6.745l4.052-.576a.53.53 0 0 0 .393-.288L8 2.223l1.847 3.658a.53.53 0 0 0 .393.288l4.052.575-2.906 2.77a.56.56 0 0 0-.163.506l.694 3.957-3.686-1.894a.5.5 0 0 0-.461 0z' })
          )
    );
  };

  // 閲覧ボタンコンポーネント
  const ReadButton = ({ itemRecid, initialReadSts, type }) => {
    const [isRead, setIsRead] = React.useState(initialReadSts);
    const handleReadToggle = async () => {
      try {
        const response = await fetch('/workspace/updateStatus', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ itemRecid, readSts: !isRead, type }),
        });
        if (response.ok) {
          setIsRead(!isRead);
          const item = items.find((i) => i.recid === itemRecid);
          if (item) item.readSts = !isRead;
          updateDisplay();
        }
      } catch (error) {
        console.error('閲覧ステータスの更新に失敗しました:', error);
      }
    };

    return React.createElement(
      'a',
      { href: '#', onClick: (e) => { e.preventDefault(); handleReadToggle(); } },
      isRead
        ? React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '20', height: '20', fill: 'currentColor', className: 'bi bi-book-fill', viewBox: '0 0 16 16' },
            React.createElement('path', { d: 'M8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783' })
          )
        : React.createElement('svg', { xmlns: 'http://www.w3.org/2000/svg', width: '20', height: '20', fill: 'currentColor', className: 'bi bi-book', viewBox: '0 0 16 16' },
            React.createElement('path', { d: 'M1 2.828c.885-.37 2.154-.769 3.388-.893 1.33-.134 2.458.063 3.112.752v9.746c-.935-.53-2.12-.603-3.213-.493-1.18.12-2.37.461-3.287.811zm7.5-.141c.654-.689 1.782-.886 3.112-.752 1.234.124 2.503.523 3.388.893v9.923c-.918-.35-2.107-.692-3.287-.81-1.094-.111-2.278-.039-3.213.492zM8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783' })
          )
    );
  };

  // ボタンのマウント
  function mountButtons() {
    document.querySelectorAll('.favorite-mount-point').forEach((mountPoint) => {
      const itemRecid = mountPoint.dataset.itemRecid;
      const initialFavoriteSts = JSON.parse(mountPoint.dataset.favoriteSts);
      const type = mountPoint.dataset.type;
      ReactDOM.render(
        React.createElement(FavoriteButton, { itemRecid, initialFavoriteSts, type }),
        mountPoint
      );
    });

    document.querySelectorAll('.read-mount-point').forEach((mountPoint) => {
      const itemRecid = mountPoint.dataset.itemRecid;
      const initialReadSts = JSON.parse(mountPoint.dataset.readSts);
      const type = mountPoint.dataset.type;
      ReactDOM.render(
        React.createElement(ReadButton, { itemRecid, initialReadSts, type }),
        mountPoint
      );
    });
  }

  // 関連ボタンのバインド
  function bindRelatedButtons() {
    const buttons = document.querySelectorAll('.relatedButton');
    buttons.forEach((button) => {
      button.addEventListener('click', function () {
        const content = this.closest('td').querySelector('.relatedInfo');
        if (content) {
          content.style.display = content.style.display === 'block' ? 'none' : 'block';
        }
      });
    });
  }

  // 年ごとのグループ表示
  function renderGroupedByYear(items) {
    itemListContainer.innerHTML = '';
    const groupedItems = {};

    items.forEach((item) => {
      const year = new Date(item.publicationDate).getFullYear();
      if (!groupedItems[year]) groupedItems[year] = [];
      groupedItems[year].push(item);
    });

    const sortedYears = Object.keys(groupedItems).sort((a, b) => b - a);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, sortedYears.length);
    const currentYears = sortedYears.slice(startIndex, endIndex);

    currentYears.forEach((year) => {
      const yearGroup = document.createElement('div');
      yearGroup.className = 'year-group';
      yearGroup.innerHTML = `<h3>${year}</h3>`;
      const table = document.createElement('table');
      table.className = 'table table-striped table-bordered';
      table.style.tableLayout = 'auto';
      const tbody = document.createElement('tbody');
      groupedItems[year].forEach((item) => {
        tbody.innerHTML += generateItemRow(item);
      });
      table.appendChild(tbody);
      yearGroup.appendChild(table);
      itemListContainer.appendChild(yearGroup);
    });

    mountButtons();
    bindRelatedButtons();
  }

  // 通常のテーブル表示
  function renderTable(items) {
    itemListContainer.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'table table-striped table-bordered';
    table.style.tableLayout = 'auto';
    const tbody = document.createElement('tbody');

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, items.length);
    const currentItems = items.slice(startIndex, endIndex);

    currentItems.forEach((item) => {
      tbody.innerHTML += generateItemRow(item);
    });

    table.appendChild(tbody);
    itemListContainer.appendChild(table);
    mountButtons();
    bindRelatedButtons();
  }

  // 単一アイテムのHTML生成
  function generateItemRow(item) {
    const relatedInfoHtml = item.relation && item.relation.length > 0
      ? `<div class="relatedInfo" style="display: none;">${item.relation.map((relatedItem) =>
          `<span>${relatedItem.relationType} ${relatedItem.relationTitle}、<a href="${relatedItem.relationUrl}">${relatedItem.relationUrl}</a></span><br>`
        ).join('')}</div>`
      : '';

    return `
      <tr>
        <td style="text-align: center; vertical-align: top;">
          <div class="favorite-mount-point" data-type="1" data-item-recid="${item.recid}" data-favorite-sts='${JSON.stringify(item.favoriteSts)}'></div><br>
          <div class="read-mount-point" data-type="2" data-item-recid="${item.recid}" data-read-sts='${JSON.stringify(item.readSts)}'></div><br>
          <input type="checkbox" value="" /><br><br>
        </td>
        <td style="width: auto;">
          <strong><a href="/records/${item.recid}">${item.title}</a></strong><br><br>
          ${item.authorlist && item.authorlist.length > 0 ? `<span>${item.authorlist.join(', ')}</span><br><br>` : ''}
          <span>${item.magazineName}／${item.conferenceName}</span><span> </span>
          <span>${item.volume}（${item.issue}）</span><span> </span>
          <span>${item.funderName || ''} | ${item.awardTitle || ''}</span><span> </span><br><br>
          <span>${item.publicationDate}</span><span> </span>
          ${item.relation && item.relation.length > 0 ? '<span><a href="javascript:void(0)" class="relatedButton"><strong>関連</strong></a></span><span> </span>' : ''}
          ${item.fileSts 
            ? `<span>本文ファイル (${item.fileCnt || 0})： 公開（${item.publicCnt || 0}）、エンバーゴ（${item.embargoedCnt || 0}）、 制限公開（${item.restrictedPublicationCnt || 0}）</span>` 
            : '<span>本文ファイル (0)</span>'}<span> </span><br>
          ${relatedInfoHtml}
        </td>
        <td style="text-align: center; vertical-align: top;">
          <span><a href="${item.doi}">DOI</a></span><br><br>
          <span>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-eye-fill" viewBox="0 0 16 16">
              <path d="M10.5 8a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0" />
              <path d="M0 8s3-5.5 8-5.5S16 8 16 8s-3 5.5-8 5.5S0 8 0 8m8 3.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7" />
            </svg>${item.accessCnt}
          </span><br><br>
          <span>
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-file-earmark" viewBox="0 0 16 16">
              <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5z" />
            </svg>${item.downloadCnt}
          </span>
        </td>
        <td style="text-align: center; vertical-align: top;">
          <span style="border: 1px solid #000; padding: 5px; border-radius: '4px'">${item.resourceType}</span><br><br>
          <span>${item.itemStatus}</span><br><br>
          <span>
            ${item.fbEmailSts 
              ? `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-envelope" viewBox="0 0 16 16">
                  <path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2zm2-1a1 1 0 0 0-1 1v.217l7 4.2 7-4.2V4a1 1 0 0 0-1-1zm13 2.383-4.708 2.825L15 11.105zm-.034 6.876-5.64-3.471L8 9.583l-1.326-.795-5.64 3.47A1 1 0 0 0 2 13h12a1 1 0 0 0 .966-.741M1 11.105l4.708-2.897L1 5.383z" />
                </svg>` 
              : `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-envelope-dash" viewBox="0 0 16 16">
                  <path d="M2 2a2 2 0 0 0-2 2v8.01A2 2 0 0 0 2 14h5.5a.5.5 0 0 0 0-1H2a1 1 0 0 1-.966-.741l5.64-3.471L8 9.583l7-4.2V8.5a.5.5 0 0 0 1 0V4a2 2 0 0 0-2-2zm3.708 6.208L1 11.105V5.383zM1 4.217V4a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v.217l-7 4.2z" />
                  <path d="M16 12.5a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0m-5.5 0a.5.5 0 0 0 .5.5h3a.5.5 0 0 0 0-1h-3a.5.5 0 0 0-.5.5" />
                </svg>`}
          </span><br><br>
        </td>
        <td style="text-align: center; vertical-align: top;">
          <a href="javascript:void(0)" class="edit-item" data-item-id="">
            <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" fill="currentColor" class="bi bi-pencil-square" viewBox="0 0 16 16">
              <path d="M15.502 1.94a.5.5 0 0 1 0 .706L14.459 3.69l-2-2L13.502.646a.5.5 0 0 1 .707 0l1.293 1.293zm-1.75 2.456-2-2L4.939 9.21a.5.5 0 0 0-.121.196l-.805 2.414a.25.25 0 0 0 .316.316l2.414-.805a.5.5 0 0 0 .196-.12l6.813-6.814z" />
              <path fill-rule="evenodd" d="M1 13.5A1.5 1.5 0 0 0 2.5 15h11a1.5 1.5 0 0 0 1.5-1.5v-6a.5.5 0 0 0-1 0v6a.5.5 0 0 1-.5.5h-11a.5.5 0 0 1-.5-.5v-11a.5.5 0 0 1 .5-.5H9a.5.5 0 0 0 0-1H2.5A1.5 1.5 0 0 0 1 2.5z" />
            </svg>
          </a>
        </td>
      </tr>
    `;
  }

  // ソート機能
  function sortItems(items, field, order) {
    return items.sort((a, b) => {
      let fieldA, fieldB;
      switch (field) {
        case '1': // 出版年月
          fieldA = new Date(a.publicationDate);
          fieldB = new Date(b.publicationDate);
          break;
        case '2': // タイトル
          fieldA = a.title.toLowerCase();
          fieldB = b.title.toLowerCase();
          break;
        case '3': // アクセス数
          fieldA = a.accessCnt;
          fieldB = b.accessCnt;
          break;
        case '4': // ダウンロード数
          fieldA = a.downloadCnt;
          fieldB = b.downloadCnt;
          break;
        default:
          return 0;
      }
      return order === '1' ? (fieldA > fieldB ? 1 : -1) : (fieldA < fieldB ? 1 : -1);
    });
  }

  // ページングの更新
  function updatePagination(totalCount) {
    const totalPages = Math.ceil(totalCount / itemsPerPage);
    pagination.innerHTML = `
      <li><a href="javascript:void(0)" class="get-pages" data-page="${currentPage - 1}"><</a></li>
    `;
    for (let i = 1; i <= totalPages; i++) {
      pagination.innerHTML += `
        <li><a href="javascript:void(0)" class="get-pages" data-page="${i}" ${i === currentPage ? 'style="background-color: #007bff; color: white;"' : ''}>${i}</a></li>
      `;
    }
    pagination.innerHTML += `
      <li><a href="javascript:void(0)" class="get-pages" data-page="${currentPage + 1}">></a></li>
    `;

    document.querySelectorAll('.get-pages').forEach((link) => {
      link.addEventListener('click', function () {
        const page = parseInt(this.getAttribute('data-page'));
        if (page >= 1 && page <= totalPages) {
          currentPage = page;
          updateDisplay();
        }
      });
    });
  }

  // 表示の更新
  function updateDisplay() {
    const sortedItems = sortItems([...items], sortItemSelect.value, sortOrderSelect.value);
    if (isGroupedByYear) {
      renderGroupedByYear(sortedItems);
      const groupedItems = {};
      sortedItems.forEach((item) => {
        const year = new Date(item.publicationDate).getFullYear();
        if (!groupedItems[year]) groupedItems[year] = [];
        groupedItems[year].push(item);
      });
      updatePagination(Object.keys(groupedItems).length);
    } else {
      renderTable(sortedItems);
      updatePagination(items.length);
    }
  }

  // フィルタ条件をレンダリング
  function renderFilters() {
    ReactDOM.render(
      React.createElement(FilterTable, { filters: defaultConditions }),
      filterContainer
    );
  }

  // トグルボタンの設定
  function setupToggle() {
    toggleButton.addEventListener('click', function (e) {
      e.preventDefault();
      if (filterContent.classList.contains('expanded')) {
        filterContent.classList.remove('expanded');
        filterContent.style.display = 'none';
      } else {
        filterContent.classList.add('expanded');
        filterContent.style.display = 'block';
        if (!filterContainer.hasChildNodes()) {
          renderFilters();
        }
      }
    });
  }

  // イベントリスナー
  sortItemSelect.addEventListener('change', updateDisplay);
  sortOrderSelect.addEventListener('change', updateDisplay);
  itemsPerPageSelect.addEventListener('change', function () {
    if (!this.disabled) {
      itemsPerPage = parseInt(this.value);
      currentPage = 1;
      updateDisplay();
    }
  });

  groupYearButton.addEventListener('click', function () {
    isGroupedByYear = !isGroupedByYear;
    currentPage = 1;
    itemsPerPageSelect.disabled = isGroupedByYear;
    updateDisplay();
  });

  // SearchBar コンポーネントをマウント
  const searchContainer = document.getElementById('search-container');
  if (searchContainer) {
    ReactDOM.render(
      React.createElement(SearchBar, {
        items: workspaceItemList,
        onFilter: (query) => {
          items = query
            ? workspaceItemList.filter(item => {
                const lowerQuery = query.toLowerCase();
                return (
                  (item.title?.toLowerCase() || '').includes(lowerQuery) ||
                  (item.magazineName?.toLowerCase() || '').includes(lowerQuery) ||
                  (item.conferenceName?.toLowerCase() || '').includes(lowerQuery) ||
                  (item.funderName?.toLowerCase() || '').includes(lowerQuery) ||
                  (item.awardTitle?.toLowerCase() || '').includes(lowerQuery) ||
                  (item.doi?.toLowerCase() || '').includes(lowerQuery)
                );
              })
            : [...workspaceItemList];
          currentPage = 1;
          updateDisplay();
        },
      }),
      searchContainer
    );
  } else {
    console.error('search-container が見つかりません');
  }

  // 初期表示
  if (workspaceItemList.length > 0 || Object.keys(defaultConditions).length > 0) {
    console.log('初期化開始: データがロードされました', { workspaceItemList, defaultConditions });
    updateDisplay();
    setupToggle();
  } else {
    console.warn('初期データが空です');
    mountButtons();
    bindRelatedButtons();
    setupToggle();
  }
});