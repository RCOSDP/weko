require([
  "jquery",
  ], function() {
  $('#itemtype-edit').on('click', function(){
    window.location.href = '/itemtypes/';
  });

  function getItemsByIndex(node) {
    refreshBreak(node);
  }

  // パンくずリストを再表示する
  function refreshBreak(node) {
    let tmp = '<ol class="breadcrumb">';
    node.parents && node.parents.forEach(function(element){
      tmp = tmp + '<li><a href="#'+element.id+'">'+element.title+'</a></li>';
    });
    tmp = tmp + '<li class="active">'+node.title+'</a></li>';
    tmp = tmp + '</ol>';
    $('.panel_bread').html(tmp);
  }

  function refreshIndexTree() {
    $.get('/indextree/jsonmapping', function(data, status){
      if(data && Array.isArray(data)) {
        let element = document.getElementById('index_tree');
        let editor = new JSONTreeView(element, {
            data: data,
            onClick: function(node){
              getItemsByIndex(node);
            }
        });
        data.length && refreshBreak(data[0]);
      }
    });
  }
  refreshIndexTree();
});
