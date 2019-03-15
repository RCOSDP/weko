require([
  "jquery",
  "bootstrap"
], function () {
  $(document).ready(function() {
    var journalNames = [];
    var actionJournal = {};

    var getJournalsTimer = null;
    // For IME
    $('#search-key').on('keydown', function(e) {
      if (e.keyCode == 229){
        clearTimeout(getJournalsTimer);
        getJournalsTimer = setTimeout(function(){ getJournals(); }, 1000);
      }
    });

    // For Delete, Backspace
    $('#search-key').on('keyup', function(e) {
      if (e.keyCode == 46 || e.keyCode == 8){
        clearTimeout(getJournalsTimer);
        getJournalsTimer = setTimeout(function(){ getJournals(); }, 1000);
      }
    });

    $('#search-key').on('keypress', function() {
      clearTimeout(getJournalsTimer);
      getJournalsTimer = setTimeout(function(){ getJournals(); }, 1000);
    });

    function getJournals() {
      var keyword = $('#search-key').val();
      if(keyword && $.trim(keyword).length >= 1){
        var key = $.trim(keyword);

        var getJournalUrl = '/workflow/journal/list?key=' + key;
        $.ajax({
          method: 'GET',
          url: getJournalUrl,
          async: true,
          success: function(data, status) {
            if(data.romeoapi && parseInt(data.romeoapi.header.numhits) > 0) {
              journalNames = [];
              var journals = data.romeoapi.journals.journal;

              var options = '';
              if(parseInt(data.romeoapi.header.numhits) == 1) {
                options = '<option value="' + journals.jtitle + '">';
                journalNames.push(journals.jtitle);

              }else {
                $.each(journals, function(index, journal) {
                  var html = '<option value="' + journal.jtitle + '">';
                  options =options + html;

                  journalNames.push(journal.jtitle);
                });
              }

              $('datalist#journal-list option').remove();
              $("#journal-list").append(options);
            } else {
              $('datalist#journal-list option').remove();
            }
          },
          error: function(status, error) {
            alert(error);
          }
        });
      }
    }

    $('#search-key').on('change', function() {
      var key = $(this).val();

      if($.inArray(key, journalNames) !== -1) {
        $('#journal-info').attr('hidden', 'hidden');
        actionJournal = {};

        var title = key;
        var issn = '';
        var href = '';
        var romeo_msg = 'Unknown';
        var paid_msg = 'Unknown';

        var getJournalUrl = '/workflow/journal?title=' + title;
        $.ajax({
          method: 'GET',
          url: getJournalUrl,
          async: true,
          success: function(data, status) {
            if(data.romeoapi && parseInt(data.romeoapi.header.numhits) > 0) {

              var journal = data.romeoapi.journals.journal;

              var publisher = null;
              if(data.romeoapi.publishers) publisher = data.romeoapi.publishers.publisher;

              if(journal.issn) {
                issn = journal.issn;
                href = 'http://www.sherpa.ac.uk/romeo/search.php?issn=' + issn;
              }

              // Set title line
              titleLine = title + ' (ISSN: ' + issn + ')'
              $('#journal-title').text(titleLine);

              if(href){$('#journal-title').append('&nbsp;&nbsp;<a href="'+ href + '" target="_blank">Detail</a>');}

              // Get RoMEO Color
              if(publisher && publisher.romeocolour) {
                romeo_msg = 'This is a RoMEO ' + publisher.romeocolour + ' journal.';
              }
              $('#romeo-color').text(romeo_msg);

              // Get paid access notes
              if(publisher && publisher.paidaccess && publisher.paidaccess.paidaccessnotes) {
                paid_msg = publisher.paidaccess.paidaccessnotes;
              }
              $('#paid-msg').text(paid_msg);

              $('#journal-info').removeAttr('hidden');

              // Set action journal
              actionJournal['keywords'] = journal.jtitle;

              if (journal.issn) {
                actionJournal['issn'] = journal.issn;
                actionJournal['href'] = 'http://www.sherpa.ac.uk/romeo/search.php?issn=' + journal.issn;
              }
              actionJournal['romeo_msg'] = romeo_msg;
              actionJournal['paid_msg'] = paid_msg;

              $('#action-journal').text(JSON.stringify(actionJournal));
            }
          },
          error: function(status, error) {
            alert(error);
          }
        });
      }
    });
  })

})
