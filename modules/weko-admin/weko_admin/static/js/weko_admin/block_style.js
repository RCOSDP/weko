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
            $(input).css('background-color', value);
          });
        });
        $('#color_setting select').each(function(){
          var input = '#' + $(this).attr('id') + '_hex';
          var value = $(this).val();
          $(input).val(value);
          $(input).css('background-color', value);
        });
        //$('#bootstrap_cus1').on('click', function(){
        //  dynamicLoadCSS('/static/css/weko_theme/bootstrap_cus1.css');
        //});
        function dynamicLoadCSS(cssUrl) {
          var head = document.getElementsByTagName('head')[0];
          var link = document.createElement('link');
          link.type='text/css';
          link.rel = 'stylesheet';
          link.href = cssUrl;
          head.appendChild(link);
        }
    });
});
