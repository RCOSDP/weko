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

      const urlLoad = '/api/admin/load_lang';
      $.ajax({
        url: urlLoad,
        type: 'GET',
        success: function (data) {
          const results = data.results.filter(ele => ele.is_registered).sort((o1, o2) => {
            return o1.sequence - o2.sequence;
          });
          let options = '';
          for (let index = 0; index < results.length; index++) {
            const element = results[index];
            if (!index) {
              options += `<option value="${element.lang_code}" selected>${element.lang_name}</option>`;
              continue;
            }
            options += `<option value="${element.lang_code}">${element.lang_name}</option>`;
        }
          const select = $('select[id=\'lang-code\']');
          select.children().remove();
          select.append(options);
        },
        error: function (error) {
          console.log(error);
        }
      });
    });
});
