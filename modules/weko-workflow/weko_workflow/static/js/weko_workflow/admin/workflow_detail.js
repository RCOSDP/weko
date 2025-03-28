$(document).ready(function () {
  checkWorkflowName();
});

const select_show = $('#select_show');
const select_hide = $('#select_hide');

$("#txt_workflow_name").keyup(function () {
  if ($("#txt_workflow_name").val().trim() == "") {
    $("#btn_create").attr("disabled", "disabled");
  } else {
    if ($("#btn_create").prop("disabled")) {
      $("#btn_create").removeAttr("disabled");
    }
  }
});

function checkWorkflowName() {
  if ($("#txt_workflow_name").val().trim() == "") {
    $("#btn_create").attr("disabled", "disabled");
  }
}

function addAlert(message) {
  $("#alerts").append(
    '<div class="alert alert-light" id="alert-style">' +
      '<button type="button" class="close" data-dismiss="alert">' +
      "&times;</button>" +
      message +
      "</div>"
  );
}

$("#btn_back").on("click", function () {
  window.history.back();
});

$("#btn_delete").on("click", function () {
  const post_uri = $("#delete_uri").text();
  $.ajax({
    url: post_uri,
    method: "DELETE",
    async: true,
    contentType: "application/json",
    success: function (data, status) {
      if (0 != data.code) {
        $("#inputModal").html(data.msg);
        $("#allModal").modal("show");
      } else {
        document.location.href = data.data.redirect;
      }
    },
    error: function (jqXHE, status) {
      $("#inputModal").html("Delete Failed");
      $("#allModal").modal("show");
    },
  });
});

$("#btn_create").on("click", function () {
  const post_uri = $("#post_uri").text();
  var list_hide = [];
  $("#select_hide option").each(function() {
    list_hide.push(this.value);
  });
  let post_data = {
    id: $("#_id").val(),
    flows_name: $("#txt_workflow_name").val(),
    itemtype_id: $("#txt_itemtype").val(),
    flow_id: $("#txt_flow_name").val(),
    delete_flow_id: $("#txt_flow_delete").val(), 
    list_hide: list_hide,
    open_restricted: $('#restricted_access_flag')?.is(":checked"),
    is_gakuninrdm: $('#chkboxGakuNinRDMFlag').is(":checked")
  };
  let index_id = $('#txt_index').val()
  if (index_id !== '') {
    post_data['index_id'] = index_id;
  }
  location_id = $('#txt_location').val()
  post_data['location_id'] = location_id !== '' ? location_id : null;
  $.ajax({
    url: post_uri,
    method: "POST",
    async: true,
    contentType: "application/json",
    data: JSON.stringify(post_data),
    success: function (data, status) {
      if (0 == data.code) {
        document.location.href = data.data.redirect;
        addAlert("Workflow created successfully.");
      }
    },
    error: function (jqXHE, status) {
      $("#inputModal").html("Something went wrong.");
      $("#allModal").modal("show");
    },
  });
});

$('#setShow').on('click', function () {
  select_hide.find('option:selected').detach().prop("selected", false).appendTo(select_show);
});

$('#setHide').on('click', function () {
  select_show.find('option:selected').detach().prop("selected", false).appendTo(select_hide);
});
