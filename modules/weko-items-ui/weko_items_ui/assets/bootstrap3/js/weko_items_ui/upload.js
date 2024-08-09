//require([
//  'jquery'
//],function () {

import $ from "jquery";
import "node_modules/angular-schema-form/node_modules/tv4/tv4.js"
import "node_modules/angular-schema-form/node_modules/objectpath/lib/ObjectPath.js"
import "node_modules/angular-sanitize/angular-sanitize.min.js"

$( function () {
  $('#myModal').modal({
    show: false
  })

  function Percentage(num, total) {
    return (Math.round(num / total * 10000) / 100.00 + "%");// 小数点后两位百分比
  }

  $('#demo-submit').on('click', function() {
    // Clear results
    $('#result').addClass('hidden');
    $('#result-list').empty();

    // Get input string
    var demoStr = $('#item-demo-data').val();
    if(/\n/.test(demoStr) == false) {
      console.log('demoStr does not match lf');
      return;
    }

    // Get files
    var all_files = $('#files')[0].files;
    var file_map = {};
    for (var i = 0; i < all_files.length; i++) {
      file_map[all_files[i].name] = all_files[i];
    }

    // Initialize
    var redirect_url = "/api/deposits/redirect";
    var items_url = "/api/deposits/items";

    var totalNo = 0;
    var errorList = [];

    // Add or update items
    var demoList = demoStr.split(/\n/);
    for(idx=0; idx<demoList.length; idx++) {
      if(demoList[idx].length == 0){break;}

      // Initialize item info
      totalNo++;
      var errorFlg = false;
      var error = {};
      error['category'] = "";
      error['line'] = idx + 1;
      error['item'] = "";
      error['eMsg'] = "";

      // Read item info
      idData = JSON.parse(demoList[idx]);
      itemData = JSON.parse(demoList[++idx]);
      indexData = JSON.parse(demoList[++idx]);

      // Get item files
      var files = {};
      var isAllFileSelected = true;
      var notFoundFiles = [];
      for (var key in itemData) {
        if (itemData[key] instanceof Array && 'filename' in itemData[key][0]) {
          for (var index in itemData[key]) {
            var fileName = itemData[key][index]['filename'];
            if (fileName in file_map) {
              files[fileName] = file_map[fileName];
            }else {
              notFoundFiles.push(fileName);
              isAllFileSelected = false;
            }
          }
        }
      }

      // Check item files
      if(!isAllFileSelected) {
        if (idData['id']) {
          error['category'] = "Update";
          error['item'] = idData['id'];
        }else {
          error['category'] = "Add";
        }
        error['eMsg'] = "File[" + notFoundFiles.join(',') + "] not found."
        errorList.push(error);

        // To next item
        continue;
      }

      // Update item
      if (idData['id']) {
        error['category'] = "Update";
        error['item'] = idData['id'];

        index_url = redirect_url + "/" + idData['id'];
        self_url = items_url + "/" + idData['id'];

        // Has file
        if (Object.keys(files) != 0) {
          // Get bucket
          $.ajax({
            type: "POST",
            url: index_url,
            async: false,
            cache: false,
            data: {},
            contentType: "application/json",
            processData: false,
            success: function(data) {
              // Upload files
              for (var fileName in files) {
                file_url = data['links']['bucket'] + "/" + fileName;
                $.ajax({
                  type: "PUT",
                  url: file_url,
                  async: false,
                  cache: false,
                  data: files[fileName],
                  contentType: "application/json",
                  processData: false,
                  success: function() {
                    // Update items
                    updateItems(index_url,
                                self_url,
                                JSON.stringify(itemData),
                                JSON.stringify(indexData),
                                error,
                                errorFlg);
                  },
                  error: function() {
                    errorFlg = true;
                    error['eMsg'] = "Error in file uploading.";
                  }
                });
              }
            },
            error: function() {
              errorFlg = true;
              error['eMsg'] = "Error in bucket requesting.";
            }
          });

        // No file
        }else {
          // Update items
          updateItems(index_url,
                      self_url,
                      JSON.stringify(itemData),
                      JSON.stringify(indexData),
                      error,
                      errorFlg);
        }

      // New item
      } else {
        error['category'] = "Add";

        // Create bucket
        $.ajax({
          type: 'POST',
          url: '/api/deposits/items',
          async: false,
          cache: false,
          data: JSON.stringify({'$schema': itemData['$schema']}),
          dataType: "json",
          contentType: "application/json",
          success: function(data){
            index_url = redirect_url + "/" + data['id'];
            self_url = items_url + "/" + data['id'];

            // Has File
            if (Object.keys(files) != 0) {
              // Upload files
              for (var fileName in files) {
                file_url = data['links']['bucket'] + "/" + fileName;
                $.ajax({
                  type: "PUT",
                  url: file_url,
                  async: false,
                  cache: false,
                  data: files[fileName],
                  contentType: "application/json",
                  processData: false,
                  success: function() {
                    // Update items
                    updateItems(index_url,
                                self_url,
                                JSON.stringify(itemData),
                                JSON.stringify(indexData),
                                error,
                                errorFlg);
                  },
                  error: function() {
                    errorFlg = true;
                    error['eMsg'] = "Error in file uploading.";
                  }
                });
              }

            // No file
            } else {
              // Update items
              updateItems(index_url,
                          self_url,
                          JSON.stringify(itemData),
                          JSON.stringify(indexData),
                          error,
                          errorFlg);
            }
          },
          error: function() {
            errorFlg = true;
            error['eMsg'] = "Error in bucket creation.";
          }
        });
      }

      // Add to error list
      if (errorFlg) {errorList.push(error)};
    }

    // Display message
    $('.modal-body').html('Upload completed. &nbsp;【&nbsp;Success(' +
                        (totalNo - errorList.length) + ')&nbsp;&nbsp;+&nbsp;&nbsp;Error(' +
                        errorList.length + ')&nbsp;&nbsp;/&nbsp;&nbsp;Total(' +
                        totalNo + ')&nbsp;&nbsp;item(s)&nbsp;】');
    $('#myModal').modal('show');

    // Display error list
    displayErrorList(errorList, totalNo);
  });

  function updateItems(index_url, self_url, itemData, indexData, error, errorFlg) {
    // Post to index select
    $.ajax({
      type: "PUT",
      url: index_url,
      async: false,
      cache: false,
      data: itemData,
      contentType: "application/json",
      success: function() {
        // Post item data
        $.ajax({
          type: "PUT",
          url: self_url,
          async: false,
          cache: false,
          data: indexData,
          contentType: "application/json",
          success: function(){},
          error: function() {
            errorFlg = true;
            error['eMsg'] = "Error in item data posting.";
          }
        });
      },
      error: function() {
        errorFlg = true;
        error['eMsg'] = "Error in index selection.";
      }
    });
  }

  function displayErrorList(errorList, totalNo) {
    if (errorList.length === 0) return;

    // Add error list
    for (var index in errorList) {
      $('#result-list').append('<tr><td>' + errorList[index]['category'] +
                              '</td><td>' + errorList[index]['line'] +
                              '</td><td>' + errorList[index]['item'] +
                              '</td><td>' + errorList[index]['eMsg'] +'</td></tr>');
    }
    $('#result-label').html("Error List:<br>&nbsp;&nbsp;" + errorList.length + " error(s) of " + totalNo +" item(s)");
    $('#result').removeClass('hidden');
  }
});

