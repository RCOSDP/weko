  require([
    "jquery",
    "bootstrap"
    ], function() {
    $('#myModal').modal({
      show: false
    })

    $('#index-tree-submit').on('click', function(){
      var data = {
        index_tree: $('#index-tree').val()
      };
      send('/indextree/edit', data);
    });

    function send(url, data){
      $.ajax({
        method: 'POST',
        url: url,
        async: true,
        contentType: 'application/json',
        dataType: 'json',
        data: JSON.stringify(data),
        success: function(data,textStatus){
          refreshIndexTree();
          $('.modal-body').text(data.msg);
          $('#myModal').modal('show');
        },
        error: function(textStatus,errorThrown){
          $('.modal-body').text('Error: ' + JSON.stringify(textStatus));
          $('#myModal').modal('show');
        }
      });
    }

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
