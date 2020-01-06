require([
        "jquery",
        "bootstrap"
    ], function() {
        $('.tb-todo').removeClass('hide');
        $('.tb-todo').each(function(index) {
            $(this).children(':first-child').text(index + 1);
        });
        $('.activity_tab').on('click', function() {
            $('.activity_li').removeClass('active');
            $(this).parent().addClass('active');
            tab_name = $(this).data('show-tab');
            $('.tb-todo').addClass('hide');
            $('.tb-wait').addClass('hide');
            $('.tb-all').addClass('hide');
            $('.tb-' + tab_name).each(function(index) {
                $(this).removeClass('hide');
                $(this).children(':first-child').text(index + 1);
            });
        });

  $('#btn_send_mail').click(function () {
    $('#popup_send').addClass('in').css('display', 'block');
  });
  $('#btn_close').click(function () {
    $('#popup_send').removeClass('in').css('display', 'none');
  });
  $('#btn_approve').click(function () {
    let approvePopup = $('#popup_approve');
    approvePopup.append('<div class="spinner"></div>');
    approvePopup.css('opacity', '0.5');
    let mail_template = $("#setTemplate").val();
    list_checkboxes.forEach(activity_id => {
      $.ajax({
        url: '/workflow/send_mail/' + activity_id + '/' + mail_template,
        method: 'POST',
        success: function () {
        },
        error: function () {
          alert('server error');
        }
      });
    });
    setTimeout(() => {
      $('.spinner').remove();
      $('#popup_approve').css('opacity', '1')
      $('#popup_success').addClass('in').css('display', 'block');
    }, 2000);
    // 15745
  });

  //Click button OK
  $('#btn_success').click(function () {
    $("#btn_Next").attr('disabled', true);
    $('#popup_success, #popup_approve').removeClass('in').css('display', 'none');
    $(".checkbox-class, #checkAll").prop('checked', false);
    listCheckbox();
    list_checkboxes.clear();

  });

  //Click button Confirm
  $('#btn_Next').click(function () {
    $('#appendHTML, #label_template').empty();
    listCheckbox();

    $('#popup_approve').addClass('in').css('display', 'block');
    let rows = wf_Data.filter(activity => list_checkboxes.has(activity.activity_id));
    // let rows;
    let i = 1;
    let appendHtml = $('#appendHTML');
    $.each(rows, function (key, val) {
      if (Object.keys(val).length > 0) {
        const td = `<tr><td>${i}</td>
              <td>${this.activity_id}</td>
              <td>${this.item}</td>
              <td>${this.email}</td></tr>`;
        appendHtml.append(td);
        i++;
      }
    });

    let labelTemplate = $("#setTemplate :selected").text();
    $('#label_template').append(labelTemplate);
  });

  //Click button close and Back
  $('#btn_close_pop2, #btn_back').click(function () {
    $('#popup_approve').removeClass('in').css('display', 'none');
  });

    //Click button check all
  $("#checkAll").click(function () {
    let nextButton = $("#btn_Next");
    if ($(this).is(":checked")) {
      $(".checkbox-class:not(:checked)").prop("checked", true);
      wf_Data.forEach(activity => {
        list_checkboxes.add(activity.activity_id);
      });
      nextButton.removeAttr("disabled");
    } else {
      $(".checkbox-class").prop("checked", false);
      list_checkboxes.clear();
      nextButton.attr('disabled', true);
    }
  });

    listCheckbox();
  }
);
const workFlowData = $("#work-flow-data").text();
var wf_Data = JSON.parse(workFlowData);

var list_checkboxes = new Set();

var req_per_page = $("#req_per_page").text();

// on page load collect data to load pagination as well as table
const data = {"req_per_page": req_per_page, "page_no": 1};

// At a time maximum allowed pages to be shown in pagination div

var pagination_visible_pages = $("#pagination_visible_pages").text();


// hide pages from pagination from beginning if more than pagination_visible_pages
function hide_from_beginning(element) {
  if (element.style.display === "" || element.style.display === "block") {
    element.style.display = "none";
  } else {
    hide_from_beginning(element.nextSibling);
  }
}

// hide pages from pagination ending if more than pagination_visible_pages
function hide_from_end(element) {
  if (element.style.display === "" || element.style.display === "block") {
    element.style.display = "none";
  } else {
    hide_from_beginning(element.previousSibling);
  }
}

