  require([
    "jquery",
    "bootstrap",
    "node_modules/bootstrap-datepicker/dist/js/bootstrap-datepicker"
    ], function() {
    // loading all the jQuery modules for the not require.js ready scripts
    // everywhere.
    $(function(){
      $('#myModal').modal({
        show: false
      })
      $('#detail_search_btn').on('click', function(){
        formdata = query_to_hash($(location).attr('search').substr(1));
        if(formdata.hasOwnProperty('search_title')) {
          $('#search_title').val(formdata.search_title);
        }
        if(formdata.hasOwnProperty('search_creator')) {
           $('#search_creator').val(formdata.search_creator);
        }
        if(formdata.hasOwnProperty('subject')) {
           $('#subject').val(formdata.subject);
        }
        if(formdata.hasOwnProperty('search_sh')) {
           $('#search_sh').val(formdata.search_sh);
        }
        if(formdata.hasOwnProperty('description')) {
           $('#description').val(formdata.description);
        }
        if(formdata.hasOwnProperty('search_publishe')) {
           $('#search_publishe').val(formdata.search_publishe);
        }
        if(formdata.hasOwnProperty('search_contributor')) {
           $('#search_contributor').val(formdata.search_contributor);
        }
        if(formdata.hasOwnProperty('date_start')) {
           $('#date_start').val(formdata.date_start);
        }
        if(formdata.hasOwnProperty('date_end')) {
           $('#date_end').val(formdata.date_end);
        }
        if(formdata.hasOwnProperty('itemtype')) {
           $('#itemtype').val(formdata.itemtype);
        }
        if(formdata.hasOwnProperty('format')) {
           $('#format').val(formdata.format);
        }
        if(formdata.hasOwnProperty('search_id')) {
           $('#search_id').val(formdata.search_id);
        }
        if(formdata.hasOwnProperty('jtitle')) {
           $('#jtitle').val(formdata.jtitle);
        }
        if(formdata.hasOwnProperty('dateofissued_start')) {
           $('#dateofissued_start').val(formdata.dateofissued_start);
        }
        if(formdata.hasOwnProperty('dateofissued_end')) {
           $('#dateofissued_end').val(formdata.dateofissued_end);
        }
        if(formdata.hasOwnProperty('search_spatial')) {
           $('#search_spatial').val(formdata.search_spatial);
        }
        if(formdata.hasOwnProperty('search_temporal')) {
           $('#search_temporal').val(formdata.search_temporal);
        }
        if(formdata.hasOwnProperty('rights')) {
           $('#rights').val(formdata.rights);
        }
        if(formdata.hasOwnProperty('textversion')) {
           $('#textversion').val(formdata.textversion);
        }
        if(formdata.hasOwnProperty('grantid')) {
           $('#grantid').val(formdata.grantid);
        }
        if(formdata.hasOwnProperty('dateofgranted_start')) {
           $('#dateofgranted_start').val(formdata.dateofgranted_start);
        }
        if(formdata.hasOwnProperty('dateofgranted_end')) {
           $('#dateofgranted_end').val(formdata.dateofgranted_end);
        }
        if(formdata.hasOwnProperty('degreename')) {
           $('#degreename').val(formdata.degreename);
        }
        if(formdata.hasOwnProperty('grantor')) {
           $('#grantor').val(formdata.grantor);
        }
        $('#myModal').modal('show');
      });
      var query_to_hash = function(queryString) {
        var query = queryString || location.search.replace(/\?/, "");
        return query.split("&").reduce(function(obj, item, i) {
          if(item) {
            item = item.split('=');
            obj[item[0]] = item[1];
            return obj;
          }
        }, {});
      };
      $('#detail-search-btn').on('click', function(){
        NIItypeVal = 0;
        if($('#NIItype').is(':checked')) {
          NIItypeVal = 1;
        }
        formdata = {}
        if(NIItypeVal == 1) {
          formdata.NIItype = NIItypeVal;
        }
        if($('#search_title').val().length > 0) {
          formdata.search_title = $('#search_title').val();
        }
        if($('#search_creator').val().length > 0) {
          formdata.search_creator = $('#search_creator').val();
        }
        if($('#subject').val().length > 0) {
          formdata.subject = $('#subject').val();
        }
        if($('#search_sh').val().length > 0) {
          formdata.search_sh = $('#search_sh').val();
        }
        if($('#description').val().length > 0) {
          formdata.description = $('#description').val();
        }
        if($('#search_publishe').val().length > 0) {
          formdata.search_publishe = $('#search_publishe').val();
        }
        if($('#search_contributor').val().length > 0) {
          formdata.search_contributor = $('#search_contributor').val();
        }
        if($('#date_start').val().length > 0) {
          formdata.date_s = $('#date_start').val();
        }
        if($('#date_end').val().length > 0) {
          formdata.date_e = $('#date_end').val();
        }
        if($('#itemtype').val().length > 0) {
          formdata.itemtype = $('#itemtype').val();
        }
        if($('#format').val().length > 0) {
          formdata.format = $('#format').val();
        }
        if($('#search_id').val().length > 0) {
          formdata.search_id = $('#search_id').val();
        }
        if($('#jtitle').val().length > 0) {
          formdata.jtitle = $('#jtitle').val();
        }
        if($('#dateofissued_start').val().length > 0) {
          formdata.dateofissued_s = $('#dateofissued_start').val();
        }
        if($('#dateofissued_end').val().length > 0) {
          formdata.dateofissued_e = $('#dateofissued_end').val();
        }
        if($('#language').val().length > 0) {
          formdata.language = $('#language').val();
        }
        if($('#search_spatial').val().length > 0) {
          formdata.search_spatial = $('#search_spatial').val();
        }
        if($('#search_temporal').val().length > 0) {
          formdata.search_temporal = $('#search_temporal').val();
        }
        if($('#rights').val().length > 0) {
          formdata.rights = $('#rights').val();
        }
        if($('#textversion').val().length > 0) {
          formdata.textversion = $('#textversion').val();
        }
        if($('#grantid').val().length > 0) {
          formdata.grantid = $('#grantid').val();
        }
        if($('#dateofgranted_start').val().length > 0) {
          formdata.dateofgranted_s = $('#dateofgranted_start').val();
        }
        if($('#dateofgranted_end').val().length > 0) {
          formdata.dateofgranted_e = $('#dateofgranted_end').val();
        }
        if($('#degreename').val().length > 0) {
          formdata.degreename = $('#degreename').val();
        }
        if($('#grantor').val().length > 0) {
          formdata.grantor = $('#grantor').val();
        }
        if($("input[ng-model='vm.userQuery']").val().length > 0) {
          formdata.q = $("input[ng-model='vm.userQuery']").val();
        }

        var search_url = $(location).attr('protocol')+"//"+	$(location).attr('host')+$(location).attr('pathname');
        queryObj = query_to_hash($(location).attr('search').substr(1));
        if(queryObj.hasOwnProperty('page')) {
          formdata.page = queryObj.page;
        }
        if(queryObj.hasOwnProperty('size')) {
          formdata.size = queryObj.size;
        }
        if(queryObj.hasOwnProperty('sort')) {
          formdata.sort = queryObj.sort;
        }
        window.location.href = search_url+'?'+$.param(formdata);
      });
    });
})
