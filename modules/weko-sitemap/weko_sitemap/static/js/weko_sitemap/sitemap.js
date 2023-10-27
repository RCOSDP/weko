//require([ // Must add requirejs to admin-side
//  "jquery",
  //"bootstrap"
//  ], function() {
    $(document).ready(function () {
        const xmlIndexEndpoint = '/weko/sitemaps/sitemapindex.xml';
        const updateSitemapEndpoint = '/admin/sitemap/update_sitemap';
        var  csrf_token=$('#csrf_token').val();
        $.ajaxSetup({
          beforeSend: function(xhr, settings) {
             if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain){
                 xhr.setRequestHeader("X-CSRFToken", csrf_token);
             }
          }
        });
        $('#btn-run').on('click', function(){
          $("#btn-run").prop('disabled', true);
          $('#loader_spinner').css('display', 'block');
          $('#task_list').hide();
          setColumnsText('', '', '', '');
          $.ajax({
            type: 'POST',
            url: updateSitemapEndpoint,
            success: function(response) {
              trackTaskProgress(response.loc); // Pass the status URL to async task
            },
            error: function(response) {
              $('#loader_spinner').hide();
              $('#task_list').show();
              $('#task_status').text('ERROR'); // TODO: Do something Failed to call endpoint
              $("#btn-run").prop('disabled', false);
            }
          });

          
        });
    });

    function trackTaskProgress(loc) {
      $.ajax({
        type: 'GET',
        url: loc,
        success: function(response) {
          console.log('Getting task status...');
          console.log(JSON.stringify(response));
          if(response.state == 'SUCCESS' ||
             response.state == 'FAILURE' ||
             response.state == 'REVOKED') {
            $('#loader_spinner').css('display', 'none');
            $('#task_list').show();
            $("#btn-run").prop('disabled', false);
            setColumnsText(response.start_time, response.end_time, response.state, response.total);
          }
          else {
            console.log('Trying again in 2 seconds...' + response.state);
            setTimeout(function() {
              trackTaskProgress(loc);
            }, 2000);
          }
        },
        error: function(response) {
          $('#loader_spinner').hide();
          $('#task_list').show();
          $('#task_status').text('ERROR'); // TODO: Do something Failed to call endpoint
          $("#btn-run").prop('disabled', false);
        }
      });
    }

    function setColumnsText(start, end, status, total) {
      $('#task_start_time').text(start);
      $('#task_end_time').text(end);
      $('#task_status').text(status);
      $('#task_total').text(total);
    }
//});

