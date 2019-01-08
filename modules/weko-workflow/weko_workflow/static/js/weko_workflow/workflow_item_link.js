require([
  "jquery",
  "bootstrap"
], function () {
  $('.btn-begin').on('click', function () {
      let post_uri = $('#post_uri').text();
      let workflow_id = $(this).data('workflow-id');
      let community = $(this).data('community');
      let post_data = {
          workflow_id: workflow_id,
          flow_id: $('#flow_' + workflow_id).data('flow-id'),
          itemtype_id: $('#item_type_' + workflow_id).data('itemtype-id')
      };
      if(community != ""){
        post_uri = post_uri+"?community="+ community;
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
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {}
      });
  });
  $('#btn-finish').on('click', function(){
    let post_uri = $('.cur_step').data('next-uri');
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
        } else {
          alert(data.msg);
        }
      },
      error: function(jqXHE, status) {
        alert('server error');
        $('#myModal').modal('hide');
      }
    });
  });
  $('#btn-draft').on('click', function(){
    let post_uri = $('.cur_step').data('next-uri');
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
        } else {
          alert(data.msg);
        }
      },
      error: function(jqXHE, status) {
        alert('server error');
        $('#myModal').modal('hide');
      }
    });
  });
  $('#btn-approval-req').on('click', function () {
      action_id = $('#hide-actionId').text();
      btn_id = "action_" + action_id;
      $('#' + btn_id).click();
  });
  $('#btn-approval').on('click', function () {
      let uri_apo = $('.cur_step').data('next-uri');
      let act_ver = $('.cur_step').data('action-version');
      let post_data = {
          commond: $('#input-comment').val(),
          action_version: act_ver
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
              } else {
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
              alert('server error');
          }
      });
  });
  $('#btn-reject').on('click', function () {
      let uri_apo = $('.cur_step').data('next-uri');
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
              } else {
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
              alert('server error');
          }
      });
  });
  $('#btn-return').on('click', function () {
      let uri_apo = $('.cur_step').data('next-uri');
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
              } else {
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
              alert('server error');
          }
      });
  });
  $('#lnk_item_detail').on('click', function () {
    $('#myModal').modal('show');
  })
})

//Item Link
function searchResItemLinkCtrl($scope, $rootScope, $http, $location) {
   $scope.link_item_list=[];
   $scope.sele_options=[
                        {id:'relateTo',content:'relateTo'},
                        {id:'isVersionOf',content:'isVersionOf'},
                        {id:'hasVersion',content:'hasVersion'},
                        {id:'isReplaceBy',content:'isReplaceBy'},
                        {id:'replaces',content:'replaces'},
                        {id:'isRequiredBy',content:'isRequiredBy'},
                        {id:'requires',content:'requires'},
                        {id:'isPartOf',content:'isPartOf'},
                        {id:'hasPart',content:'hasPart'},
                        {id:'isReferencedBy',content:'isReferencedBy'},
                        {id:'references',content:'references'},
                        {id:'isFormatOf',content:'isFormatOf'},
                        {id:'hasFormat',content:'hasFormat'},
                        {id:'isSupplementTo',content:'isSupplementTo'},
                        {id:'isSupplementBy',content:'isSupplementBy'},
                        {id:'isIdenticalTo',content:'isIdenticalTo'},
                        {id:'isDeriverdFrom',content:'isDeriverdFrom'},
                        {id:'isSoruceOf',content:'isSoruceOf'},
                       ];
   $scope.comment_data="";
//   add button
   $rootScope.add_link=function(data, index){
    var sub_data={seleOption:[],sele_id:'',item_data:"",item_title:""};
    sub_data.seleOption = angular.copy($scope.sele_options);
    sub_data.sele_id = 'relateTo';
    sub_data.item_data = data;
    sub_data.item_title = data.metadata.title[0];
    $scope.link_item_list.push(sub_data);
   }
//   delete button
   $scope.del_link=function(index){
    $scope.link_item_list.splice(index,1);
   }
//   save button
   $scope.btn_save=function(){
    var post_url = $('.cur_step').data('next-uri');
    var post_data = {
      commond: $scope.comment_data,
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 1
    };

    $http({
        method: 'POST',
        url: post_url,
        data: post_data,
        headers: {'Content-Type': 'application/json'},
    }).then(function successCallback(response) {
      if(0 == response.data.code) {
        if(response.data.hasOwnProperty('data') && response.data.data.hasOwnProperty('redirect')) {
          document.location.href=response.data.data.redirect;
        } else {
          document.location.reload(true);
        }
       }
    }, function errorCallback(response) {
      alert(response.data.msg)
    });
   }
//   run button
   $scope.btn_run=function(){
      var post_url = $('.cur_step').data('next-uri');
      var post_data = {
        commond: $scope.comment_data,
        action_version: $('.cur_step').data('action-version'),
        temporary_save: 0,
        link_data:$scope.link_item_list
      };

      $http({
          method: 'POST',
          url: post_url,
          data: post_data,
          headers: {'Content-Type': 'application/json'},
      }).then(function successCallback(response) {
        if(0 == response.data.code) {
          if(response.data.hasOwnProperty('data') && response.data.data.hasOwnProperty('redirect')) {
            document.location.href=response.data.data.redirect;
          } else {
            document.location.reload(true);
          }
        }
      }, function errorCallback(response) {
         alert(response.data.msg)
      });
    }
}

angular.module('invenioSearch')
  .controller('searchResItemLinkCtrl', searchResItemLinkCtrl);

angular.module('invenioSearch').config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{[');
  $interpolateProvider.endSymbol(']}');
}]);
