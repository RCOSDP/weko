$(document).ready(function () {
  checkWorkflowName();
  setI18n();
});

const select_show = $('#select_show');
const select_hide = $('#select_hide');
const MESSAGE = {
  display: {
    en: "Display",
    ja: "表示",
  },
  hide: {
    en: "Hide",
    ja: "非表示",
  },
  display_hide: {
    en: "Display/Hide",
    ja: "表示/非表示",
  }
}

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

$('#setShow').on('click', function () {
  select_hide.find('option:selected').detach().prop("selected", false).appendTo(select_show);
});

$('#setHide').on('click', function () {
  select_show.find('option:selected').detach().prop("selected", false).appendTo(select_hide);
});

function setI18n() {
  list_I18n = ['display', 'hide', 'display_hide']
  list_I18n.forEach(element => {
    getMessage(element)
  });
}

function getMessage(messageCode) {
  const defaultLanguage = "en";
  let currentLanguage = document.getElementById("current_language").value;
  let message = MESSAGE[messageCode];
  if (message) {
    if (message[currentLanguage]) {
      $('#' + messageCode).html(message[currentLanguage]);
    } else {
      $('#' + messageCode).html(message[defaultLanguage]);
    }
  }
}
