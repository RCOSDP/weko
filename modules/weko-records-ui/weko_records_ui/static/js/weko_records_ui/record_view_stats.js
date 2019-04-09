
$(document).ready(function () {  
    let record_id = document.getElementById("record_id").innerText;
    let statsurl = '/api/stats/' + record_id
    $.ajax({
        url: statsurl,
        type: 'GET',
        contentType: 'application/json; charset=UTF-8',
        success: function(data) {
            if (data != null && 'total' in data) {
                // total
                document.getElementById("record_view_num").innerHTML = data.total;
                // period
                let ddl = document.getElementById("record_view_period");
                let ddlHtml = ddl.innerHTML;
                for (let i in data.period) {
                    ddlHtml += '<option value=' + data.period[i] + '>' + data.period[i] + '</option>';
                }
                ddl.innerHTML = ddlHtml;
                // domain
                let tableHtml = '';
                for (let key in data.domain) {
                    tableHtml += '<tr><td>' + key + '</td><td>' + data.domain[key] + '</td></tr>';
                }
                document.getElementById("record_view_domain").innerHTML = tableHtml;
            } else {
                document.getElementById("record_view_num").innerHTML = 0;
                document.getElementById("record_view_domain").innerHTML = '';
            }
        },
        error: function() {
            document.getElementById("record_view_num").innerHTML = 0;
            document.getElementById("record_view_domain").innerHTML = '';
        }
    });
});

function period_change (control) {
    date = control.value;
    let record_id = document.getElementById("record_id").innerText;
    let statsurl = '/api/stats/' + record_id;
    $.ajax({
        url: statsurl,
        type: 'POST',
        data: '{"date": "' + date + '"}',
        contentType: 'application/json; charset=UTF-8',
        success: function(data) {
            if (data != null && 'total' in data) {
                document.getElementById("record_view_num").innerHTML = data.total;
                let tableHtml = '';
                for (let key in data.domain) {
                    tableHtml += '<tr><td>' + key + '</td><td>' + data.domain[key] + '</td></tr>';
                }
                document.getElementById("record_view_domain").innerHTML = tableHtml;
            }
        },
        error: function(data) {
            document.getElementById("record_view_num").innerHTML = 0;
            document.getElementById("record_view_domain").innerHTML = '';
        }
    });
}
