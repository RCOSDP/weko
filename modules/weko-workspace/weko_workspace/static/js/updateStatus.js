// static/js/favorite-button.js
console.log('updateStatus.js loaded');
const { useState, useEffect } = React;

// FavoriteButton コンポーネントを定義する
const FavoriteButton = ({ itemRecid, initialFavoriteSts ,type}) => {
  const [isFavorite, setIsFavorite] = useState(initialFavoriteSts);
  const handleFavoriteToggle = async () => {
    try {
      const response = await fetch('/workspace/updateStatus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ itemRecid, favoriteSts: !isFavorite ,type})
      });
      if (response.ok) setIsFavorite(!isFavorite);
    } catch (error) {
      console.error('Failed to update favorite status:', error);
    }
  };

  return (
    <a href="#" onClick={(e) => { e.preventDefault(); handleFavoriteToggle(); }}>
      {isFavorite ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" className="bi bi-star-fill" viewBox="0 0 16 16">
          <path d="M3.612 15.443c-.386.198-.824-.149-.746-.592l.83-4.73L.173 6.765c-.329-.314-.158-.888.283-.95l4.898-.696L7.538.792c.197-.39.73-.39.927 0l2.184 4.327 4.898.696c.441.062.612.636.282.95l-3.522 3.356.83 4.73c.078.443-.36.79-.746.592L8 13.187l-4.389 2.256z" />
        </svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" className="bi bi-star" viewBox="0 0 16 16">
          <path d="M2.866 14.85c-.078.444.36.791.746.593l4.39-2.256 4.389 2.256c.386.198.824-.149.746-.592l-.83-4.73 3.522-3.356c.33-.314.16-.888-.282-.95l-4.898-.696L8.465.792a.513.513 0 0 0-.927 0L5.354 5.12l-4.898.696c-.441.062-.612.636-.283.95l3.523 3.356-.83 4.73zm4.905-2.767-3.686 1.894.694-3.957a.56.56 0 0 0-.163-.505L1.71 6.745l4.052-.576a.53.53 0 0 0 .393-.288L8 2.223l1.847 3.658a.53.53 0 0 0 .393.288l4.052.575-2.906 2.77a.56.56 0 0 0-.163.506l.694 3.957-3.686-1.894a.5.5 0 0 0-.461 0z" />
        </svg>
      )}
    </a>
  );
};

// ReadButton コンポーネントを定義する
const ReadButton = ({ itemRecid, initialReadSts ,type}) => {
  const [isRead, setIsRead] = useState(initialReadSts);
  const handleReadToggle = async () => {
    try {
      const response = await fetch('/workspace/updateStatus', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ itemRecid, readSts: !isRead ,type})
      });
      if (response.ok) setIsRead(!isRead);
    } catch (error) {
      console.error('Failed to update read status:', error);
    }
  };

  return (
    <a href="#" onClick={(e) => { e.preventDefault(); handleReadToggle(); }}>
      {isRead ? (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-book-fill" viewBox="0 0 16 16">
          <path d="M8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783" />
        </svg>
      ) : (
        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" class="bi bi-book" viewBox="0 0 16 16">
          <path d="M1 2.828c.885-.37 2.154-.769 3.388-.893 1.33-.134 2.458.063 3.112.752v9.746c-.935-.53-2.12-.603-3.213-.493-1.18.12-2.37.461-3.287.811zm7.5-.141c.654-.689 1.782-.886 3.112-.752 1.234.124 2.503.523 3.388.893v9.923c-.918-.35-2.107-.692-3.287-.81-1.094-.111-2.278-.039-3.213.492zM8 1.783C7.015.936 5.587.81 4.287.94c-1.514.153-3.042.672-3.994 1.105A.5.5 0 0 0 0 2.5v11a.5.5 0 0 0 .707.455c.882-.4 2.303-.881 3.68-1.02 1.409-.142 2.59.087 3.223.877a.5.5 0 0 0 .78 0c.633-.79 1.814-1.019 3.222-.877 1.378.139 2.8.62 3.681 1.02A.5.5 0 0 0 16 13.5v-11a.5.5 0 0 0-.293-.455c-.952-.433-2.48-.952-3.994-1.105C10.413.809 8.985.936 8 1.783" />
        </svg>
      )}
    </a>
  );
};

// 掛載ロジックを独立した関数として定義する
const mountFavorites = () => {
  console.log('Mounting favorites');
  document.querySelectorAll('.favorite-mount-point').forEach((mountPoint) => {
    const itemRecid = mountPoint.dataset.itemRecid;
    const initialFavoriteSts = JSON.parse(mountPoint.dataset.favoriteSts);
    const type = mountPoint.dataset.type;
    ReactDOM.render(
      <FavoriteButton itemRecid={itemRecid} initialFavoriteSts={initialFavoriteSts} type={type}/>,
      mountPoint
    );
  });
};

const mountRead = () => {
  console.log('Mounting read');
  document.querySelectorAll('.read-mount-point').forEach((mountPoint) => {
    const itemRecid = mountPoint.dataset.itemRecid;
    const initialReadSts = JSON.parse(mountPoint.dataset.readSts);
    const type = mountPoint.dataset.type;
    ReactDOM.render(
      <ReadButton itemRecid={itemRecid} initialReadSts={initialReadSts} type={type}/>,
      mountPoint
    );
  });
};


// DOM がすでにロードされているかどうかをチェックする
if (document.readyState === 'complete' || document.readyState === 'interactive') {
  console.log('DOM already loaded');
  mountFavorites(); // DOM がすでにロードされている場合、直接実行する。
  mountRead();
} else {
  console.log('Waiting for DOMContentLoaded');
  document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded');
    mountFavorites();
    mountRead();
  });
}