require([
  "jquery",
  "bootstrap"
], function () {
  /*
  $(function(){
    history.pushState(null,null,null)
    window.addEventListener('popstate', function(e) {
      $('a.back-button')[0].click()
    });
  })
  */
  /**
   * Start Loading
   * @param actionButton
   */
  function startLoading(actionButton) {
    actionButton.prop('disabled', true);
    $(".lds-ring-background").removeClass("hidden");
  }

  /**
   * End Loading
   * @param actionButton
   */
  function endLoading(actionButton) {
    actionButton.removeAttr("disabled");
    $(".lds-ring-background").addClass("hidden");
  }

  $('.btn-begin').on('click', function () {
      let _this = $(this);
      startLoading(_this);
      let post_uri = $('#post_uri').text();
      let workflow_id = $(this).data('workflow-id');
      let community = $(this).data('community');
      let post_data = {
          workflow_id: workflow_id,
          flow_id: $('#flow_' + workflow_id).data('flow-id'),
          itemtype_id: $('#item_type_' + workflow_id).data('itemtype-id')
      };
      if(community != ""){
        post_uri = post_uri+"?c="+ community;
      }
      $.ajax({
          url: post_uri,
          method: 'POST',
          async: true,
          contentType: 'application/json',
          data: JSON.stringify(post_data),
          success: function (data, status) {
              if (0 == data.code) {
                  document.location.href = data.data.redirect;
              } else {
                  endLoading(_this);
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
            endLoading(_this);
          }
      });
  });

  $('#btn-finish').on('click', function(){
    let _this = $(this);
    startLoading(_this);
    let post_uri = $('.cur_step').data('next-uri');
    if (!post_uri) {
      let error_msg = $('#AutoCancelMsg').text();
      $('#cancelModalBody').text(error_msg);
      $('#cancelModal').modal('show');
    }
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 0
    };
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function(data, status) {
        if(0 == data.code) {
          if(data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href=data.data.redirect;
          } else {
            document.location.reload(true);
          }
        } else if (-2 == data.code) {
          let error_msg = $('#AutoCancelMsg').text();
          $('#cancelModalBody').text(error_msg);
          $('#cancelModal').modal('show');
        } else {
          endLoading(_this);
          alert(data.msg);
        }
      },
      error: function(jqXHR, status) {
        if (-2 == jqXHR.responseJSON.code) {
          let error_msg = $('#AutoCancelMsg').text();
          $('#cancelModalBody').text(error_msg);
          $('#cancelModal').modal('show');
        } else if (-1 ==jqXHR.responseJSON.code) {
          endLoading(_this);
          alert(jqXHR.responseJSON.msg);
        } else{
          endLoading(_this);
          alert('server error');
          $('#myModal').modal('hide');
        }
      }
    });
  });

  $('#btn-draft').on('click', function(){
    let _this = $(this);
    startLoading(_this);
    let post_uri = $('.cur_step').data('next-uri');
    if (!post_uri) {
      let error_msg = $('#AutoCancelMsg').text();
      $('#cancelModalBody').text(error_msg);
      $('#cancelModal').modal('show');
    }
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 1
    };
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function(data, status) {
        if(0 == data.code) {
          if(data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href=data.data.redirect;
          } else {
            document.location.reload(true);
          }
        } else if (-2 == data.code) {
          let error_msg = $('#AutoCancelMsg').text();
          $('#cancelModalBody').text(error_msg);
          $('#cancelModal').modal('show');
        } else {
          endLoading(_this);
          alert(data.msg);
        }
      },
      error: function(jqXHR, status) {
        if (-2 == jqXHR.responseJSON.code) {
          let error_msg = $('#AutoCancelMsg').text();
          $('#cancelModalBody').text(error_msg);
          $('#cancelModal').modal('show');
        } else if (-1 == jqXHR.responseJSON.code) {
          endLoading(_this);
          alert(jqXHR.responseJSON.msg);
        } else {
          endLoading(_this);
          alert('server error');
          $('#myModal').modal('hide');
        }
      }
    });
  });

  $('#btn-approval-req').on('click', function () {
      action_id = $('#hide-actionId').text();
      btn_id = "action_" + action_id;
      $('#' + btn_id).click();
  });

  $('#btn-approval').on('click', function () {
      let _this = $(this);
      startLoading(_this);
      let uri_apo = $('.cur_step').data('next-uri');
      if (!uri_apo) {
        let error_msg = $('#AutoCancelMsg').text();
        $('#cancelModalBody').text(error_msg);
        $('#cancelModal').modal('show');
      }
      let act_ver = $('.cur_step').data('action-version');
      let community_id = $('#community_id').text();
      let post_data = {
          commond: $('#input-comment').val(),
          action_version: act_ver,
          community: community_id
      };
      $.ajax({
          url: uri_apo,
          method: 'POST',
          async: true,
          contentType: 'application/json',
          data: JSON.stringify(post_data),
          success: function (data, status) {
              if (0 == data.code) {
                  if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
                      document.location.href = data.data.redirect;
                  } else {
                      document.location.reload(true);
                  }
              } else if (-2 == data.code) {
                  let error_msg = $('#AutoCancelMsg').text();
                  $('#cancelModalBody').text(error_msg);
                  $('#cancelModal').modal('show');
              } else {
                  endLoading(_this);
                  alert(data.msg);
              }
          },
          error: function (jqXHR, status) {
            if (-2 == jqXHR.responseJSON.code) {
              let error_msg = $('#AutoCancelMsg').text();
              $('#cancelModalBody').text(error_msg);
              $('#cancelModal').modal('show');
            } else if (-1 == jqXHR.responseJSON.code){
              endLoading(_this);
              alert(jqXHR.responseJSON.msg);
            } else {
              endLoading(_this);
              alert('server error');
            }
          }
      });
  });

  $('#btn-reject').on('click', function () {
      let _this = $(this);
      startLoading(_this);
      let uri_apo = $('.cur_step').data('next-uri');
      if (!uri_apo) {
        let error_msg = $('#AutoCancelMsg').text();
        $('#cancelModalBody').text(error_msg);
        $('#cancelModal').modal('show');
      }
      let act_ver = $('.cur_step').data('action-version');
      let post_data = {
          commond: $('#input-comment').val(),
          action_version: act_ver
      };
      uri_apo = uri_apo+"/rejectOrReturn/0";
      $.ajax({
          url: uri_apo,
          method: 'POST',
          async: true,
          contentType: 'application/json',
          data: JSON.stringify(post_data),
          success: function (data, status) {
              if (0 == data.code) {
                  if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
                      document.location.href = data.data.redirect;
                  } else {
                      document.location.reload(true);
                  }
              } else if (-2 == data.code) {
                  let error_msg = $('#AutoCancelMsg').text();
                  $('#cancelModalBody').text(error_msg);
                  $('#cancelModal').modal('show');
              } else {
                  endLoading(_this);
                  alert(data.msg);
              }
          },
          error: function (jqXHR, status) {
            if (-2 == jqXHR.responseJSON.code) {
              let error_msg = $('#AutoCancelMsg').text();
              $('#cancelModalBody').text(error_msg);
              $('#cancelModal').modal('show');
            } else if(-1 == jqXHR.responseJSON.code) {
              endLoading(_this);
              alert(jqXHR.responseJSON.msg);
            } else {
              endLoading(_this);
              alert('server error');
            }
          }
      });
  });

  $('#btn-return').on('click', function () {
      let _this = $(this);
      startLoading(_this);
      let uri_apo = $('.cur_step').data('next-uri');
      if (!uri_apo) {
        let error_msg = $('#AutoCancelMsg').text();
        $('#cancelModalBody').text(error_msg);
        $('#cancelModal').modal('show');
      }
      let act_ver = $('.cur_step').data('action-version');
      let post_data = {
          commond: $('#input-comment').val(),
          action_version: act_ver
      };
      uri_apo = uri_apo+"/rejectOrReturn/1";
      $.ajax({
          url: uri_apo,
          method: 'POST',
          async: true,
          contentType: 'application/json',
          data: JSON.stringify(post_data),
          success: function (data, status) {
              if (0 == data.code) {
                  if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
                      document.location.href = data.data.redirect;
                  } else {
                      document.location.reload(true);
                  }
              } else if (-2 == data.code) {
                  let error_msg = $('#AutoCancelMsg').text();
                  $('#cancelModalBody').text(error_msg);
                  $('#cancelModal').modal('show');
              } else {
                  endLoading(_this);
                  alert(data.msg);
              }
          },
          error: function (jqXHR, status) {
            if (-2 == jqXHR.responseJSON.code) {
              let error_msg = $('#AutoCancelMsg').text();
              $('#cancelModalBody').text(error_msg);
              $('#cancelModal').modal('show');
            } else if (-1 == jqXHR.responseJSON.code) {
              endLoading(_this);
              alert(jqXHR.responseJSON.msg);
            } else {
              endLoading(_this)
              alert('server error');
            }
          }
      });
  });

  $('#link_record_detail').on('click', function () {
    $('#myModal').modal('show');
  })
})

