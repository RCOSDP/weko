$(document).ready(function () {
  $("#input_type").change((e) => {
    let value = $(this).val();
    if (value == "0") {
      $("#CrossRef_API").addClass("hidden");
    } else if (value == "1") {
      $("#CrossRef_API").removeClass("hidden");
    }
  });

  $("#api_account_save").click((e) => {
    save();
  });
});

save = () => {
  let data = {
    api_code: $('#input_type').val(),
    cert_data: $('#cross_ref_account').val()
  }
  $.ajax({
    url: "/api/admin/save_api_cert_data",
    type: 'POST',
    data: data,

    success: function (data) {
      let results = data.results;
      if (!results) {
        return;
      }

    },
    error: function (error) {
      console.log(error);
      alert('Error when get languages');
    }
  });
}

loadDataForInputType = () => {
  $.ajax({
    url: "/api/admin/get_api_cert_type",
    type: 'GET',
    success: function (data) {
      let error = data.error;
      let results = data.results;
      if(error){
        console.log(error)
        return;
      }
      if (!results) {
        return;
      }
      let options = '';
      for (let i = 0; i < results.length; i++) {
        options += `<option value = "${results[i].api_code}">${results[i].api_name}</option>`;
      }
      const select = $('#input_type');
      select.append(options);
    },
    error: function (error) {
      console.log(error);
      alert('Error when get languages');
    }
  });
}
