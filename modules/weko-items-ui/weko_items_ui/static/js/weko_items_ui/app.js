require([
  //'jquery',
  //'bootstrap'
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

      $scope.getItemMetadata = function () {
        // Reset error message befor open modal.
        this.resetAutoFillErrorMessage();
        $('#meta-search').modal('show');
      }

      $scope.setValueToField = function (id, value) {
        if (!id) {
          return;
        }
        if (!value) {
          // Reset current value
          $scope.depositionForm[id].$setViewValue("");
          $scope.depositionForm[id].$render();
          $scope.depositionForm[id].$commitViewValue();
          return;
        }
        $scope.depositionForm[id].$setViewValue(value);
        $scope.depositionForm[id].$render();
        $scope.depositionForm[id].$commitViewValue();
      }

      $scope.getAutoFillValue = function (data) {
        if (data) {
          return data;
        } else {
          return "";
        }
      }

      $scope.setAutoFillErrorMessage = function (message) {
        $("#autofill-error-message").text(message);
        $("#auto-fill-error-div").addClass("alert alert-danger");
      }

      $scope.resetAutoFillErrorMessage = () => {
        $("#autofill-error-message").text("");
        $("#auto-fill-error-div").removeClass("alert alert-danger");
      }

      $scope.dictValue = function (id, sub1 = null, sub2 = null, sub3 = null) {
        if (!id) {
          return null;
        }
        if (sub1) {
          if (id.hasOwnProperty(sub1)) {
            if (!sub2 && !sub3) {
              return id[sub1];
            }
            else if (sub2 && !sub3) {
              if (id[sub1].hasOwnProperty(sub2)) {
                return id[sub1][sub2];
              }
            } else if (sub2 && sub3) {
              if (id[sub1].hasOwnProperty(sub2)) {
                if (id[sub1][sub2].hasOwnProperty(sub3)) {
                  return id[sub1][sub2][sub3];
                }
              }
            }
          }
        }
        return null;
      }

      $scope.setItemMetadata = function () {
        let autoFillID = $('#autofill_id_type').val();
        let value = $('#autofill_item_id').val();
        let itemTypeId = $("#autofill_item_type_id").val();
        if (autoFillID === 'Default') {
          this.setAutoFillErrorMessage($("#autofill_error_id").val());
          return;
        } else if (!value.length) {
          this.setAutoFillErrorMessage($("#autofill_error_input_value").val());
          return;
        }

        let param = {
          api_type: autoFillID,
          search_data: $.trim(value),
          item_type_id: itemTypeId
        }
        this.setItemMetadataFromApi(param);
      }

      $scope.setItemMetadataFromApi = function (param) {
        $.ajax({
          url: '/api/autofill/get_items_autofill_data',
          headers: {
            'Content-Type': 'application/json'
          },
          method: "POST",
          data: JSON.stringify(param),
          dataType: "json",
          success: (data, status) => {
            if (data.error) {
              this.setAutoFillErrorMessage("An error have occurred!\nDetail: " + data.error);
            } else {
              let items = data.items;
              if (!items) {
                this.setAutoFillErrorMessage('Some error is occurs!');
              }
              let result = data.result;
              if (!result) {
                this.setAutoFillErrorMessage($("#autofill_error_doi").val());
              } else {
                // Reset error message
                this.resetAutoFillErrorMessage();

                this.setItemMetadataCreator(items, result);

                if (items.hasOwnProperty('numPages')) {
                  this.setValueToField(this.dictValue(items.numPages, '@value'), this.getAutoFillValue(this.dictValue(result.numPages, '@value')));
                }

                if (items.hasOwnProperty('pageStart')) {
                  this.setValueToField(this.dictValue(items.pageStart, '@value'), this.getAutoFillValue(this.dictValue(result.pageStart, '@value')));
                }

                if (items.hasOwnProperty('pageEnd')) {
                  this.setValueToField(this.dictValue(items.pageEnd, '@value'), this.getAutoFillValue(this.dictValue(result.pageEnd, '@value')));
                }

                if (items.hasOwnProperty('publisher')) {
                  let id = items.publisher;
                  let resultId = result.publisher;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
                    this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                    this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
                  }
                }

                this.setItemMetadataRelation(items, result);

                if (items.hasOwnProperty('contributor')) {
                  let contributor = items.contributor;
                  let resultId = result.contributor;
                  if (contributor.hasOwnProperty('contributorName')) {
                    let id = contributor.contributorName;
                    let subresultId = resultId.contributorName;
                    if (subresultId && subresultId['@value']) {
                      this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(subresultId, '@attributes', 'xml:lang')));
                      this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subresultId, '@value')));
                    } else {
                      this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
                      this.setValueToField(this.dictValue(id, '@value'), "");
                    }
                  }
                }

                if (items.hasOwnProperty('subject')) {
                  let subject = items.subject;
                  let resultId = result.subject;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(subject, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
                    this.setValueToField(this.dictValue(subject, '@attributes', 'subjectScheme'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'subjectScheme')));
                    this.setValueToField(this.dictValue(subject, '@attributes', 'subjectURI'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'subjectURI')));
                    this.setValueToField(this.dictValue(subject, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(subject, '@attributes', 'xml:lang'), "");
                    this.setValueToField(this.dictValue(subject, '@value'), "");
                    this.setValueToField(this.dictValue(subject, '@attributes', 'subjectScheme'), "");
                    this.setValueToField(this.dictValue(subject, '@attributes', 'subjectURI'), "");
                  }
                }

                if (items.hasOwnProperty('description')) {
                  let description = items.description;
                  let resultId = result.description;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(description, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
                    this.setValueToField(this.dictValue(description, '@attributes', 'descriptionType'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'descriptionType')));
                    this.setValueToField(this.dictValue(description, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(description, '@attributes', 'xml:lang'), "");
                    this.setValueToField(this.dictValue(description, '@value'), "");
                    this.setValueToField(this.dictValue(description, '@attributes', 'descriptionType'), "");
                  }
                }

                if (items.hasOwnProperty('sourceTitle')) {
                  let sourceTitle = items.sourceTitle;
                  let resultId = result.sourceTitle;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(sourceTitle, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
                    this.setValueToField(this.dictValue(sourceTitle, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(sourceTitle, '@attributes', 'xml:lang'), "");
                    this.setValueToField(this.dictValue(sourceTitle, '@value'), "");
                  }
                }

                if (items.hasOwnProperty('volume')) {
                  let volume = items.volume;
                  let resultId = result.volume;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(volume, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(volume, '@value'), "");
                  }
                }

                if (items.hasOwnProperty('issue')) {
                  let issue = items.issue;
                  let resultId = result.issue;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(issue, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(issue, '@value'), "");
                  }
                }

                if (items.hasOwnProperty('sourceIdentifier')) {
                  let sourceIdentifier = items.sourceIdentifier;
                  let resultId = result.sourceIdentifier;
                  if (resultId && resultId['@value']) {
                    this.setValueToField(this.dictValue(sourceIdentifier, '@attributes', 'identifierType'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'identifierType')));
                    this.setValueToField(this.dictValue(sourceIdentifier, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
                  } else {
                    this.setValueToField(this.dictValue(sourceIdentifier, '@attributes', 'xml:lang'), "");
                    this.setValueToField(this.dictValue(sourceIdentifier, '@value'), "");
                  }
                }

                if (param.api_type == 'CrossRef') {
                  this.setItemMetadataCrossRef(items, result);
                }
                else if (param.api_type == 'CiNii') {
                  this.setItemMetadataCiNii(items, result);
                }

                $('#meta-search').modal('toggle');
              }
            }
          },
          error: (data, status) => {
            this.setAutoFillErrorMessage("Cannot connect to server!");
          }
        });
      }

      $scope.setItemMetadataCrossRef = function (items, result) {
        if (items.hasOwnProperty('date')) {
          let id = items.date;
          let resultId = result.date;
          if (this.getAutoFillValue(this.dictValue(resultId, '@value'))) {
            this.setValueToField(this.dictValue(id, '@attributes', 'dateType'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'dateType')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@attributes', 'dateType'), "");
            this.setValueToField(this.dictValue(id, '@value'), "");
          }
        }

        if (items.hasOwnProperty('language')) {
          this.setValueToField(this.dictValue(items.language, '@value'), this.getAutoFillValue(this.dictValue(result.language, '@value')));
        }

        if (items.hasOwnProperty('title')) {
          let id = items.title;
          let resultId = result.title;
          if (resultId && resultId['@value']) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
          }
        }
      }

      $scope.setItemMetadataCiNii = function (items, result) {
        if (items.hasOwnProperty('date')) {
          let id, resultId;
          for (let i = 0; i < items.date.length; i++) {
            if (this.getAutoFillValue(this.dictValue(items.date[i], 'date')) != "") {
              id = items.date[i];
              resultId = result.date[i];
              break;
            }
          }
          if (this.getAutoFillValue(this.dictValue(resultId, 'date', '@value'))) {
            this.setValueToField(this.dictValue(id, 'date', '@attributes', 'dateType'), this.getAutoFillValue(this.dictValue(resultId, 'date', '@attributes', 'dateType')));
            this.setValueToField(this.dictValue(id, 'date', '@value'), this.getAutoFillValue(this.dictValue(resultId, 'date', '@value')));
          } else {
            this.setValueToField(this.dictValue(id, 'date', '@attributes', 'dateType'), "");
            this.setValueToField(this.dictValue(id, 'date', '@value'), "");
          }
        }

        if (items.hasOwnProperty('language')) {
          let id, resultId;
          for (let i = 0; i < items.language.length; i++) {
            if (this.getAutoFillValue(this.dictValue(items.language[i], 'date')) != "") {
              id = items.language[i];
              resultId = result.language[i];
              break;
            }
          }
          this.setValueToField(this.dictValue(id, 'language', '@value'), this.getAutoFillValue(this.dictValue(resultId, 'language', '@value')));
        }

        if (items.hasOwnProperty('title')) {
          let id, resultId;
          for (let i = 0; i < items.title.length; i++) {
            if (this.getAutoFillValue(this.dictValue(items.title[i], 'title')) != "") {
              id = items.title[i];
              resultId = result.title[i];
              break;
            }
          }
          if (this.getAutoFillValue(this.dictValue(resultId, 'title', '@value'))) {
            this.setValueToField(this.dictValue(id, 'title', '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, 'title', '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, 'title', '@value'), this.getAutoFillValue(this.dictValue(resultId, 'title', '@value')));
          } else {
            this.setValueToField(this.dictValue(id, 'title', '@attributes', 'xml:lang'), "");
            this.setValueToField(this.dictValue(id, 'title', '@value'), "");
          }
        }
      }

      $scope.setItemMetadataCreator = function (items, result) {
        if (items.creator.hasOwnProperty('affiliation')) {
          if (items.creator.affiliation.hasOwnProperty('affiliationName')) {
            let id = items.creator.affiliation.affiliationName;
            let resultId = result.creator.affiliation.affiliationName;
            if (resultId && resultId['@value']) {
              this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            } else {
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
              this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
            }
          }
          if (items.creator.affiliation.hasOwnProperty('nameIdentifier')) {
            let id = items.creator.affiliation.nameIdentifier;
            let resultId = result.creator.affiliation.nameIdentifier;
            this.setValueToField(this.dictValue(id, '@attributes', 'nameIdentifierScheme'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'nameIdentifierScheme')));
            this.setValueToField(this.dictValue(id, '@attributes', 'nameIdentifierURI'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'nameIdentifierURI')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(resultId['@value']));
          }
        }
        if (items.creator.hasOwnProperty('creatorAlternative')) {
          let id = items.creator.creatorAlternative;
          let resultId = result.creator.creatorAlternative;
          if (resultId && resultId['@value']) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
          }
        }
        if (items.creator.hasOwnProperty('creatorName')) {
          let id = items.creator.creatorName;
          let resultId = result.creator.creatorName;
          if (resultId && resultId['@value']) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
          }
        }
        if (items.creator.hasOwnProperty('familyName')) {
          let id = items.creator.familyName;
          let resultId = result.creator.familyName;
          if (resultId && resultId['@value']) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
          }
        }
        if (items.creator.hasOwnProperty('givenName')) {
          let id = items.creator.givenName;
          let resultId = result.creator.givenName;
          if (resultId && resultId['@value']) {
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'xml:lang')));
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
          } else {
            this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
            this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
          }
        }
        if (items.creator.hasOwnProperty('nameIdentifier')) {
          let id = items.creator.nameIdentifier;
          let resultId = result.creator.nameIdentifier;
          this.setValueToField(this.dictValue(id, '@attributes', 'nameIdentifierScheme'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'nameIdentifierScheme')));
          this.setValueToField(this.dictValue(id, '@attributes', 'nameIdentifierURI'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'nameIdentifierURI')));
          this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(resultId, '@value')));
        }
      }

      $scope.setItemMetadataRelation = function (items, result) {
        if (items.hasOwnProperty('relation')) {
          let relation = items.relation;
          let resultId = result.relation;
          this.setValueToField(this.dictValue(relation, '@attributes', 'relationType'), this.getAutoFillValue(this.dictValue(resultId, '@attributes', 'relationType')));
          if (relation.hasOwnProperty('relatedIdentifier')) {
            let id = relation.relatedIdentifier;
            let subresultId = resultId.relatedIdentifier;
            if (subresultId && subresultId['@value']) {
              this.setValueToField(this.dictValue(id, '@attributes', 'identifierType'), this.getAutoFillValue(this.dictValue(subresultId, '@attributes', 'identifierType')));
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subresultId, '@value')));
            } else {
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subresultId, '@value')));
              this.setValueToField(this.dictValue(id, '@attributes', 'identifierType'), "");
            }
          }
          if (relation.hasOwnProperty('relatedTitle')) {
            let id = relation.relatedTitle;
            let subresultId = resultId.relatedTitle;
            if (subresultId && subresultId['@value']) {
              this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), this.getAutoFillValue(this.dictValue(subresultId, '@attributes', 'xml:lang')));
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subresultId, '@value')));
            } else {
              this.setValueToField(this.dictValue(id, '@value'), this.getAutoFillValue(this.dictValue(subresultId, '@value')));
              this.setValueToField(this.dictValue(id, '@attributes', 'xml:lang'), "");
            }
          }
        }
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
