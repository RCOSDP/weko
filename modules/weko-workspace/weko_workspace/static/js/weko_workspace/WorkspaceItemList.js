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
  const placeholder = document.getElementById('placeholder').value;
  const showNoResultsMsg = document.getElementById('showNoResultsMsg').value;
  const remindMsg = document.getElementById('remindMsg').value;
  const confirmDeleteMsg = document.getElementById('confirmDeleteMsg').value;
  const relation = document.getElementById('relation').value;
  const documentfile = document.getElementById('documentfile').value;
  const published = document.getElementById('published').value;
  const embargo = document.getElementById('embargo').value;
  const restricted = document.getElementById('restricted').value;

  // 必要な要素のチェック
  if (!filterContainer || !toggleButton || !filterContent || !detailSearchBtn || !clearSearchBtn || !saveSearchBtn || !resetSearchBtn || !saveSuccess || !saveFail || !sortItemSelect || !sortOrderSelect || !itemsPerPageSelect || !groupYearButton || !itemListContainer || !pagination) {
    console.error('The required element was not found: ', {
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
      placeholder: !!placeholder,
      showNoResultsMsg: !!showNoResultsMsg,
      remindMsg: !!remindMsg,
      confirmDeleteMsg: !!confirmDeleteMsg,
      relation: !!relation,
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
  let items = workspaceItemList.slice(0); // 一覧データのコピー

  // // 選択状態を保持するためのオブジェクト
  let checkedItems = new Set();
  // すべてチェックの処理
  function handleCheckAll() {
    const itemCheckboxes = document.querySelectorAll('tbody input[type="checkbox"]');
    itemCheckboxes.forEach(checkbox => {
      checkbox.checked = document.getElementById('check_all').checked;
      const tr = checkbox.closest('tr');
      const anchor = tr && tr.querySelector('td:nth-child(2) strong a');
      const recid = anchor ? anchor.href.split('/').pop() : null;
      if (recid) {
        if (document.getElementById('check_all').checked) {
          checkedItems.add(recid);
        } else {
          checkedItems.delete(recid);
        }
      }
    });
  }



  // 個別チェックボックスの処理
  function handleItemCheckboxChange() {
    // const recid = this.closest('tr')?.querySelector('td:nth-child(2) strong a')?.href.split('/').pop();
    const tr = checkbox.closest('tr');
    const anchor = tr && tr.querySelector('td:nth-child(2) strong a');
    const recid = anchor ? anchor.href.split('/').pop() : null;

    if (recid) {
      if (this.checked) {
        checkedItems.add(recid);
      } else {
        checkedItems.delete(recid);
      }
    }
    updateCheckAllStatus();
  }

  // すべてチェックボックスの状態を更新
  function updateCheckAllStatus() {
    const itemCheckboxes = document.querySelectorAll('tbody input[type="checkbox"]');
    document.getElementById('check_all').checked = itemCheckboxes.length > 0 && [...itemCheckboxes].every(cb => cb.checked);
  }

  // ページ変更時にチェックボックスの状態を復元
  function restoreCheckedItems() {
    const itemCheckboxes = document.querySelectorAll('tbody input[type="checkbox"]');
    itemCheckboxes.forEach(checkbox => {
      //const recid = checkbox.closest('tr')?.querySelector('td:nth-child(2) strong a')?.href.split('/').pop();
      const tr = checkbox.closest('tr');
      const anchor = tr && tr.querySelector('td:nth-child(2) strong a');
      const recid = anchor ? anchor.href.split('/').pop() : null;
      if (recid && checkedItems.has(recid)) {
        checkbox.checked = true;
      }
      checkbox.addEventListener('change', handleItemCheckboxChange);
    });
    updateCheckAllStatus();
  }
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
        ((item.title ? item.title.toLowerCase() : '') || '').includes(lowerQuery) ||
        ((item.magazineName ? item.magazineName.toLowerCase() : '') || '').includes(lowerQuery) ||
        ((item.conferenceName ? item.conferenceName.toLowerCase() : '') || '').includes(lowerQuery) ||
        ((item.funderName ? item.funderName.toLowerCase() : '') || '').includes(lowerQuery) ||
        ((item.awardTitle ? item.awardTitle.toLowerCase() : '') || '').includes(lowerQuery) ||
        ((item.doi ? item.doi.toLowerCase() : '') || '').includes(lowerQuery)
      );
    };


    // マッチするフィールドを判断する補助関数
    const getMatchedField = (query, item) => {
      const lowerQuery = query.toLowerCase();
      if (((item.title ? item.title.toLowerCase() : '') || '').includes(lowerQuery)) return 'title';
      if (((item.magazineName ? item.magazineName.toLowerCase() : '') || '').includes(lowerQuery)) return 'magazineName';
      if (((item.conferenceName ? item.conferenceName.toLowerCase() : '') || '').includes(lowerQuery)) return 'conferenceName';
      if (((item.funderName ? item.funderName.toLowerCase() : '') || '').includes(lowerQuery)) return 'funderName';
      if (((item.awardTitle ? item.awardTitle.toLowerCase() : '') || '').includes(lowerQuery)) return 'awardTitle';
      if (((item.doi ? item.doi.toLowerCase() : '') || '').includes(lowerQuery)) return 'doi';
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
          .map(item => ({
            item,
            matchedField: getMatchedField(value, item),
          }))
          .sort((a, b) => a.item.title.localeCompare(b.item.title));
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
      { style: { position: 'relative', marginTop: '10px', marginBottom: '10px', marginLeft: '5px', maxWidth: '300px' } },
      React.createElement('input', {
        type: 'text',
        id: 'search-input',
        style: { marginBottom: '10px', width: '100%', textAlign: 'left' },
        placeholder: placeholder,
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
            fontSize: '12px',
            overflowY: 'scroll',
            maxHeight: '162px', 
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
        showNoResultsMsg
      )
    );
  };

  // フィルタコンポーネント
  function FilterItem(props) {
    var filterKey = props.filterKey;
    var filter = props.filter;
    var selectedOptions = props.selectedOptions;
    var onSelectionChange = props.onSelectionChange;

    function handleCheckboxChange(option) {
      var newSelection;
      if (singleSelectFilters.includes(filterKey)) {
        newSelection = selectedOptions.includes(option) ? [] : [option];
      } else {
        newSelection = selectedOptions.includes(option)
          ? selectedOptions.filter(function(item) { return item !== option; })
          : selectedOptions.slice(0).concat([option]);
      }
      onSelectionChange(filterKey, newSelection);
    }

    if (filter.options.length === 0 && (filterKey === 'funder_name' || filterKey === 'award_title')) {
      return null;
    }
    
    const [hoveredOption, setHoveredOption] = React.useState(null);
    var checkboxes = filter.options.map(function(option) {
      const ctx = document.createElement('canvas').getContext('2d');
      ctx.font = window.getComputedStyle(document.body).font;
      let text_length = '';
      for (let i = 0; i < option.length; i++) {
        const next = text_length + option[i];
        if (ctx.measureText(next).width >= 140) {
          break;
        }
        text_length = next;
      }

      const long_text = text_length + '...'
      hover= hoveredOption === option;
      const text =
      ctx.measureText(option).width >= 140 &&(filterKey === 'funder_name' || filterKey === 'award_title')
        ? (hover ? option : long_text)
        : option 
      
      window.addEventListener('scroll', () => {
        setHoveredOption();
     });
     
      if(document.querySelectorAll('.checkbox-group-exclude')!=null){ 
          document.querySelectorAll('.checkbox-group-exclude').forEach(el => {
            el.addEventListener('scroll', () => {
              setHoveredOption();
          });
        });
      }
      
      return React.createElement(
        'label',
        { key: option},
        React.createElement('input', {
          type: 'checkbox',
          checked: selectedOptions.includes(option),
          onChange: function() { handleCheckboxChange(option); },
        }),
        React.createElement(
        'span',{id: `e-${option}`,onMouseEnter: function(e) { if(ctx.measureText(option).width >= 140 &&(filterKey === 'funder_name' || filterKey === 'award_title'))
            { 
              let place = e.target.getBoundingClientRect();
              el=document.getElementById('tooltip-'+e.target.id.replace("e-",""))
              el.style.top = (place.top -20) + 'px'; 
              el.style.left = place.left + 'px';
              setHoveredOption(option);
            }
            else
            {setHoveredOption();}
          }, 
          onMouseLeave: function() { setHoveredOption(); }},
        ctx.measureText(option).width >= 140 &&(filterKey === 'funder_name' || filterKey === 'award_title') ? long_text : option
      ),React.createElement(
        'span',
        { id: `tooltip-${option}`,style: hover? {display: 'block',backgroundColor: 'white', border: '1px solid #0f0e0eff',padding: '0px',position: 'fixed'} : {display: 'none'} },
        text
      ),
      );
    });

    var isExcludedFilter = filterKey === 'funder_name' || filterKey === 'award_title';
    var note = isExcludedFilter
      ? React.createElement(
          'small',
          { style: { color: '#888', fontSize: '12px', display: 'block', marginTop: '5px' } },
          remindMsg
        )
      : null;
    
    function getfilterclassName(){
      if(singleSelectFilters.includes(filterKey)) {
      return 'checkbox-group-single';
      }else if(filterKey === 'funder_name' || filterKey === 'award_title'){
        return 'checkbox-group-exclude';
      }else{
        return '';
      }
  }
    return React.createElement(
      'tr', {style: { position: 'relative' }},
      null,
      React.createElement('th', { style: { width: '30%' } }, filter.label),
      React.createElement(
        'td',
        null,
        React.createElement('div', { className: `checkbox-group ${getfilterclassName()}`}, checkboxes),
        note
      )
    );
  }


  const FilterTable = ({ filters }) => {
    const [selections, setSelections] = React.useState(
      Object.fromEntries(filterOrder.map((key) => [key, (filters[key] ? filters[key].default : undefined) || []]))
    );

    const selectionsRef = React.useRef(selections);
    React.useEffect(() => {
      selectionsRef.current = selections;
    }, [selections]);

    const handleSelectionChange = (filterKey, newSelection) => {
      setSelections(function(prev) {
        return Object.assign({}, prev, { [filterKey]: newSelection });
      });
    };

    const clearSelections = () => {
      setSelections(
        Object.fromEntries(filterOrder.map((key) => [key, []]))
      );
    };

    const generateJsonTemplate = (is_save=false) => {
      const currentSelections = selectionsRef.current;
      const result = {};
      for (const key of filterOrder) {
        if (filters[key]) {
          if (singleSelectFilters.includes(key)) {
            const selection = currentSelections[key] || [];
            result[key] = selection.includes('Yes') ? true : selection.includes('No') ? false : null;
          } else if (is_save && alwaysEmptyFilters.includes(key)) {
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

    function refreshPage(url, method, body) {
      body = typeof body !== 'undefined' ? body : null;
      return fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined
      })
        .then(function(response) {
          if (!response.ok) {
            throw new Error('Failed to call the API.');
          }
          return response.text();
        })
        .then(function(html) {
          document.open();
          document.write(html);
          document.close();
        })
        .catch(function(error) {
          console.error('Update page error:', error);
          throw error;
        });
    }

    function fetchJsonResponse(url, method, body) {
      body = typeof body !== 'undefined' ? body : null;

      return fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: body ? JSON.stringify(body) : undefined
      })
        .then(function(response) {
          if (!response.ok) {
            throw new Error('Failed to call the API.');
          }
          return response.json();
        })
        .then(function(data) {
          return data;
        })
        .catch(function(error) {
          console.error('Get json error:', error);
          throw error;
        });
    }

    React.useEffect(() => {
      const handleClear = (e) => {
        e.preventDefault();
        clearSelections();
      };

      const handleFilter = async (e) => {
        e.preventDefault();
        const jsonTemplate = generateJsonTemplate();
        await refreshPage('/workspace/', 'POST', jsonTemplate);
        closeFilter();
      };

      const handleSave = async (e) => {
        e.preventDefault();
        const jsonTemplate = generateJsonTemplate(true);
        try {
          const data = await fetchJsonResponse('/workspace/save_filters', 'POST', jsonTemplate);
          alert(data.message);
          closeFilter();
          await refreshPage('/workspace/', 'GET');
        } catch (error) {
          alert(error.message);
          closeFilter();
          await refreshPage('/workspace', 'GET');
          console.error('Save error:', error);
        }
      };

      const handleReset = async (e) => {
        e.preventDefault();
        if (confirm(confirmDeleteMsg)) {
          try {
            const data = await fetchJsonResponse('/workspace/reset_filters', 'DELETE');
            alert(data.message);
            closeFilter();
            await refreshPage('/workspace/', 'GET');
          } catch (error) {
            alert(error.message);
            closeFilter();
            await refreshPage('/workspace', 'GET');
            console.error('Reset error:', error);
          }
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
      React.useEffect(() => {
      if(document.querySelectorAll('.checkbox-group-exclude')!=null){
          document.querySelectorAll('.checkbox-group-exclude').forEach((el) => {
             const height = window.getComputedStyle(el).getPropertyValue('height');
             if(parseFloat(height) >135){
                el.style.overflowY = 'scroll';
                el.style.height = '135px';
             }
          });
      }
      }, []);
    return React.createElement(
      'div',
      { className: 'row row-4', style: { overflow: 'visible' } },
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
        console.error('Failed to update favorite status:', error);
      }
    };

    return React.createElement(
      'a',
      { href: '#', onClick: (e) => { e.preventDefault(); handleFavoriteToggle(); } },
      React.createElement('i', {
        className: isFavorite ? 'bi bi-star-fill' : 'bi bi-star',
        style: { fontSize: '20px' }
      })
    );
  };

  
const handleReadToggle = async (itemRecid, isRead, type, setIsRead) => {
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
    console.error('Failed to update viewing status:', error);
  }
};

const ReadButton = ({ itemRecid, initialReadSts, type }) => {
  const [isRead, setIsRead] = React.useState(initialReadSts);

 return React.createElement(
      'a',
      { href: '#', onClick: (e) => { e.preventDefault(); handleReadToggle(itemRecid, isRead, type, setIsRead); } },
      React.createElement('i', {
        className: isRead ? 'bi bi-book-fill' : 'bi bi-book',
        style: { fontSize: '20px' }
      })
    );
  };
  
const Unread = ({ itemRecid, initialReadSts, type }) => {
    const [isRead2, setIsRead2] = React.useState(initialReadSts);
    const text = $('#unread').text();

  return React.createElement(
      'span',
      { onClick: (e) => { e.preventDefault(); handleReadToggle(itemRecid, isRead2, type, setIsRead2);},className: isRead2 ? 'unread_hide' : 'unread_show'  },
      text
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

    document.querySelectorAll('.unread').forEach((mountPoint) => {
      const itemRecid = mountPoint.dataset.itemRecid;
      const initialReadSts = JSON.parse(mountPoint.dataset.readSts);
      const type = mountPoint.dataset.type;
      ReactDOM.render(
        React.createElement(Unread, { itemRecid, initialReadSts, type }),
        mountPoint
      );
    });

    document.querySelectorAll('.item_checkbox').forEach((checkbox) => {
      checkbox.addEventListener('click', function (e) {
      if (document.querySelectorAll(".item_checkbox:checked").length === document.querySelectorAll(".item_checkbox").length) {
        document.getElementById('check_all').checked = true;
      }
      else{
         document.getElementById('check_all').checked = false;
      }
  });
});
  document.getElementById('check_all').addEventListener('change', handleCheckAll);
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
      tbody.innerHTML += generateItemlabel();
      groupedItems[year].forEach((item) => {
        tbody.innerHTML += generateItemRow(item);
      });
      table.appendChild(tbody);
      yearGroup.appendChild(table);
      itemListContainer.appendChild(yearGroup);
    });

    mountButtons();
    bindRelatedButtons();
    // restoreCheckedItems(); //  チェック状態復元を追加
  }

  // 通常のテーブル表示
  function renderTable(items) {
    var scrollOffsetY = window.pageYOffset;
    itemListContainer.innerHTML = '';
    const table = document.createElement('table');
    table.className = 'table table-striped table-bordered';
    table.style.tableLayout = 'auto';
    const tbody = document.createElement('tbody');

    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, items.length);
    const currentItems = items.slice(startIndex, endIndex);
    
    tbody.innerHTML += generateItemlabel();
    currentItems.forEach((item) => {
      tbody.innerHTML += generateItemRow(item);
    });

    table.appendChild(tbody);
    itemListContainer.appendChild(table);
    window.scrollTo(0,scrollOffsetY);
    mountButtons();
    bindRelatedButtons();
    updateReadStatus();
    // restoreCheckedItems(); //  チェック状態復元を追加
  }

  function generateItemlabel() {
      return `
      <tr>
        <td style="text-align: center; vertical-align: middle;">
          <input type="checkbox" id="check_all">
        </td>
        <td style="text-align: center; vertical-align: middle; width: 50px; white-space: nowrap;">
          ${document.getElementById('action').innerText}
        </td>
        <td style="width: auto;">
          ${document.getElementById('item_text').innerText}
        </td>
        <td style="text-align: center; vertical-align: top; width: 60px;">
          ${document.getElementById('stats').innerText}
        </td>
        <td style="text-align: center; vertical-align: top; width: 30px;">
          ${document.getElementById('info_text').innerText}
        </td>
        <td style="text-align: center; vertical-align: top;">
          ${document.getElementById('edit_text').innerText}
        </td>
      </tr>
    `;
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
        <td style="text-align: center; vertical-align: middle;">
          <input type="checkbox" value="item-checkbox" class="item_checkbox" />
        </td>
        <td style="text-align: center; vertical-align: middle; width: 50px;">
          <div class="favorite-mount-point" style="margin-bottom:6px;" data-type="1" data-item-recid="${item.recid}" data-favorite-sts='${JSON.stringify(item.favoriteSts)}'></div>
          <div class="read-mount-point" data-type="2" data-item-recid="${item.recid}" data-read-sts='${JSON.stringify(item.readSts)}'></div>
        </td>
        <td style="width: auto;">
          <strong><a href="/records/${item.recid}" data-item-title="${item.title}" data-item-recid="${item.recid}">${item.title}</a><span class="unread" data-type="3" data-item-recid="${item.recid}" data-read-sts='${JSON.stringify(item.readSts)}'></span><br>
          ${item.authorlist && item.authorlist.length > 0 ? `<span>${item.authorlist.join(', ')}</span><br>` : ''}
          <span>${item.magazineName || ''} ${(item.magazineName && item.conferenceName) ? '/' : ''} ${item.conferenceName || ''} ${(item.magazineName || item.conferenceName) ? '&nbsp;&nbsp;' : ''}</span>
          <span>${item.volume || ''} ${item.issue ? '('+item.issue+')' : ''} ${(item.volume || item.issue) ? '&nbsp;&nbsp;' : ''}</span>
          <span>${item.funderName || ''} ${(item.funderName && item.awardTitle) ? '|' : ''} ${item.awardTitle || ''}</span>
          ${(item.magazineName || item.conferenceName || item.volume || item.issue || item.funderName || item.awardTitle) ? '<br>' : ''}
          <span>${item.publicationDate} ${item.publicationDate ? '&nbsp;&nbsp;' : ''}</span>
          ${item.relation && item.relation.length > 0 ? `<span><a href="javascript:void(0)" class="relatedButton"><strong>${relation}</strong></a></span><span> </span> ${item.relation && item.relation.length > 0 ? '&nbsp;&nbsp;' : ''}` : ''}
          ${item.fileSts
            ? `<span>${documentfile} (${item.fileCnt || 0})： ${published}（${item.publicCnt || 0}）、${embargo}（${item.embargoedCnt || 0}）、 ${restricted}（${item.restrictedPublicationCnt || 0}）</span>`
            : `<span>${documentfile} (0)</span>`}<span> </span><br>
          ${relatedInfoHtml}
        </td>
        <td style="text-align: center; vertical-align: middle; width: 60px;">
          <span>
            <i class="bi bi-eye-fill" style="font-size: 20px; display: inline-block; margin-bottom:6px;"></i>${item.accessCnt}
          </span>
          <span>
            <i class="bi bi-file-earmark" style="font-size: 20px;"></i>${item.downloadCnt}
          </span>
        </td>
        <td style="text-align: center; vertical-align: top; width: 30px; padding-top:12px; padding-bottom:0px">
          <span style="border: 1px solid #000; padding: 5px; border-radius: '4px'; white-space:nowrap;">${item.resourceType}</span>
          <div style="margin-bottom:3px; margin-top:9px;white-space:nowrap;">${item.itemStatus}</div>
          <div style="margin-bottom:3px;">
            ${item.fbEmailSts
              ? `<i class="bi bi-envelope" style="font-size: 20px;"></i>`
              : `<i class="bi bi-envelope-dash" style="font-size: 20px;"></i>`}
          </div>
          <span>
          ${item.doi ? `<a href="${item.doi}">DOI</a>` : ''}
          </span>
        </td>
        <td style="text-align: center; vertical-align: top;">
          <a href="/workflow/edit_item_direct/${item.recid}" class="edit-item" data-item-id="">
            <i class="bi bi-pencil-square" style="font-size: 25px;"></i>
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
  
  function updateReadStatus(){
    document.querySelectorAll('a[data-item-title]').forEach(ta => {
      ta.addEventListener('click', async function(e){
          const target=document.querySelector(`.read-mount-point[data-item-recid="${this.dataset.itemRecid}"]`);
          const itemRecid = target.dataset.itemRecid;
          const type = target.dataset.type;
          try {
            const response = await fetch('/workspace/updateStatus', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ itemRecid, readSts: true, type }),
          });
          } catch (error) {
            console.error('Failed to update viewing status:', error);
        }
      })
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
    var sortedItems = sortItems(items.slice(0), sortItemSelect.value, sortOrderSelect.value);
    if (isGroupedByYear) {
      renderGroupedByYear(sortedItems);
      var groupedItems = {};
      sortedItems.forEach(function(item) {
        var year = new Date(item.publicationDate).getFullYear();
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
        onFilter: function(query) {
          items = query
            ? workspaceItemList.filter(function(item) {
                var lowerQuery = query.toLowerCase();
                return (
                  ((item.title ? item.title.toLowerCase() : '') || '').includes(lowerQuery) ||
                  ((item.magazineName ? item.magazineName.toLowerCase() : '') || '').includes(lowerQuery) ||
                  ((item.conferenceName ? item.conferenceName.toLowerCase() : '') || '').includes(lowerQuery) ||
                  ((item.funderName ? item.funderName.toLowerCase() : '') || '').includes(lowerQuery) ||
                  ((item.awardTitle ? item.awardTitle.toLowerCase() : '') || '').includes(lowerQuery) ||
                  ((item.doi ? item.doi.toLowerCase() : '') || '').includes(lowerQuery)
                );
              })
            : workspaceItemList.slice(0);
          currentPage = 1;
          updateDisplay();
        }
      }),
      searchContainer
    );
  }

  // 初期表示
  if (workspaceItemList.length > 0 || Object.keys(defaultConditions).length > 0) {
    updateDisplay();
    setupToggle();
  } else {
    mountButtons();
    bindRelatedButtons();
    setupToggle();
  }
});
