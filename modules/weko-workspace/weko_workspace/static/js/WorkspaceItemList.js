// WorkspaceItems.js
document.addEventListener('DOMContentLoaded', function () {
  const workspaceItemList = window.workspaceItemList || [];
  const sortItemSelect = document.getElementById('sort_item');
  const sortOrderSelect = document.getElementById('sort_order');
  const itemsPerPageSelect = document.getElementById('items_per_page');
  const table = document.querySelector('.table.table-striped.table-bordered');
  const tableBody = table.querySelector('tbody') || document.createElement('tbody');
  const pagination = document.querySelector('.pagination');

  if (!sortItemSelect || !sortOrderSelect || !itemsPerPageSelect || !pagination) {
    console.error('必要な要素が見つかりません');
    return;
  }

  let currentPage = 1;
  let itemsPerPage = parseInt(itemsPerPageSelect.value) || 20;

  // workspaceItemListが空の場合、既存のテーブルからデータを抽出
  let items = workspaceItemList;
  if (items.length === 0) {
    items = Array.from(tableBody.querySelectorAll('tr')).map(row => {
      const titleLink = row.querySelector('td:nth-child(2) strong a');
      const authorSpan = row.querySelector('td:nth-child(2) span:nth-child(2)');
      const metaSpan = row.querySelector('td:nth-child(2) span:nth-child(3)');
      const dateSpan = row.querySelector('td:nth-child(2) span:nth-child(5)');
      const doiLink = row.querySelector('td:nth-child(3) a');
      const accessSpan = row.querySelector('td:nth-child(3) span:nth-child(2)');
      const downloadSpan = row.querySelector('td:nth-child(3) span:nth-child(3)');
      const resourceSpan = row.querySelector('td:nth-child(4) span:nth-child(1)');
      const statusSpan = row.querySelector('td:nth-child(4) span:nth-child(2)');
      const favoriteMount = row.querySelector('.favorite-mount-point');
      const readMount = row.querySelector('.read-mount-point');

      return {
        recid: titleLink ? titleLink.href.split('/').pop() : '',
        title: titleLink ? titleLink.textContent.split(' -- ')[0] : '',
        authorlist: authorSpan ? authorSpan.textContent.split(', ') : [],
        magazineName: metaSpan ? metaSpan.textContent.split('／')[0] : '',
        conferenceName: metaSpan ? metaSpan.textContent.split('／')[1] : '',
        volume: metaSpan ? metaSpan.nextElementSibling.textContent.split('（')[0].trim() : '',
        issue: metaSpan ? metaSpan.nextElementSibling.textContent.match(/\((.*)\)/)[1] : '',
        publicationDate: dateSpan ? dateSpan.textContent : '',
        doi: doiLink ? doiLink.href : '',
        accessCnt: accessSpan ? parseInt(accessSpan.textContent.replace(/\D/g, '')) : 0,
        downloadCnt: downloadSpan ? parseInt(downloadSpan.textContent.replace(/\D/g, '')) : 0,
        resourceType: resourceSpan ? resourceSpan.textContent : '',
        itemStatus: statusSpan ? statusSpan.textContent : '',
        favoriteSts: favoriteMount ? JSON.parse(favoriteMount.dataset.favoriteSts) : false,
        readSts: readMount ? JSON.parse(readMount.dataset.readSts) : false,
        relation: [] // relationフィールドがない場合に備えて空配列を設定（必要に応じて調整）
      };
    });
  }

  // FavoriteButton Reactコンポーネント
  const FavoriteButton = ({ itemRecid, initialFavoriteSts, type }) => {
    const [isFavorite, setIsFavorite] = React.useState(initialFavoriteSts);
    const handleFavoriteToggle = async () => {
      try {
        const response = await fetch('/workspace/updateStatus', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ itemRecid, favoriteSts: !isFavorite, type })
        });
        if (response.ok) {
          setIsFavorite(!isFavorite);
          const item = items.find(i => i.recid === itemRecid);
          if (item) item.favoriteSts = !isFavorite;
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

  // ReadButton Reactコンポーネント
  const ReadButton = ({ itemRecid, initialReadSts, type }) => {
    const [isRead, setIsRead] = React.useState(initialReadSts);
    const handleReadToggle = async () => {
      try {
        const response = await fetch('/workspace/updateStatus', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ itemRecid, readSts: !isRead, type })
        });
        if (response.ok) {
          setIsRead(!isRead);
          const item = items.find(i => i.recid === itemRecid);
          if (item) item.readSts = !isRead;
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

  // ボタンをマウントする関数
  function mountButtons() {
    document.querySelectorAll('.favorite-mount-point').forEach(mountPoint => {
      const itemRecid = mountPoint.dataset.itemRecid;
      const initialFavoriteSts = JSON.parse(mountPoint.dataset.favoriteSts);
      const type = mountPoint.dataset.type;
      ReactDOM.render(
        React.createElement(FavoriteButton, { itemRecid, initialFavoriteSts, type }),
        mountPoint
      );
    });

    document.querySelectorAll('.read-mount-point').forEach(mountPoint => {
      const itemRecid = mountPoint.dataset.itemRecid;
      const initialReadSts = JSON.parse(mountPoint.dataset.readSts);
      const type = mountPoint.dataset.type;
      ReactDOM.render(
        React.createElement(ReadButton, { itemRecid, initialReadSts, type }),
        mountPoint
      );
    });
  }

  // 関連ボタンの展開機能を追加
  function bindRelatedButtons() {
    const buttons = document.querySelectorAll('.relatedButton');
    buttons.forEach(button => {
      button.addEventListener('click', function () {
        const content = this.closest('td').querySelector('.relatedInfo');
        if (content) {
          if (content.classList.contains('expanded')) {
            content.classList.remove('expanded');
            content.style.display = 'none';
          } else {
            content.classList.add('expanded');
            content.style.display = 'block';
          }
        }
      });
    });
  }

  // テーブルをレンダリングする関数
  function renderTable(items) {
    tableBody.innerHTML = '';
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, items.length);
    const currentItems = items.slice(startIndex, endIndex);

    currentItems.forEach(item => {
      const row = document.createElement('tr');
      // relation データがアイテムに存在する場合、関連情報を動的に生成
      const relatedInfoHtml = item.relation && item.relation.length > 0
        ? `<div class="relatedInfo" style="display: none;">${item.relation.map(relatedItem => 
            `<span>${relatedItem.relationType} ${relatedItem.relationTitle}、<a href="${relatedItem.relationUrl}">${relatedItem.relationUrl}</a></span><br>`
          ).join('')}</div>`
        : '';

      row.innerHTML = `
        <td style="text-align: center; vertical-align: top;">
          <div class="favorite-mount-point" data-type="1" data-item-recid="${item.recid}" data-favorite-sts='${JSON.stringify(item.favoriteSts)}'></div><br>
          <div class="read-mount-point" data-type="2" data-item-recid="${item.recid}" data-read-sts='${JSON.stringify(item.readSts)}'></div><br>
          <input type="checkbox" value="" /><br><br>
        </td>
        <td style="width: auto;">
          <strong><a href="${window.location.host}/records/${item.recid}">${item.title} -- recid: ${item.recid}</a></strong><br><br>
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
          <span style="border: 1px solid #000; padding: 5px; border-radius: 4px;">${item.resourceType}</span><br><br>
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
      `;
      tableBody.appendChild(row);
    });

    // ページング後にボタンを再マウント
    mountButtons();
    // 関連ボタンのイベントをバインド
    bindRelatedButtons();
  }

  // アイテムをソートする関数
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

  // ページングを更新する関数
  function updatePagination(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
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

    document.querySelectorAll('.get-pages').forEach(link => {
      link.addEventListener('click', function () {
        const page = parseInt(this.getAttribute('data-page'));
        if (page >= 1 && page <= totalPages) {
          currentPage = page;
          updateDisplay();
        }
      });
    });
  }

  // 表示を更新する関数
  function updateDisplay() {
    const sortedItems = sortItems([...items], sortItemSelect.value, sortOrderSelect.value);
    renderTable(sortedItems);
    updatePagination(items.length);
  }

  sortItemSelect.addEventListener('change', updateDisplay);
  sortOrderSelect.addEventListener('change', updateDisplay);
  itemsPerPageSelect.addEventListener('change', function () {
    itemsPerPage = parseInt(this.value);
    currentPage = 1;
    updateDisplay();
  });

  // 初期レンダリング
  if (items.length > 0) {
    updateDisplay();
  } else {
    mountButtons(); // サーバー側レンダリングの初期コンテンツを使用する場合、ボタンをマウント
    bindRelatedButtons(); // 初期表示に関連ボタンのイベントをバインド
  }
});