//Item Link
function searchResItemLinkCtrl($scope, $rootScope, $http, $location) {
  $('#btnContinue').on('click', function () {
    let activity_id = $("#activity_id").text().trim();
    let action_id = $("#hide-actionId").text().trim();
    let cancel_uri = '/workflow/activity/action/' + activity_id + '/' + action_id + '/cancel'
    let cancel_data = {
      commond: 'Auto cancel because workflow setting be changed.',
      action_version: '',
      pid_value: ''
    };
    $.ajax({
      method: 'POST',
      url: cancel_uri,
      async: true,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(cancel_data),
      success: function (data, textStatus) {
        if (data && data.code == 0) {
          document.location.href = '/workflow';
        } else {
          alert(data.msg);
        }
      },
      error: function (jqXHR, textStatus, errorThrown) {
        if (jqXHR.responseJSON && jqXHR.responseJSON.code == -1){
          alert(jqXHR.responseJSON.msg);
        }else {
          alert('Server error.');
        }
      }
    });
  });

  /**
   * Start Loading
   * @param actionButton
   */
  $scope.startLoading = function (actionButton) {
    actionButton.prop('disabled', true);
    $(".lds-ring-background").removeClass("hidden");
  }

  /**
   * End Loading
   * @param actionButton
   */
  $scope.endLoading = function (actionButton) {
    actionButton.removeAttr("disabled");
    $(".lds-ring-background").addClass("hidden");
  }
  $scope.link_item_list = [];
  $scope.sele_options = [
    { id: "relateTo", content: "relateTo" },
    { id: "isVersionOf", content: "isVersionOf" },
    { id: "hasVersion", content: "hasVersion" },
    { id: "isReplacedBy", content: "isReplacedBy" },
    { id: "replaces", content: "replaces" },
    { id: "isRequiredBy", content: "isRequiredBy" },
    { id: "requires", content: "requires" },
    { id: "isPartOf", content: "isPartOf" },
    { id: "hasPart", content: "hasPart" },
    { id: "isReferencedBy", content: "isReferencedBy" },
    { id: "references", content: "references" },
    { id: "isFormatOf", content: "isFormatOf" },
    { id: "hasFormat", content: "hasFormat" },
    { id: "isSupplementTo", content: "isSupplementTo" },
    { id: "isSupplementedBy", content: "isSupplementedBy" },
    { id: "isIdenticalTo", content: "isIdenticalTo" },
    { id: "isDerivedFrom", content: "isDerivedFrom" },
    { id: "isSourceOf", content: "isSourceOf" },
    { id: "isCitedBy", content: "isCitedBy" },
    { id: "Cites", content: "Cites" }
  ];

//   add button
  $rootScope.add_link = function(data, index) {
    let sub_data = {
      item_id: 0,
      item_title: "",
      sele_id: ""
    };

    sub_data.sele_id = "relateTo";
    sub_data.item_id = data.metadata.control_number;
    sub_data.item_title = data.metadata.title[0];
    $scope.link_item_list.push(sub_data);
  };

//   add ex_item_link
  $scope.add_ex_link = function (data) {
    let item_data = {
      item_id: "",
      item_title: "",
      sele_id: ""
    };

    item_data.sele_id = data.value;
    item_data.item_id = data.item_links;
    item_data.item_title = data.item_title;
    $scope.link_item_list.push(item_data);
  };

//   delete button
  $scope.del_link = function(index){
    $scope.link_item_list.splice(index, 1);
  };

//   back button
  $scope.btn_back = function() {
    let backButton = $("#item-link-back-btn");
    $scope.startLoading(backButton);
    var post_url = $('.cur_step').data('next-uri');
    if (!post_url) {
      let error_msg = $('#AutoCancelMsg').text();
      $('#cancelModalBody').text(error_msg);
      $('#cancelModal').modal('show');
    }
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $('.cur_step').data('action-version')
    };
    post_url = post_url + "/rejectOrReturn/0";
    $.ajax({
      url: post_url,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function (data, status) {
        if (0 == data.code) {
          if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href = data.data.redirect;
          } else {
            let origin = new URL(window.location.href).origin;
            let redirect_uri = origin + "/workflow/activity/detail/" + $("#activity_id").text().trim();
            document.location.href = redirect_uri;
          }
        } else if (-2 == data.code) {
          let error_msg = $('#AutoCancelMsg').text();
          $('#cancelModalBody').text(error_msg);
          $('#cancelModal').modal('show');
        } else {
          endLoading(_this);
          alert(data.msg);
        }
      },
      error: function (jqXHR, status) {
        if (-2 == jqXHR.responseJSON.code) {
          let error_msg = $('#AutoCancelMsg').text();
          $('#cancelModalBody').text(error_msg);
          $('#cancelModal').modal('show');
        } else if (-1 == jqXHR.responseJSON.code) {
          endLoading(_this);
          alert(jqXHR.responseJSON.msg);
        } else{
          endLoading(_this);
          alert('server error');
        }
      }
    });
  };