(function (angular) {
  angular.element(document).ready(function () {
    angular.module('schemaForm')
    .run(["$templateCache", function($templateCache) {
      var allow_multiple = $("#allow-thumbnail-flg").val() == 'True' ? 'multiple' : '';
      var template = "<div class=\"form-group\" ng-class=\"{\'has-error\': hasError()}\">\n    <div>\n        <input ng-model=\"$$value$$\" type=\"file\" id=\"selectThumbnail\" on-read-file accept=\".gif,.jpg,.jpe,.jpeg,.png,.bmp\" " + allow_multiple + "/>\n        <img ng-show=\"$$value$$\" id=\"myimage\" src=\"\" alt=\"your image\" />\n    </div>\n    <span class=\"help-block\">{{ (hasError() && errorMessage(schemaError())) || form.description}}</span>\n</div>";
      $templateCache.put("directives/decorators/bootstrap/fileUpload/file-upload.html", template);
    }]);
    angular.module('schemaForm').config(
    ['schemaFormProvider', 'schemaFormDecoratorsProvider', 'sfPathProvider',
      function (schemaFormProvider, schemaFormDecoratorsProvider, sfPathProvider) {
                var fileUpload = function (name, schema, options) {
                    if (schema.type === 'string' && schema.format === 'file') {
                        var f = schemaFormProvider.stdFormObj(name, schema, options);
                        f.key = options.path;
                        f.type = 'fileUpload';
                        options.lookup[sfPathProvider.stringify(options.path)] = f;
                        return f;
                    }
                };

                schemaFormProvider.defaults.string.unshift(fileUpload);

                schemaFormDecoratorsProvider.addMapping(
                    'bootstrapDecorator',
                    'fileUpload',
                    'directives/decorators/bootstrap/fileUpload/file-upload.html'
                );

                schemaFormDecoratorsProvider.createDirective(
                    'fileUpload',
                    'directives/decorators/bootstrap/fileUpload/file-upload.html'
                );
      }]);
      angular.module('schemaForm').directive('onReadFile', function ($parse, $rootScope) {
        return {
            restrict: 'A',
            require: ['ngModel'],
            scope: true,
            link: function ($scope, element, attrs, ngModelCtrl) {
                element.on('change', function (onChangeEvent) {
                    var files = (onChangeEvent.srcElement || onChangeEvent.target).files;
                    if (!angular.isUndefined(files) && files.length > 0) {
                      if ($scope.$parent.model.allowMultiple != 'True') {
                        files = Array.prototype.slice.call(files, 0, 1);
                        let overwriteFiles = $.extend(true, {}, $scope.$parent.model.thumbnailsInfor);

                        if (Object.keys(overwriteFiles).length > 0) {
                          $rootScope.$$childHead.uploadingThumbnails = files;

                          $.each(overwriteFiles, function (index, thumb) {
                            $rootScope.$$childHead.removeThumbnail(thumb);
                          });
                        } else {
                          $rootScope.$$childHead.directedUpload(files);
                        }
                      } else {
                        $rootScope.$$childHead.directedUpload(files);
                      }
                    }
                });
            }
        };
    });
  });
})(angular);
