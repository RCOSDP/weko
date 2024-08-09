//require([
//    "jquery",
//    "bootstrap"
//], function () {
  import "bootstrap";
  import $ from "jquery";
    $(document).ready( function() {
      $($('.field-row-default').find('input[name="access_date"]')[0]).val(getDate());
      addField();
    });
    $('#add-field-link').on('click', function() {
      addField();
      return false;
    });

    // Remove field
    $('.del-field').on('click', function() {
      if($('#field-panel').find('.field-row').length > 1) {
        $(this).parents('.field-row').remove();
      }
      return false;
    });

    $('input[name="access_type"]').change(function() {
      var selected = $(this).val();
      accessDate = $(this).parents('.access-type-select').find('input[name="access_date"]');
      if(selected == 'open_date'){
        $(accessDate).removeAttr("disabled");
      } else {
        $(accessDate).attr('disabled', 'disabled');
      }
    });

    $('select[name="field_sel"]').change(function() {
      var selected = $(this).val();
      var contents = $(this).parents('.field-row').find('.field-content');

      // Get selected fields
      var fields = [];
      $('.row.field-row').each(function(i, row) {
        var field = $($(row).find('select[name="field_sel"]')[0]).prop('value');
        if(field !== 'unselected') {
          fields.push(field);
        }
      });

      var uniqueFields = fields.filter(function (x, i, self) {
        return self.indexOf(x) === i;
      });
      // Check fields
      if(fields.length !== uniqueFields.length) {
        //alert('Field already exists.');
        var modalcontent =  "Field already exists.";
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
        $(this).val('unselected');
        contents.each(function(i, elem) {
          $(elem).attr('hidden', 'hidden');
        });
        return;
      }

      contents.each(function(i, elem) {
        var elemAttr = $(elem).attr('class');
        // Access Type
        if(elemAttr.indexOf('access-type-select') >= 0){
          if('1' === selected.toString()){
            $(elem).removeAttr("hidden");
          }else {
            $(elem).attr('hidden', 'hidden');
          }

        // Licence
        } else if(elemAttr.indexOf('licence-select') >= 0){
          if('2' === selected.toString()){
            $(elem).removeAttr("hidden");
          }else {
            $(elem).attr('hidden', 'hidden');
          }
        }
      });
    });

    $('select[name="licence_sel"]').change( function() {
      var selected = $(this).val();
      var des = $($(this).parent().find('.licence-des'));

      if(selected === 'license_free') {
        des.removeAttr("hidden");
      } else {
        des.attr('hidden', 'hidden');
      }
    });

    // Select All
    $('#select-all').on('click', function() {
      hasChecked = false;
      hasCanceled = false;

      checkboxes = $(this).parent().find('input[type="checkbox"]');
      checkboxes.each( function(i, elem) {
        if($(elem).prop('checked') === false){
          hasCanceled = true;
        }else {
          hasChecked = true;
        }
      });

      // Cancel all
      if(hasChecked && !hasCanceled) {
        checkboxes.each( function(i, elem) {
          $(elem).prop("checked", false);
        });
      // Check all
      }else {
        checkboxes.each( function(i, elem) {
          $(elem).prop("checked", true);
        });
      }
      return false;
    });

    $('#submit-btn').on('click', function() {
      // Get id
      pids = '';
      $('input[type="checkbox"]').each(function(i, elem) {
        if($(elem).prop('checked') === true){
          if(pids === '') {
            pids = $(elem).prop('value');
          } else {
            pids = pids + '/' + $(elem).prop('value');
          }
        }
      });
      if (pids === '') {
        //alert('Please select items to update.');
        var modalcontent =  "Please select items to update.";
        $("#inputModal").html(modalcontent);
        $("#allModal").modal("show");
        return;
      } else {
        $("#confirm_update").modal("show");
      }
      $('#table_list_of_update').remove()
      $("#confirm_update > div > div > div.modal-body").append(
          '<table id="table_list_of_update" class="table table-striped table-bordered table-hover">\
            <thead>\
              <tr>\
                <th rowspan="2" valign="middle">Item</th>\
                <th colspan="2" align="center">Before</th>\
                <th colspan="2" align="center">After</th>\
              </tr>\
              <tr>\
                <th>Access Type</th>\
                <th>Licence</th>\
                <th>Access Type</th>\
                <th>Licence</th>\
              </tr>\
            </thead>\
            <tbody>\
            </tbody>\
          </table>'
      )  
      // Get setting fields
      var accessType = {};
      var licence= '';
      var licenceDes= '';
      $('.row.field-row').each(function(i, row) {
        var field = $($(row).find('select[name="field_sel"]')[0]);
        // Access Type
        if(field.prop('value') === '1') {
          var type = $($(row).find('input[name="access_type"]:checked')[0]).prop('value');
          accessType = {'accessrole': type};
          if (type === 'open_date') {
            accessType['accessdate'] = $($(row).find('input[name="access_date"]')[0]).prop('value');
          }
        // Licence
        }else if(field.prop('value') === '2') {
          licence = $($(row).find('select[name="licence_sel"]')[0]).prop('value');
          if(licence === 'license_free') {
            licenceDes = $($(row).find('textarea[name="licence_des"]')[0]).prop('value');
          }
        }
      });

      getUrl = '/admin/items/bulk/update/items_metadata?pids=' + pids;
      $.ajax({
        method: 'GET',
        url: getUrl,
        async: false,
        success: function(data, status){

          itemsMeta = data;
          Object.keys(itemsMeta).forEach(function(pid) {
            // Contents Meta
            if (Object.keys(itemsMeta[pid].contents).length !== 0) {
                Object.values(itemsMeta[pid].contents).forEach(function(content){
                    for(i = 0; i < content.length; ++i) {
                        var before_access_type = content[i]['accessrole'];
                        var before_licence = content[i]['licensetype'];
                        var after_access_type = accessType['accessrole'] ? accessType['accessrole'] : before_access_type;
                        var after_licence = licence ? licence : before_licence;
                        $('#table_list_of_update > tbody').append(
                         '<tr>' +
                         '<td>' + content[i]['filename'] + '</td>' +
                         '<td>' + before_access_type + '</td>' +
                         '<td>' + before_licence + '</td>' +
                         '<td>' + after_access_type + '</td>' +
                         '<td>' + after_licence + '</td>' +
                         '</tr>' 
                        );
                    };
                });
            };
          });
        },
        error: function(status, error){
          console.log(error);
        }
      });
    });


    // Bulk Update
    $('#confirm_submit').on('click', function() {
      // Get id
      pids = '';
      $('input[type="checkbox"]').each(function(i, elem) {
        if($(elem).prop('checked') === true){
          if(pids === '') {
            pids = $(elem).prop('value');
          } else {
            pids = pids + '/' + $(elem).prop('value');
          }
        }
      });

      $('#confirm_update').modal('hide')
      // Get setting fields
      var accessType = {};
      var licence= '';
      var licenceDes= '';
      $('.row.field-row').each(function(i, row) {
        var field = $($(row).find('select[name="field_sel"]')[0]);
        // Access Type
        if(field.prop('value') === '1') {
          var type = $($(row).find('input[name="access_type"]:checked')[0]).prop('value');
          accessType = {'accessrole': type};
          if (type === 'open_date') {
            accessType['accessdate'] = $($(row).find('input[name="access_date"]')[0]).prop('value');
          }
        // Licence
        }else if(field.prop('value') === '2') {
          licence = $($(row).find('select[name="licence_sel"]')[0]).prop('value');
          if(licence === 'license_free') {
            licenceDes = $($(row).find('textarea[name="licence_des"]')[0]).prop('value');
          }
        }
      });

      // Update
      getUrl = '/admin/items/bulk/update/items_metadata?pids=' + pids;
      $.ajax({
        method: 'GET',
        url: getUrl,
        async: false,
        success: function(data, status){
          var errorMsgs = [];
          var redirect_url = "/api/deposits/redirect";
          var items_url = "/api/deposits/items";
          var publish_url = "/api/deposits/publish";

          itemsMeta = data;
          Object.keys(itemsMeta).forEach(function(pid) {
            // Contents Meta
            if (Object.keys(itemsMeta[pid].contents).length !== 0) {
              Object.keys(itemsMeta[pid].contents).forEach( function(contentKey) {

                var contentsMeta = itemsMeta[pid].contents[contentKey];
                $.each( contentsMeta, function( key, value ) {
                  // Access Type
                  if (Object.keys(accessType).length !== 0) {
                    Object.keys(accessType).forEach( function(field) {
                    value[field] =  accessType[field];
                    });
                  }
                  // Licence
                  if(licence !== 'unselected' && licence !== '') {
                    value['licensetype'] = licence;
                  }
                  // Licence Description
                  if(licenceDes !== '' && licence === 'license_free') {
                    value['licensefree'] = licenceDes;
                  }
                });
                itemsMeta[pid].meta[contentKey] = contentsMeta;
              });

              // Data
              var _meta = JSON.stringify(itemsMeta[pid].meta);
              itemsMeta[pid].meta['edit_mode'] = 'upgrade'
              var meta = JSON.stringify(itemsMeta[pid].meta);
              var index = JSON.stringify(itemsMeta[pid].index);
              var version = itemsMeta[pid].version;

              let next_version = version
              if (version) {
                next_version = version.split('.')[0] + '.' + (parseInt(version.split('.')[1]) + 1)
              }

              // URL
              var _index_url= redirect_url + "/" + pid;
              var _self_url = items_url    + "/" + pid;
              var _pub_url  = publish_url  + "/" + pid;
              var index_url = redirect_url + "/" + version;
              var self_url  = items_url    + "/" + next_version;
              var pub_url   = publish_url  + "/" + next_version;

              var error = {};

              // Update items
              updateItems(_index_url, _self_url, _pub_url, _meta, index, error);
              // Create new version
              updateItems(index_url, self_url, pub_url, meta, index, error);

              if(error.isError) {
                errorMsgs.push('[ ID: '+pid.toString()+', Title: '+
                               itemsMeta[pid].meta.title_ja+', Error: '+error.msg+' ]');
              }
            }
          });

          // Result
          if(errorMsgs.length !== 0) {
            var msg = 'Error List:\n'+errorMsgs.join('\n');
            alert(msg);

          } else {
            alert('All selected items have been updated successfully.');
          }
        },
        error: function(status, error){
          console.log(error);
        }
      });
    });

    $("#bulk_delete_confirmation_button").click(function () {
      $("#bulk_delete_confirmation_button").attr('disabled', true);
      var data = {
        'q': GetUrlParam("q"),
        'recursively': $("#recursively").prop('checked'),
        'sort': 'custom_sort'
      }

      // Update
      $.ajax({
        method: 'GET',
        url: '/admin/items/bulk/delete/check',
        async: false,
        cache: false,
        data: data,
        success: function (data, status, xhr) {
          if (data.status == 1) {
            $("#bulk_delete_confirmation_continue").attr('disabled', false);
            $("#bulk_delete_confirmation_message").html(data.msg);
            $("#bulk_delete_confirmation_message").addClass('text-info');
            $("#bulk_delete_confirmation").modal("show");
          } else {
            $("#bulk_delete_confirmation_message").html(data.msg);
            $("#bulk_delete_confirmation_message").addClass('text-danger');
            $("#bulk_delete_confirmation").modal("show");
          }
          $("#bulk_delete_confirmation_button").attr('disabled', false);
        },
        error: function (status, error) {
          $("#bulk_delete_confirmation_message").html(error);
          $("#bulk_delete_confirmation").modal("show");
          $("#bulk_delete_confirmation_button").attr('disabled', false);
        }
      });
    });

    // For bulk delete's actions
    $("#bulk_delete_confirmation_continue").click(function () {
      $("#bulk_delete_confirmation_continue").attr('disabled', true);
      $("#bulk_delete_confirmation_cancel").attr('disabled', true);

      // Do submit data
      // Get index id
      var data = {
        'q': GetUrlParam("q"),
        'recursively': $("#recursively").prop('checked'),
        'sort': 'custom_sort'
      }

      // Update
      $.ajax({
        method: 'PUT',
        url: '/admin/items/bulk/delete/',
        async: false,
        cache: false,
        data: data,
        success: function (data, status, xhr) {
          console.log(xhr.status);

          $("#bulk_delete_confirmation_continue").attr('disabled', false);
          $("#bulk_delete_confirmation_cancel").attr('disabled', false);
          $("#bulk_delete_confirmation").modal("hide");
          $("#recursively").prop("checked", false);
          addError(data.msg)
        },
        error: function (status, error) {
          $("#bulk_delete_confirmation_continue").attr('disabled', false);
          $("#bulk_delete_confirmation_cancel").attr('disabled', false);
          $("#bulk_delete_confirmation").modal("hide");
          $("#recursively").prop("checked", false);
          addError(error)
        }
      });
    });

    function updateItems(index_url, self_url, pub_url, itemData, indexData, error) {
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
            success: function(){
                $.ajax({
                    type: "PUT",
                    url: pub_url,
                    async: false,
                    cache: false,
                    data: {},
                    contentType: "application/json",
                success: function(){
                },
                error: function() {
                  error['isError'] = true;
                  error['msg'] = "Error in publish item.";
                }
              });
            },
            error: function() {
              error['isError'] = true;
              error['msg'] = "Error in item data posting.";
            }
          });
        },
        error: function() {
          error['isError'] = true;
          error['msg'] = "Error in index selection.";
        }
      });
    }

    // Add field
    function addField() {
      newField = $('.field-row-default').first().clone(true)
      $(newField).attr('class', 'row field-row');
      $(newField).removeAttr("hidden");
      $(newField).insertBefore($('#add-field-row'));
    }

    // Get date
    function getDate() {
      var year;
      var month;
      var day;
      $.ajax({
        url: '/api/admin/get_server_date',
        method: 'GET',
        async: false,
        success: function (data, status) {
          year = data.year
          month = data.month
          day = data.day
        },
        error: function (data, status) {
          var date = new Date();
          year = date.getFullYear();
          month = date.getMonth() + 1;
          day = date.getDate();
        }
      });

      var toTwoDigits = function (num, digit) {
        num += '';
        if (num.length < digit) {
          num = '0' + num;
        }
        return num;
      }

      var yyyy = toTwoDigits(year, 4);
      var mm = toTwoDigits(month, 2);
      var dd = toTwoDigits(day, 2);

      return yyyy + "-" + mm + "-" + dd;
    }

    //urlからパラメタ―の値を取得
    function GetUrlParam(sParam) {
        var sURL = window.location.search.substring(1);
        var sURLVars = sURL.split('&');
        for (var i = 0; i < sURLVars.length; i++) {
            var sParamArr = sURLVars[i].split('=');
            if (sParamArr[0] == sParam) {
                return decodeURIComponent(sParamArr[1]);
            }
        }
        return false;
    }

    function addError(message) {
      $('#errors').append(
        '<div class="alert alert-danger alert-dismissable">' +
        '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">' +
        '&times;</button>' + message + '</div>');
    }
;