//   save button
  $scope.btn_save = function () {
    let saveButton = $("#item-link-save-btn");
    $scope.startLoading(saveButton);
    var post_url = $('.cur_step').data('next-uri');
    if (!post_url) {
      let error_msg = $('#AutoCancelMsg').text();
      $('#cancelModalBody').text(error_msg);
      $('#cancelModal').modal('show');
    }
    var post_data = {
      commond: $("#input-comment").val(),
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 1,
      link_data: $scope.link_item_list
    };
    $http({
      method: 'POST',
      url: post_url,
      data: post_data,
      headers: { 'Content-Type': 'application/json' },
    }).then(function successCallback(response) {
      if (0 == response.data.code) {
        if (response.data.hasOwnProperty('data') && response.data.data.hasOwnProperty('redirect')) {
          document.location.href = response.data.data.redirect;
        } else {
          document.location.reload(true);
        }
      } else if (-2 == response.data.code) {
        let error_msg = $('#AutoCancelMsg').text();
        $('#cancelModalBody').text(error_msg);
        $('#cancelModal').modal('show');
      } else {
        $scope.endLoading(saveButton);
        alert(response.data.msg);
      }
    }, function errorCallback(response) {
      $scope.endLoading(saveButton);
      alert(response.data.msg);
      document.location.reload(true);
    });
  };
