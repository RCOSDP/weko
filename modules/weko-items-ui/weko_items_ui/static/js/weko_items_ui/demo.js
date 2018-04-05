require([
  'jquery'
],function () {
  $('#myModal').modal({
    show: false
  })
  function Percentage(num, total) {
    return (Math.round(num / total * 10000) / 100.00 + "%");// 小数点后两位百分比
  }
  $('#demo-submit').on('click', function(){
    var demoStr = $('#item-demo-data').val();
    if(/\n/.test(demoStr) == false) {
      console.log('demoStr does not match lf');
      return;
    }
    var demoList = demoStr.split(/\n/);
    for(idx=0; idx<demoList.length; idx++) {
      if(demoList[idx].length == 0){break;}
      itemData = JSON.parse(demoList[idx]);
      indexData = JSON.parse(demoList[++idx]);
      $.ajax({
        type: 'POST',
        url: '/api/deposits/items',
        async: false,
        cache: false,
        data: JSON.stringify({'$schema': itemData['$schema']}),
        dataType: "json",
        contentType: "application/json",
        success: function(data,textStatus){
          rec_id = data['id'];
          index_url = data['links']['index'];
          self_url = data['links']['self'];
          // post item data
          $.ajax({
            type: "PUT",
            url: index_url,
            async: false,
            cache: false,
            data: JSON.stringify(itemData),
            contentType: "application/json",
            success: function(){
              // post index data
              $.ajax({
                type: "PUT",
                url: self_url,
                async: false,
                cache: false,
                data: JSON.stringify(indexData),
                contentType: "application/json",
                success: function(){},
                error: function() {}
              });
            },
            error: function() {}
          });
        }});
    }
    $('.modal-body').text('completed');
    $('#myModal').modal('show');
  });
});
