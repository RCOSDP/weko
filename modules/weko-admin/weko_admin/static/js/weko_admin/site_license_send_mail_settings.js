$('#repository_select').on('change', function () {
  let repoId = document.getElementById("repository_select").value;
  $.ajax({
    url: "/api/admin//get_site_license_send_mail_settings",
    method: "GET",
    data: { repo_id: repoId },
    success: function (data) {
      let sitelicensesTableBody = document.querySelector("#sitelicenses_table tbody");
      sitelicensesTableBody.innerHTML = "";

      data.sitelicenses.forEach(function (sitelicense) {
        let row = document.createElement("tr");
        row.innerHTML = `
                    <td align="center" valign="middle">
                        <input type="checkbox" name="${sitelicense.organization_name}" id="send_mail_flag_${sitelicense.organization_id}"
                            ${sitelicense.receive_mail_flag === 'T' && sitelicense.mail_address ? 'checked' : ''}
                            ${!sitelicense.mail_address ? 'disabled' : ''}
                        >
                    </td>
                    <td>${sitelicense.organization_name}</td>
                    <td>
                        ${sitelicense.mail_address.split("\n").length >= 3
            ? `<textarea class="form-control" rows="3" cols="52" name="mail_address" readonly>${sitelicense.mail_address}</textarea>`
            : sitelicense.mail_address.split("\n").map(mail => `${mail}<br>`).join('')}
                    </td>
                `;
        sitelicensesTableBody.appendChild(row);
      });

      let autoSendValue = data.auto_send ? "True" : "False";
      let autoSendRadio = document.querySelector('input[name="dis_enable_auto_send"][value="' + autoSendValue + '"]');
      if (autoSendRadio) {
        autoSendRadio.checked = true;
      }
    },
    error: function () {
      alert('Failed to fetch data');
    }
  });
});

// Confirm manual send
$('#confirm_send_button').on('click', function () {
  $("#manual_send_mail").attr('disabled', true);
  $("#manual_send_mail").attr('data-target', null);
  let s = Number($("#from_year_select").val() + paddingLeft($("#from_month_select").val(), 2));
  let e = Number($("#to_year_select").val() + paddingLeft($("#to_month_select").val(), 2));
  if (s > e) {
    alert('Selected period is wrong!');
    return;
  }
  let start_month = $("#from_year_select").val() + '-' + paddingLeft($("#from_month_select").val(), 2);
  let end_month = $("#to_year_select").val() + '-' + paddingLeft($("#to_month_select").val(), 2);
  let repo_id = document.getElementById("repository_select").value;
  $.ajax({
    url: '/api/admin/sitelicensesendmail/send/' + start_month + '/' + end_month,
    type: 'POST',
    data: { repo_id: repo_id },
    success: function (data) {
      alert('Send successfully');
    },
    error: function (error) {
      console.log(error);
      alert('Send erroneously');
    }
  });
  $('#send_mail_confirm_modal').modal('hide');
  $("#manual_send_mail").attr('data-target', '#send_mail_confirm_modal');
  $("#manual_send_mail").attr('disabled', null);
});

$('input:radio[name="dis_enable_auto_send"]').change(function () {
  //document.getElementById("manual_send_mail").enabled = false
  $("#manual_send_mail").attr('disabled', true);
  $("#manual_send_mail").attr('data-target', null);
});

let checked_list = {};
$(document).on('change', 'input:checkbox[id^="send_mail_flag_"]', function () {
  $("#manual_send_mail").attr('disabled', true);
  $("#manual_send_mail").attr('data-target', null);
  checked_list[$(this)[0].name] = $(this)[0].checked ? 'T' : 'F';
});

$('#save_settings').on('click', function () {
  let auto_send_flag = $('input:radio[id="enable_auto_send"]')[0].checked ? true : false;
  //let check_list = document.querySelectorAll("[id^=send_mail_flag_]");
  let data = {};
  data['auto_send_flag'] = auto_send_flag;
  data['checked_list'] = checked_list;
  data['repository_id'] = document.getElementById("repository_select").value;
  $.ajax({
    url: '/admin/sitelicensesendmail/',
    type: "POST",
    contentType: 'application/json',
    data: JSON.stringify(data),
    success: function (data) {
      alert('Update successfully');
      location.reload();
    },
    error: function (error) {
      console.log(error);
      alert('Update erroneously');
      location.reload();
    }
  });
});

function paddingLeft(str, lenght) {
  if (str.length >= lenght)
    return str;
  else
    return paddingLeft("0" + str, lenght);
}
