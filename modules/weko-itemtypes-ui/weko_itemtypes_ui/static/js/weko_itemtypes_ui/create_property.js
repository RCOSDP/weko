require([
  "jquery",
  "bootstrap"
  ], function() {
    initschema = {
          type: "object",
          properties: {},
          required: []
        }
    url_update_schema = '/itemtypes/property';
    element = document.getElementById('new_option');
    var editor = new JSONSchemaEditor(element, {
      startval: initschema,
      editor: true
    });
    $('#previews').on('click', function(){
      schema = editor.getValue();
      forms = editor.exportForm();
      $('#schema_json').text(JSON.stringify(schema, null, 4));
      $('#form1_json').val(JSON.stringify(forms.form, null, 4));
      $('#form2_json').val(JSON.stringify(forms.forms, null, 4));
    });
    $('#sending').on('click', function(){
      let data = {
        name: $('#property_name').val(),
        schema: editor.getValue(),
        form1: JSON.parse($('#form1_json').val()),
        form2: JSON.parse($('#form2_json').val())
      }
      send(url_update_schema, data);
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

    $('#item-type-lists').on('change', function(){
      if($('#item-type-lists').val().length > 0) {
        url = '/itemtypes/property/' + $('#item-type-lists').val();
        $.get(url, function(data, status){
          url_update_schema = '/itemtypes/property/'+data.id;
          $('#property_name').val(data.name);
          $('#schema_json').text(JSON.stringify(data.schema, null, 4));
          $('#form1_json').val(JSON.stringify(data.form, null, 4));
          $('#form2_json').val(JSON.stringify(data.forms, null, 4));
          editor.setValue({
            startval: data.schema,
            editor: true
          });
        });
      } else {
        url_update_schema = '/itemtypes/property';
        $('#property_name').val('');
        $('#schema_json').text('');
        $('#form1_json').val('');
        $('#form2_json').val('');
        editor.setValue({
          startval: initschema,
          editor: true
        });
      }
    });
});
