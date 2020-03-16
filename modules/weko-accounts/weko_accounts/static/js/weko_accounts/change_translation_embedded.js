$(document).ready(function() {
  const currentTime = new Date().getTime();
  const urlLoad = '/api/admin/get_selected_lang?' + currentTime;
  $.ajax({
    url: urlLoad,
    type: "GET",
    success: function(data) {
      if (!data.lang) {
        return;
      } else {
        const selectedLang = data.selected;
        if (selectedLang != "ja") {
          $("input#wayf_submit_button").val("Login");
          $("label#wayf_remember_checkbox_label").text(
            "Remember selection for this web browser session"
          );
          $("label#inc_type_label").text("Type list:");
          $("label#inc_categories_label").text("Category:");
          $("span#wayf_type_name_0").text("All");
          $("span#wayf_type_name_1").text("Hokkaido");
          $("span#wayf_type_name_2").text("Tohoku");
          $("span#wayf_type_name_3").text("Kanto");
          $("span#wayf_type_name_4").text("Chubu");
          $("span#wayf_type_name_5").text("Kinki");
          $("span#wayf_type_name_6").text("Chugoku");
          $("span#wayf_type_name_7").text("Shikoku");
          $("span#wayf_type_name_8").text("Kyushu");
          $("span#wayf_type_name_9").text("Others");
          $("span#wayf_categories_name_0").text("All");
          $("span#wayf_categories_name_1").text("University");
          $("span#wayf_categories_name_2").text("College");
          $("span#wayf_categories_name_3").text("Institute of Technology");
          $("span#wayf_categories_name_4").text("Research Institute");
          $("span#wayf_categories_name_5").text("Others");
        }
      }
    },
    error: function(error) {
      console.log(error);
    }
  });
});
