  require([
    "jquery",
    "bootstrap"
    ], function() {
    $('#myModal').modal({
      show: false
    })

    $('#itemtype-submit').on('click', function(){
      var name = $('#itemtype-name').val();
      if(!name){
      }else{
        var data = {
          name: name,
          schema: $('#itemtype-json-schema').val(),
          form: $('#itemtype-schema-form').val()
        };
        send('/itemtypes/register', data);
      }
    });

    $("#item-type-lists").change(function (ev) {
      window.location.href = '/itemtypes/mapping/' + $(this).val();
    });

    $('#mapping-submit').on('click', function(){
      var data = {
        item_type_id: parseInt($('#item-type-lists').val()),
        mapping: $('#itemtype-schema-mapping').val()
      };
      send('/itemtypes/mapping', data);
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
          $('.modal-body').text(data.msg);
          $('#myModal').modal('show');
        },
        error: function(textStatus,errorThrown){
          $('.modal-body').text('Error: ' + JSON.stringify(textStatus));
          $('#myModal').modal('show');
        }
      });
    }
});
