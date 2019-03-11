require([
  'jquery',
  'bootstrap'
],function () {
  $('#weko_id_hidden').hide();
  $("#item-type-lists").change(function (ev) {
    window.location.href = '/items/' + $(this).val();
  });
  $("#btnModalClose").click(function () {
    $('#myModal').modal('toggle');
    $("div.modal-backdrop").remove();
  });

  $("#meta-search-close").click(function () {
    $('#meta-search').modal('toggle');
    $("div.modal-backdrop").remove();
  });

});

(function (angular) {
  // Bootstrap it!
  angular.element(document).ready(function() {
    angular.module('wekoRecords.controllers', []);
    function WekoRecordsCtrl($scope, $rootScope, $modal, InvenioRecordsAPI){
//      $scope.items = [ 'item1', 'item2', 'item3' ];
      $scope.filemeta_key = '';
      $scope.filemeta_form_idx = -1;

      $scope.searchFilemetaKey = function() {
          if($scope.filemeta_key.length > 0) {
            return $scope.filemeta_key;
          }
          Object.entries($rootScope.recordsVM.invenioRecordsSchema.properties).forEach(
            ([key, value]) => {
              if(value.type == 'array') {
                if(value.items.properties.hasOwnProperty('filename')) {
                  $scope.filemeta_key = key;
                }
              }
            }
          );
      }
      $scope.findFilemetaFormIdx = function() {
          if($scope.filemeta_form_idx >= 0) {
            return $scope.filemeta_form_idx;
          }
          $rootScope.recordsVM.invenioRecordsForm.forEach(
            (element, index) => {
              if(element.hasOwnProperty('key')
                  && element.key == $scope.filemeta_key) {
                $scope.filemeta_form_idx = index;
              }
            }
          );
      }
      $scope.initFilenameList = function() {
        $scope.searchFilemetaKey();
        $scope.findFilemetaFormIdx();
        filemeta_schema = $rootScope.recordsVM.invenioRecordsSchema.properties[$scope.filemeta_key];
        filemeta_schema.items.properties['filename']['enum'] = [];
        filemeta_form = $rootScope.recordsVM.invenioRecordsForm[$scope.filemeta_form_idx];
        filemeta_filename_form = filemeta_form.items[0];
        filemeta_filename_form['titleMap'] = [];
        $rootScope.filesVM.files.forEach(file => {
          if(file.completed) {
            filemeta_schema.items.properties['filename']['enum'].push(file.key);
            filemeta_filename_form['titleMap'].push({name: file.key, value: file.key});
          }
        });
        $rootScope.$broadcast('schemaFormRedraw');
      }

      $rootScope.$on('invenio.records.loading.stop', function(ev){
        $scope.initFilenameList();
        hide_endpoints = $('#hide_endpoints').text()
        if(hide_endpoints.length > 2) {
          endpoints = JSON.parse($('#hide_endpoints').text());
          if(endpoints.hasOwnProperty('bucket')) {
            $rootScope.$broadcast(
              'invenio.records.endpoints.updated', endpoints
            );
          }
        }
      });
      $rootScope.$on('invenio.uploader.upload.completed', function(ev){
        $scope.initFilenameList();
      });
      $scope.$on('invenio.uploader.file.deleted', function(ev, f){
        $scope.initFilenameList();
      });

      $scope.getItemMetadata = function(model_id,arrayFlg,form) {
        $('#meta-search').modal('show');
      }

      $scope.setValueToField = function(id, value){
        $('#'+id).val(value);
      }

      $scope.setItemMetadata = function() {
        let autoFillID = $('#autofill_id_type').val();
        let value = $('#autofill_item_id').val();
        let itemTypeId = $("#autofill_item_type_id").val();
        if (autoFillID === 'Default'){
          alert('Please select the ID');
          return;
        } else if (!value.length){
          alert('Please input valid value');
          return;
        }

        let param = {
          api_type: autoFillID,
          search_data: value,
          item_type_id: itemTypeId
        }
        // Create requet
        let request = $.ajax({
          url: '/api/autofill/crossref_api',
          headers: {
            'Content-Type': 'application/json'
          },
          async: false,
          method: "POST",
          data: JSON.stringify(param),
          dataType: "json",
          success: (data, status)=>{
            console.log(data.items);
            let items = data.items;
            let value = 'dummy data';
            if (items.hasOwnProperty('creator')) {
              if (items.creator.hasOwnProperty('affiliation')) {
                if (items.creator.affiliation.hasOwnProperty('affiliationName')) {
                  let id = items.creator.affiliation.affiliationName;
                  this.setValueToField(id['@attributes']['xml:lang'], 'en');
                  this.setValueToField(id['@value'], value);
                  // $rootScope.recordsVM.invenioRecordsModel[id['@value']] = fieldData;
                }
                if (items.creator.affiliation.hasOwnProperty('nameIdentifier')) {
                  let id = items.creator.affiliation.nameIdentifier;
                  this.setValueToField(id['@attributes']['nameIdentifierScheme'], 'AID');
                  this.setValueToField(id['@attributes']['nameIdentifierURI'], value);
                  this.setValueToField(id['@value'], value);
                }
              }
              if (items.creator.hasOwnProperty('creatorAlternative')) {
                let id = items.creator.creatorAlternative;
                this.setValueToField(id['@attributes']['xml:lang'], 'en');
                this.setValueToField(id['@value'], value);
              }
              if (items.creator.hasOwnProperty('creatorName')) {
                let id = items.creator.creatorName;
                this.setValueToField(id['@attributes']['xml:lang'], 'en');
                this.setValueToField(id['@value'], value);
              }
              if (items.creator.hasOwnProperty('familyName')) {
                let id = items.creator.familyName;
                this.setValueToField(id['@attributes']['xml:lang'], 'en');
                this.setValueToField(id['@value'], value);
              }
              if (items.creator.hasOwnProperty('givenName')) {
                let id = items.creator.givenName;
                this.setValueToField(id['@attributes']['xml:lang'], 'en');
                this.setValueToField(id['@value'], value);
              }
              if (items.creator.hasOwnProperty('nameIdentifier')) {
                let id = items.creator.nameIdentifier;
                  this.setValueToField(id['@attributes']['nameIdentifierScheme'], 'AID');
                  this.setValueToField(id['@attributes']['nameIdentifierURI'], value);
                  this.setValueToField(id['@value'], value);
              }
            }
            if (items.hasOwnProperty('date')){
              let id = items.date;
              this.setValueToField(id['@attributes']['dateType'], value);
              this.setValueToField(id['@value'], value);
            }
            if (items.hasOwnProperty('language')) {
              this.setValueToField(items.language['@value'], value);
            }
            if (items.hasOwnProperty('numPages')) {
              this.setValueToField(items.numPages['@value'], value);
            }
            if (items.hasOwnProperty('pageStart')) {
              this.setValueToField(items.pageStart['@value'], value);
            }
            if (items.hasOwnProperty('pageEnd')) {
              this.setValueToField(items.pageEnd['@value'], value);
            }
            if (items.hasOwnProperty('publisher')) {
              let id = items.publisher;
              this.setValueToField(id['@attributes']['xml:lang'], value);
              this.setValueToField(id['@value'], value);
            }
            if (items.hasOwnProperty('relation')) {
              let relation = items.relation;
              this.setValueToField(relation['@attributes']['relationType'], value);
              if (relation.hasOwnProperty('relatedIdentifier')) {
                let id = relation.relatedIdentifier;
                this.setValueToField(id['@attributes']['identifierType'], value);
                this.setValueToField(id['@value'], value);
              }
              if (relation.hasOwnProperty('relatedTitle')) {
                let id = relation.relatedTitle;
                this.setValueToField(id['@attributes']['xml:lang'], value);
                this.setValueToField(id['@value'], value);
              }
            }
            if (items.hasOwnProperty('title')) {
              let id = items.title;
              this.setValueToField(id['@attributes']['xml:lang'], value);
              this.setValueToField(id['@value'], value);
            }
            $('#meta-search').modal('toggle');
          }
        });
        // // Request sucess
        // request.done((data) => {
        //   console.log(data.items);
        //   let items = data.items;
        //   let value = data.result;
        //   console.log(0.1);
        //   if (items.hasOwnProperty('creator')) {
        //     console.log(1);
        //     if (items.creator.hasOwnProperty('affiliation')) {
        //       console.log(2);
        //       if (items.creator.affiliation.hasOwnProperty('affiliationName')) {
        //         console.log(3);
        //         let id = items.creator.affiliation.affiliationName;
        //         let fieldData = "affiliation"
        //         console.log(id['@attributes']['xml:lang']+"---"+fieldData+' language');
        //         console.log(id['@value']);
        //         this.setValueToField(id['@attributes']['xml:lang'], 'en');
        //         this.setValueToField(id['@value'], fieldData);
        //         $rootScope.recordsVM.invenioRecordsModel[id['@value']] = fieldData;
        //       }
        //     }
        //     $('#meta-search').modal('toggle');
        //   }
        // });
        // // Request fail
        // request.fail((jqXHR, textStatus) => {
        //   console.log(jqXHR);
        //   alert("Request failed: " + textStatus);
        // });



        // $.ajax({
        //   method: 'GET',
        //   url: '/api/autofill/search/' + param,
        //   async: false,
        //   success: function(data, status){
        //     // Title
        //     $rootScope.recordsVM.invenioRecordsModel[data.items.sourceTitle] = data.data.sourceTitle;
        //     $rootScope.recordsVM.invenioRecordsModel[data.items.title] = data.data.title;
        //     // Languages
        //     $rootScope.recordsVM.invenioRecordsModel[data.items.language] = data.data.language;
        //     // PublicationDate
        //     $rootScope.recordsVM.invenioRecordsModel[data.items.date] = data.data.date;
        //     // Author
        //     $rootScope.recordsVM.invenioRecordsModel[data.items.creator] = data.data.creator;
        //     // Number of page
        //     $rootScope.recordsVM.invenioRecordsModel[data.items.pageEnd] = data.data.pageEnd;
        //     // Publisher
        //     $rootScope.recordsVM.invenioRecordsModel[data.items.publisher] = data.data.publisher;
        //     // ISBN
        //     $rootScope.recordsVM.invenioRecordsModel[data.items.relatedIdentifier] = data.data.relatedIdentifier;

        //     $('#meta-search').modal('toggle');

        //   },
        //   error: function(status, error){
        //     alert(error);
        //     console.log(error);
        //   }
        // });


      }

      $scope.searchSource = function(model_id,arrayFlg,form) {

        alert(form.key[1]);

      }


      $scope.searchAuthor = function(model_id,arrayFlg,form) {
        // add by ryuu. start 20180410
        $("#btn_id").text(model_id);
        $("#array_flg").text(arrayFlg);
        $("#array_index").text(form.key[1]);
        // add by ryuu. end 20180410
        $('#myModal').modal('show');
      }
      // add by ryuu. start 20180410
      $scope.setAuthorInfo = function() {
         var authorInfo = $('#author_info').text();
         var arrayFlg = $('#array_flg').text();
         var modelId = $('#btn_id').text();
         var array_index = $('#array_index').text();
         var authorInfoObj = JSON.parse(authorInfo);
         var updateIndex = 0;
         if(arrayFlg == 'true'){
//            $rootScope.recordsVM.invenioRecordsModel[modelId].push(authorInfoObj[0]);
//              $rootScope.recordsVM.invenioRecordsModel[modelId][array_index]= authorInfoObj[0];
//            2018/05/28 start
　　　　　　　var familyName ="";
              var givenName = "";
              if(authorInfoObj[0].hasOwnProperty('affiliation')){
                 $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].affiliation = authorInfoObj[0].affiliation;
               }
               if(authorInfoObj[0].hasOwnProperty('creatorAlternatives')){
                 $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].creatorAlternatives = authorInfoObj[0].creatorAlternatives;
               }

               if(authorInfoObj[0].hasOwnProperty('creatorNames')){
                 $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].creatorNames = authorInfoObj[0].creatorNames;
               }

               if(authorInfoObj[0].hasOwnProperty('familyNames')){
                 $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].familyNames = authorInfoObj[0].familyNames;
                 if($rootScope.recordsVM.invenioRecordsModel[modelId][array_index].familyNames.length == 1){
                    familyName = authorInfoObj[0].familyNames[0].familyName;
                 }
               }else{
                 $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].familyNames = {"familyName": "","lang": ""};
               }
               if(authorInfoObj[0].hasOwnProperty('givenNames')){
                 $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].givenNames = authorInfoObj[0].givenNames;
                 if($rootScope.recordsVM.invenioRecordsModel[modelId][array_index].givenNames.length == 1){
                    givenName = authorInfoObj[0].givenNames[0].givenName;
                 }
               }else{
                 $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].givenNames = {"givenName": "","lang": ""};
               }

               if(authorInfoObj[0].hasOwnProperty('familyNames')&&authorInfoObj[0].hasOwnProperty('givenNames')){
                 if(!authorInfoObj[0].hasOwnProperty('creatorNames')){
                   $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].creatorNames = [];
                 }
                 for(var i=0;i<authorInfoObj[0].familyNames.length;i++){
                   var subCreatorName = {"creatorName":"","lang":""};
                   subCreatorName.creatorName = authorInfoObj[0].familyNames[i].familyName + "　"+authorInfoObj[0].givenNames[i].givenName;
                   subCreatorName.lang = authorInfoObj[0].familyNames[i].lang;
                   $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].creatorNames.push(subCreatorName);
                 }
               }

               if(authorInfoObj[0].hasOwnProperty('nameIdentifiers')){
                 $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].nameIdentifiers = authorInfoObj[0].nameIdentifiers;
               }

               var weko_id = $('#weko_id').text();
               $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].weko_id= weko_id;
               $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].weko_id_hidden= weko_id;
               $rootScope.recordsVM.invenioRecordsModel[modelId][array_index].authorLink=['check'];
