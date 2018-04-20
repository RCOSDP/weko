require([
  'jquery',
  'bootstrap'
],function () {
  $("#item-type-lists").change(function (ev) {
    window.location.href = '/items/' + $(this).val();
  });
});

(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function() {
    angular.module('wekoRecords.controllers', []);
    function WekoRecordsCtrl($scope, $rootScope, $modal, InvenioRecordsAPI){
      $scope.items = [ 'item1', 'item2', 'item3' ];
      $scope.searchAuthor = function(model_id,arrayFlg) {
        // add by ryuu. start 20180410
        $("#btn_id").text(model_id);
        $("#array_flg").text(arrayFlg);
        // add by ryuu. end 20180410
        $('#myModal').modal('show');
        /*
        $rootScope.recordsVM.invenioRecordsModel[model_id] = '123';
        $rootScope.recordsVM.invenioRecordsModel['item_1522722977216'] =
          {"subitem_1522722931599":[{"subitem_1522722942322":"1"},{"subitem_1522722942322":"2"}],"subitem_1522722919975":"1","subitem_1522722927207":"1"};
        var modalInstance = $modal.open({
          templateUrl : '/static/templates/weko_items_ui/myModalContent.html',
          controller : ModalInstanceCtrl,
          resolve : {
            items : function() {
              return $scope.items;
            }
          }
        });
        modalInstance.opened.then(function() {
          console.log('modal is opened');
        });
        modalInstance.result.then(function(result) {
          console.log(result);
          $rootScope.recordsVM.invenioRecordsModel[model_id] = result;
        }, function(reason) {
          console.log(reason);
        });*/
      }
      // add by ryuu. start 20180410
      $scope.setAuthorInfo = function() {
         var authorInfo = $('#author_info').text();
         var arrayFlg = $('#array_flg').text();
         var modelId = $('#btn_id').text();
         var authorInfoObj = JSON.parse(authorInfo);
         var updateIndex = 0;
         if(arrayFlg == 'true'){
           if(authorInfoObj[0].hasOwnProperty('affiliation')){
             $rootScope.recordsVM.invenioRecordsModel[modelId][0].affiliation = authorInfoObj[0].affiliation;
           }
           if(authorInfoObj[0].hasOwnProperty('creatorAlternatives')){
             $rootScope.recordsVM.invenioRecordsModel[modelId][0].creatorAlternatives = authorInfoObj[0].creatorAlternatives;
           }
           if(authorInfoObj[0].hasOwnProperty('creatorNames')){
             $rootScope.recordsVM.invenioRecordsModel[modelId][0].creatorNames = authorInfoObj[0].creatorNames;
           }else{
             $rootScope.recordsVM.invenioRecordsModel[modelId][0].creatorNames = {};
           }
           if(authorInfoObj[0].hasOwnProperty('familyNames')){
             $rootScope.recordsVM.invenioRecordsModel[modelId][0].familyNames = authorInfoObj[0].familyNames;
           }else{
             $rootScope.recordsVM.invenioRecordsModel[modelId][0].familyNames = {};
           }
           if(authorInfoObj[0].hasOwnProperty('givenNames')){
             $rootScope.recordsVM.invenioRecordsModel[modelId][0].givenNames = authorInfoObj[0].givenNames;
           }else{
             $rootScope.recordsVM.invenioRecordsModel[modelId][0].givenNames = {};
           }
           if(authorInfoObj[0].hasOwnProperty('nameIdentifiers')){
             $rootScope.recordsVM.invenioRecordsModel[modelId][0].nameIdentifiers = authorInfoObj[0].nameIdentifiers;
           }

//          $rootScope.recordsVM.invenioRecordsModel[modelId][0]=authorInfoObj[0];
         }else{
             if(authorInfoObj[0].hasOwnProperty('affiliation')){
               $rootScope.recordsVM.invenioRecordsModel[modelId].affiliation = authorInfoObj[0].affiliation;
             }
             if(authorInfoObj[0].hasOwnProperty('creatorAlternatives')){
               $rootScope.recordsVM.invenioRecordsModel[modelId].creatorAlternatives = authorInfoObj[0].creatorAlternatives;
             }
             if(authorInfoObj[0].hasOwnProperty('creatorNames')){
               $rootScope.recordsVM.invenioRecordsModel[modelId].creatorNames = authorInfoObj[0].creatorNames;
             }else{
               $rootScope.recordsVM.invenioRecordsModel[modelId].creatorNames = {};
             }
             if(authorInfoObj[0].hasOwnProperty('familyNames')){
               $rootScope.recordsVM.invenioRecordsModel[modelId].familyNames = authorInfoObj[0].familyNames;
             }else{
               $rootScope.recordsVM.invenioRecordsModel[modelId].familyNames = {};
             }
             if(authorInfoObj[0].hasOwnProperty('givenNames')){
               $rootScope.recordsVM.invenioRecordsModel[modelId].givenNames = authorInfoObj[0].givenNames;
             }else{
               $rootScope.recordsVM.invenioRecordsModel[modelId].givenNames = {};
             }
             if(authorInfoObj[0].hasOwnProperty('nameIdentifiers')){
               $rootScope.recordsVM.invenioRecordsModel[modelId].nameIdentifiers = authorInfoObj[0].nameIdentifiers;
             }
//            $rootScope.recordsVM.invenioRecordsModel[modelId]=authorInfoObj[0];
         }
         //画面にデータを設定する
         $("#btn_id").text('');
         $("#author_info").text('');
         $("#array_flg").text('');
      }
      // add by ryuu. end 20180410
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
        'mgcrea.ngStrap.modal', 'pascalprecht.translate', 'ui.select',
        'mgcrea.ngStrap.select', 'invenioFiles'
      ]
    );
  });
})(angular);
