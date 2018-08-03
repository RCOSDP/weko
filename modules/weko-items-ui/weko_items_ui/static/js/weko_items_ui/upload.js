require([
  'jquery'
],function () {
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
