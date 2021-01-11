$(document).ready(function () {
  checkWorkflowName();
  displayIndexTreeSelection();
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
  let selected = $('#txt_flow_name option:selected').text();
  let index_id = null;
  if (check_show_indexes(selected)) {
    index_id = $('#txt_index').val()
  }
  let post_data = {
    id: $("#_id").val(),
    flows_name: $("#txt_workflow_name").val(),
    itemtype_id: $("#txt_itemtype").val(),
    flow_id: $("#txt_flow_name").val(),
  };
  if (index_id !== null) {
    post_data['index_id'] = index_id;
  }
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

function check_show_indexes(selected) {
  let show_items_lit = $("#special_itemtype_list").val();
  if (typeof show_items_lit === "string") {
    show_items_lit = JSON.parse(show_items_lit);
  }
  for (const show_items of show_items_lit) {
    if (selected === show_items) {
      return true;
    }
  }
  return false
}

function displayIndexTreeSelection() {
  let selected = $('#txt_flow_name option:selected').text();
  let is_show_selection_index = $('#enable_showing_index_tree_selection_value').val();
  if (is_show_selection_index === 'True' && check_show_indexes(selected)) {
    $('#index-tree').removeAttr('hidden');
  } else {
    $('#index-tree').attr("hidden", true);
  }
}

$('#txt_flow_name').on('change', function () {
  displayIndexTreeSelection();
});
