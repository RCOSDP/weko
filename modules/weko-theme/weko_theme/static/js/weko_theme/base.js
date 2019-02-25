require([
  "jquery",
  "bootstrap"
  ], function() {
    $(document).ready(function() {
      $('#btn_edit_start').on('click', function(){
        window.location.href = '/schema/list/';
      });
      $('#btn_edit_stop').on('click', function(){
        window.location.href = '/';
      });

      // Chunk Design
      $.ajax({
        url: '/admin/chunk-select/format',
        method: 'GET',
        async: false,
        success: function(data, status) {

          format = data.format;

          if (!format) {
            alert('Load chunk format failed.');
            return;
          }

          if (format === '1') {
            $('#grid-info').attr('hidden', 'hidden');

          }else if (format === '2') {
            $('#grid-body-left').attr('hidden', 'hidden');
            $('#grid-body').attr('class', 'col-md-9');

          }else if (format === '3') {
            $('#grid-body-right').attr('hidden', 'hidden');
            $('#grid-body').attr('class', 'col-md-9');

          }
        },
        error: function(jqXHR, status) {
          alert('Load chunk format failed.');
        }
      });



    });
});
