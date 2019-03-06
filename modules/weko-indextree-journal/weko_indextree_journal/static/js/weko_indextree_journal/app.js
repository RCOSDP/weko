require([
  "jquery",
  "bootstrap"
], function() {
});

(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function() {
  angular.module('wekoRecords.controllers', []);

  function WekoRecordsCtrl($scope, $rootScope, $modal, InvenioRecordsAPI){
    $scope.saveData = function(){
      // Broadcast an event so all fields validate themselves
      $scope.$broadcast('schemaFormValidate');
      var invalidFlg = $('form[name="depositionForm"]').hasClass("ng-invalid");
      if (!invalidFlg) {
        var page_info = {
          cur_journal_id: 0,
          cur_index_id: 0,
          send_method: 'POST'
        }
        if($('#right_index_id').val() != '') {
          page_info.cur_index_id = $('#right_index_id').val();
        }
        if($('#journal_id').val() != '' && $('#journal_id').val() != 'None') {
          page_info.cur_journal_id = $('#journal_id').val();
        }
        var data = {
          id: page_info.cur_index_id,
          index_id: page_info.cur_index_id,
          is_output: $("input[name='is_output']:checked").val() || true,
          publication_title: $('#publication_title').val() || '',
          print_identifier: $('#print_identifier').val() || '',
          online_identifier: $('#online_identifier').val() || '',
          date_first_issue_online: $('input[name=date_first_issue_online]').val() || '',
          num_first_vol_online: $('#num_first_vol_online').val() || '',
          num_first_issue_online: $('#num_first_issue_online').val() || '',
          date_last_issue_online: $('input[name=date_last_issue_online]').val() || '',
          num_last_vol_online: $('#num_last_vol_online').val() || '',
          num_last_issue_online: $('#num_last_issue_online').val() || '',
          embargo_info: $('#embargo_info').val() || '',
          coverage_depth: $('select[name=coverage_depth]').val() || '',
          coverage_notes: $('#coverage_notes').val() || '',
          publisher_name: $('#publisher_name').val() || '',
          publication_type: $('select[name=publication_type]').val() || '',
          parent_publication_title_id: $('#parent_publication_title_id').val() || null,
          preceding_publication_title_id: $('#preceding_publication_title_id').val() || null,
          access_type: $('select[name=access_type]').val() || '',
          language: $('select[name=language]').val() || '',
          title_alternative: $('#title_alternative').val() || '',
          title_transcription: $('#title_transcription').val() || '',
          ncid: $('#ncid').val() || '',
          ndl_callno: $('#ndl_callno').val() || '',
          ndl_bibid: $('#ndl_bibid').val() || '',
          jstage_code: $('#jstage_code').val() || '',
          ichushi_code: $('#ichushi_code').val() || ''
        }
        $.extend( data, $rootScope.recordsVM.invenioRecordsModel );
        data.parent_publication_title_id = data.parent_publication_title_id || null;
        data.preceding_publication_title_id = data.preceding_publication_title_id || null;

        if(page_info.cur_journal_id != '0') {
          page_info.send_method = "PUT";
        }
        var request = {
          url: '/api/indextree/journal/'+page_info.cur_index_id,
          method: page_info.send_method,
          headers: {
            'Content-Type': 'application/json'
          },
          data: JSON.stringify(data)
        };
        InvenioRecordsAPI.request(request).then(
          function success(response){
            if (!$('form[name="depositionForm"]').hasClass("ng-invalid")) {
              alert(response.data.message);
            }
          },
          function error(response){
            if (!$('form[name="depositionForm"]').hasClass("ng-invalid")) {
              alert(response.data.message);
            }
          }
        );
      }
    }
  }

  // Inject depedencies
  WekoRecordsCtrl.$inject = [
    '$scope',
    '$rootScope',
    '$modal',
    'InvenioRecordsAPI',
  ];
  angular.module('wekoRecords.controllers')
    .controller('WekoRecordsCtrl', WekoRecordsCtrl);

  var ModalInstanceCtrl = function($scope, $modalInstance, items) {
    $scope.items = items;
    $scope.searchKey = '';
    $scope.selected = {
      item : $scope.items[0]
    };
    $scope.ok = function() {
      $modalInstance.close($scope.selected);
    };
    $scope.cancel = function() {
      $modalInstance.dismiss('cancel');
    };
    $scope.search = function() {
      $scope.items.push($scope.searchKey);
    }
  };

  angular.module('wekoRecords', [
    'invenioRecords',
    'wekoRecords.controllers',
  ]);

  angular.bootstrap(
    document.getElementById('weko-records'), [
      'wekoRecords', 'invenioRecords', 'schemaForm', 'mgcrea.ngStrap',
      'mgcrea.ngStrap.modal', 'pascalprecht.translate', 'ui.sortable',
      'ui.select', 'mgcrea.ngStrap.select', 'mgcrea.ngStrap.datepicker',
      'mgcrea.ngStrap.helpers.dateParser', 'mgcrea.ngStrap.tooltip',
      'invenioFiles'
    ]
  );
});
})(angular);
