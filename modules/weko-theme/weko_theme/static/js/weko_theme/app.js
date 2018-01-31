require([
  "jquery",
  ], function() {
  $('#itemtype-edit').on('click', function(){
    window.location.href = '/itemtypes';
  });

  function getItemsByIndex(indexid) {
    alert(indexid);
  }

  function refreshIndexTree() {
    $.get('/indextree/jsonmapping', function(data, status){
      var element = document.getElementById('index_tree');
      var editor = new JSONTreeView(element, {
          data: data,
          onClick: function(node){
            getItemsByIndex(node.id);
          }
      });
    });
  }
  refreshIndexTree();
});
