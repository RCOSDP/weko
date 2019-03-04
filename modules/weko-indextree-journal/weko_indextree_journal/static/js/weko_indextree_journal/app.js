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
      if (invalidFlg) {
        var page_info = {
          cur_journal_id: 0,
          cur_index_id: 0,
          send_method: 'POST'
        }
        page_info.cur_journal_id = $rootScope.recordsVM.invenioRecordsModel.id;
        page_info.cur_index_id = $rootScope.recordsVM.invenioRecordsModel.index_id;

        if(page_info.cur_journal_id != '0') {
          page_info.send_method = "PUT";
        }
        var request = {
          url: '/api/indextree/journal/'+page_info.cur_index_id,
          method: page_info.send_method,
          headers: {
            'Content-Type': 'application/json'
          },
          data: JSON.stringify($rootScope.recordsVM.invenioRecordsModel)
        };
        InvenioRecordsAPI.request(request).then(
          function success(response){
            alert(response.data.message);
          },
          function error(response){
            alert(response.data.message);
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
