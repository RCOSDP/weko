require([
  "jquery",
  "bootstrap"
  ], function() {
    $(document).ready(function() {
        $('#color_setting select').each(function(){
          $(this).on('change', function(){
            var input = '#' + $(this).attr('id') + '_hex';
            var value = $(this).val();
            $(input).val(value);
          });
        });
        $('#color_setting input').each(function(){
          $(this).val('#0000FF')
        });
    });
});