// load data and style for active page
function active_page(element, rows, req_per_page) {
  var current_page = document.getElementsByClassName('active-page');
  var next_link = document.getElementById('next_link');
  var prev_link = document.getElementById('prev_link');
  var next_tab = current_page[0].nextSibling;
  var prev_tab = current_page[0].previousSibling;
  current_page[0].className = current_page[0].className.replace("active-page", "");
  if (element === "next") {
    if (parseInt(next_tab.text).toString() === 'NaN') {
      next_tab.previousSibling.className += " active-page";
      next_tab.setAttribute("onclick", "return false");
    } else {
      next_tab.className += " active-page"
      render_table_rows(rows, parseInt(req_per_page), parseInt(next_tab.text));
      if (prev_link.getAttribute("onclick") === "return false") {
        prev_link.setAttribute("onclick", `active_page('prev',\"${rows}\",${req_per_page})`);
      }
      if (next_tab.style.display === "none") {
        next_tab.style.display = "block";
        hide_from_beginning(prev_link.nextSibling)
      }
    }
  } else if (element === "prev") {
    if (parseInt(prev_tab.text).toString() === 'NaN') {
      prev_tab.nextSibling.className += " active-page";
      prev_tab.setAttribute("onclick", "return false");
    } else {
      prev_tab.className += " active-page";
      render_table_rows(rows, parseInt(req_per_page), parseInt(prev_tab.text));
      if (next_link.getAttribute("onclick") === "return false") {
        next_link.setAttribute("onclick", `active_page('next',\"${rows}\",${req_per_page})`);
      }
      if (prev_tab.style.display === "none") {
        prev_tab.style.display = "block";
        hide_from_end(next_link.previousSibling)
      }
    }
  } else {
    element.className += "active-page";
    render_table_rows(rows, parseInt(req_per_page), parseInt(element.text));
    if (prev_link.getAttribute("onclick") === "return false") {
      prev_link.setAttribute("onclick", `active_page('prev',\"${rows}\",${req_per_page})`);
    }
    if (next_link.getAttribute("onclick") === "return false") {
      next_link.setAttribute("onclick", `active_page('next',\"${rows}\",${req_per_page})`);
    }
  }
}

// Render the table's row in table request-table
function render_table_rows(rows, req_per_page, page_no) {
  const response = JSON.parse(window.atob(rows));
  const resp = response.slice(req_per_page * (page_no - 1), req_per_page * page_no);
  $('.check_table').empty();
  var count = req_per_page * (page_no - 1) + 1;
  resp.forEach(function (element, index) {
    if (Object.keys(element).length > 0) {
      const {activity_id, item, work_flow, status, email} = element;
      let activityId = activity_id;
      if (list_checkboxes.has(activityId.toString())) {
        const td = `<tr id = "${activity_id}"><td scope="row" class="col_empty"><input class="checkbox-class" type="checkbox" checked value="${activityId}"/></td>
          <td class="col_empty">${count++}</td>
          <td class="activity_id">${activity_id}</a></td>
          <td>${item}</td>

          <td class="col_empty">${work_flow}</td>
          <td class="col_empty">${status}</td>
          <td>${email}</td></tr>`;
        $('.check_table').append(td);

      } else {
        const td = `<tr id = "${activity_id}"><td scope="row" class="col_empty"><input class="checkbox-class" type="checkbox" value="${activityId}"/></td>
          <td class="col_empty">${count++}</td>
          <td class="activity_id">${activity_id}</a></td>
          <td>${item}</td>
          <td class="col_empty">${work_flow}</td>
          <td class="col_empty">${status}</td>
          <td>${email}</td></tr>`;
        $('.check_table').append(td)
      }
    }
  });
  listCheckbox();
}

// Pagination logic implementation
function pagination(data, wf_Data) {
  const all_data = window.btoa(JSON.stringify(wf_Data));
  $(".pagination").empty();
  if (data.req_per_page !== 'ALL') {
    let pager = `<a href="#" id="prev_link" onclick=active_page('prev',\"${all_data}\",${data.req_per_page})>&laquo;</a>` +
      `<a href="#" class="active-page" onclick=active_page(this,\"${all_data}\",${data.req_per_page})>1</a>`;
    const total_page = Math.ceil(parseInt(wf_Data.length) / parseInt(data.req_per_page));
    if (total_page < pagination_visible_pages) {
      render_table_rows(all_data, data.req_per_page, data.page_no);
      for (let num = 2; num <= total_page; num++) {
        pager += `<a href="#" onclick=active_page(this,\"${all_data}\",${data.req_per_page})>${num}</a>`;
      }
    } else {
      render_table_rows(all_data, data.req_per_page, data.page_no);
      for (let num = 2; num <= pagination_visible_pages; num++) {
        pager += `<a href="#" onclick=active_page(this,\"${all_data}\",${data.req_per_page})>${num}</a>`;
      }
      for (let num = pagination_visible_pages + 1; num <= total_page; num++) {
        pager += `<a href="#" style="display:none;" onclick=active_page(this,\"${all_data}\",${data.req_per_page})>${num}</a>`;
      }
    }
    pager += `<a href="#" id="next_link" onclick=active_page('next',\"${all_data}\",${data.req_per_page})>&raquo;</a>`;
    $(".pagination").append(pager);
  } else {
    render_table_rows(all_data, wf_Data.length, 1);
  }
}

//calling pagination function
pagination(data, wf_Data);

//Array to hold the checked ids

//Event listener to detect changes
function listCheckbox() {
  $('#appendHTML').empty();
  $('.checkbox-class').change(function () {
    var id = $(this).parents('tr').attr('id');
    if ($(this).is(":checked")) {
      list_checkboxes.add(id);
      $("#btn_Next").removeAttr('disabled');
    } else {
      list_checkboxes.delete(id);
      $("#checkAll").prop("checked", false);
      if (list_checkboxes.size == 0) {
        $("#btn_Next").attr('disabled', true);
      }
    }
  });
}