//            2018/05/28 end
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

             var weko_id = $('#weko_id').text();
             $rootScope.recordsVM.invenioRecordsModel[modelId].weko_id= weko_id;
             $rootScope.recordsVM.invenioRecordsModel[modelId].weko_id_hidden= weko_id;
             $rootScope.recordsVM.invenioRecordsModel[modelId].authorLink=['check'];

         }
         //画面にデータを設定する
         $("#btn_id").text('');
         $("#author_info").text('');
         $("#array_flg").text('');
      }
      // add by ryuu. end 20180410
      $scope.updated=function(model_id,modelValue,form,arrayFlg){
//        2018/05/28 start

         if(arrayFlg){
            var array_index = form.key[1];
            if(modelValue == true){
              $rootScope.recordsVM.invenioRecordsModel[model_id][array_index].weko_id= $rootScope.recordsVM.invenioRecordsModel[model_id][array_index].weko_id_hidden;
            }else{
  　　　　　　delete $rootScope.recordsVM.invenioRecordsModel[model_id][array_index].weko_id;
            }
          }else{
            if(modelValue == true){
              $rootScope.recordsVM.invenioRecordsModel[model_id].weko_id= $rootScope.recordsVM.invenioRecordsModel[model_id].weko_id_hidden;
            }else{
  　　　　　　delete $rootScope.recordsVM.invenioRecordsModel[model_id].weko_id;
            }
          }
//        2018/05/28 end
      }
