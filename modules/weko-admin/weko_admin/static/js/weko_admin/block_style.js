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

        document.querySelector('#logo_file').onchange = function() {
//          var reader = new FileReader();
//
//          reader.onload = function() {
//            var dataURL = reader.result;
//            document.querySelector('#preview').src = dataURL;
//          };
//
//          reader.readAsDataURL(this.files[0]);
          $('#fpname').text(this.files[0].name);
          $('#fpsize').text(humanSize(this.files[0].size, 0));
          $('#fptype').text(this.files[0].type);
          $('#logo_info').removeClass('hide');
        };
        unit = ['bytes','KB','MB','GB'];
        function humanSize(defSize, unit_idx) {
          let tmp_size = round(defSize, 2);
          let human_size = ''+tmp_size+unit[unit_idx];
          if(defSize > 1024 && unit_idx < 2) {
            human_size = humanSize(defSize/1024, ++unit_idx);
          }
          return human_size;
        }
        function round(number, precision) {
          return Math.round(+number + 'e' + precision) / Math.pow(10, precision);
        }
    });
});
