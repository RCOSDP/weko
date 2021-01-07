$(document).ready(function () {
  checkWorkflowName();
});

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
      var modalcontent = "Delete Failed";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
    },
  });
});

$("#btn_create").on("click", function () {
  const post_uri = $("#post_uri").text();
  var list_hide = []
  var list_show = []
  $("#select_hide option").each(function() {
    console.log(this.value);
    list_hide.push(this.value);
  });
  post_data = {
    id: $("#_id").val(),
    flows_name: $("#txt_workflow_name").val(),
    itemtype_id: $("#txt_itemtype").val(),
    flow_id: $("#txt_flow_name").val(),
    list_hide: list_hide
  };
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
      var modalcontent = "Something went wrong.";
      $("#inputModal").html(modalcontent);
      $("#allModal").modal("show");
    },
  });
});

$("#setHide").on("click", function () {
  value_hide = $('#select_show').val();
  text_hide = $("#select_show option:selected").text();
  if (value_hide) {
    $("#select_show option[value='"+ value_hide +"']").remove();
    $('#select_hide').append($('<option>', {value:value_hide, text: text_hide}));
  }
});

$("#setShow").on("click", function () {
  value_show = $('#select_hide').val();
  text_show = $("#select_hide option:selected").text();
  if (value_show) {
    $("#select_hide option[value='"+ value_show +"']").remove();
    $('#select_show').append($('<option>', {value:value_show, text: text_show}));
  }
});