//    authorLink condition
      $scope.linkCondition=function(val){
        var linkStus = val.hasOwnProperty('authorLink');
        if(linkStus){
          return true;
        }else{
          return false;
        }
      }
//    authorId condition
      $scope.idCondition=function(val){
        var c = val.hasOwnProperty('authorLink');
        if(!c){
          return false;
        }else{
          return true;
        }
      }
      $scope.updateDataJson = function(){
        var str = JSON.stringify($rootScope.recordsVM.invenioRecordsModel);
        var indexOfLink = str.indexOf("authorLink");
        if(indexOfLink != -1){
          str = str.split(',"authorLink":[]').join('');
        }
        $rootScope.recordsVM.invenioRecordsModel = JSON.parse(str);
      }
      $scope.saveDataJson = function(item_save_uri){
        var metainfo = {'metainfo': $rootScope.recordsVM.invenioRecordsModel};
        if(!angular.isUndefined($rootScope.filesVM)) {
          metainfo = angular.merge(
            {},
            metainfo,
            {
              'files': $rootScope.filesVM.files,
              'endpoints': $rootScope.filesVM.invenioFilesEndpoints
            }
          );
        }
        var request = {
          url: item_save_uri,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          data: JSON.stringify(metainfo)
        };
        InvenioRecordsAPI.request(request).then(
          function success(response){
            alert(response.data.msg);
          },
          function error(response){
            alert(response);
          }
        );
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
