$(document).ready(function () {
    const currentTime = new Date().getTime();
    const urlLoad = '/api/admin/get_selected_lang?' + currentTime;
  $.ajax({
    url: urlLoad,
    type: 'GET',
    success: function (data) {
      let options = '';
      if (!data.lang) {
        return;
      } else {
        if (!data.selected && data.lang[0].lang_code) {
          data.selected = data.lang[0].lang_code
        }
          const results = data.lang.sort(function(o1, o2) {
          return o1.sequence - o2.sequence;
        });

        for (let index = 0; index < results.length; index++) {
          const element = results[index];
          if (element.lang_code === data.selected) {
             options += "<option value=" + element.lang_code + " selected>" + element.lang_name + "</option>";
            continue;
          }
             options += "<option value=" + element.lang_code + ">" + element.lang_name + "</option>";
        }
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