//   run button
  $scope.btn_run=function(){
    let runButton = $("#item-link-run-btn");
    $scope.startLoading(runButton);
    var post_url = $('.cur_step').data('next-uri');
    if (!post_url) {
      let error_msg = $('#AutoCancelMsg').text();
      $('#cancelModalBody').text(error_msg);
      $('#cancelModal').modal('show');
    }
    var post_data = {
      commond: $("#input-comment").val(),
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 0,
      link_data: $scope.link_item_list
    };
    $scope.isDisabledRun = true;
    $http({
        method: 'POST',
        url: post_url,
        data: post_data,
        headers: {'Content-Type': 'application/json'},
    }).then(function successCallback(response) {
      if (0 === response.data.code) {
        if (response.data.hasOwnProperty('data') && response.data.data.hasOwnProperty('redirect')) {
          document.location.href = response.data.data.redirect;
        } else if (window.location.href.indexOf('/workflow/activity/detail') === -1) {
          let community_id = $('#community_id').text();
          let redirectUrl = "/workflow/activity/detail/" + $("#activity_id").text().trim();
          if (community_id) {
            redirectUrl += '?c=' + community_id;
          }
          parent.document.location.href = redirectUrl;
        } else {
          document.location.reload(true);
        }
      } else if (-2 === response.data.code) {
        let error_msg = $('#AutoCancelMsg').text();
        $('#cancelModalBody').text(error_msg);
        $('#cancelModal').modal('show');
      } else {
        $scope.endLoading(runButton);
        alert(response.data.msg);
      }
    }, function errorCallback(response) {
      $scope.endLoading(runButton);
        alert(response.data.msg);
        document.location.reload(true);
    });
  };

// init ex-item links
  $(document).ready(function () {
    let ex_item_links = $("#ex_item_links").val();

    if (ex_item_links !== "" && typeof ex_item_links !== "undefined") {
      json = JSON.parse(ex_item_links);

      json.forEach(function (key) {
        $scope.add_ex_link(key);
      });
    }
  });
}

angular.module('invenioSearch')
  .controller('searchResItemLinkCtrl', searchResItemLinkCtrl);

angular.module('invenioSearch').config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{[');
  $interpolateProvider.endSymbol(']}');
}]);
