let response_data = null;

$(document).ready(function () {
    let bucket_id = document.getElementById("bucket_id").innerText;
    let file_key = document.getElementById("file_key").innerText;

    statsurl = '/api/stats/' + bucket_id + '/' + file_key
    $.ajax({
        url: statsurl,
        type: 'GET',
        contentType: 'application/json; charset=UTF-8',
        success: function(data) {
            if (data != null && 'download_total' in data && 'preview_total' in data) {
                response_data = data;
                // total
                document.getElementById("file_download_num").innerHTML = data.download_total;
                document.getElementById("file_preview_num").innerHTML = data.preview_total;
                // period
                let ddl = document.getElementById("file_period");
                let ddlHtml = ddl.innerHTML;
                for (let key in data.period) {
                    ddlHtml += '<option value=' + key + '>' + key + '</option>';
                }
                ddl.innerHTML = ddlHtml;
                // domain
                let tableHtml = '';
                for (let i in data.domain_list) {
                    d = data.domain_list[i]
                    tableHtml += '<tr><td>' + d.domain + '</td><td>' + 
                        d.download_counts + '</td><td>' + 
                        d.preview_counts + '</td></tr>';
                }
                document.getElementById("file_domain").innerHTML = tableHtml;
            } else {
                document.getElementById("file_download_num").innerHTML = 0;
                document.getElementById("file_preview_num").innerHTML = 0;
            }
        },
        error: function() {
            document.getElementById("file_download_num").innerHTML = 0;
            document.getElementById("file_preview_num").innerHTML = 0;
        }
    });
});

function period_change(control) {
    date = control.value;
    if (response_data != null) {
        data = null
        if (date == 'total') {
            data = response_data;
        } else {
            data = response_data.period[date];
        }
        if (data != null) {
            document.getElementById("file_download_num").innerHTML = data.download_total;
            document.getElementById("file_preview_num").innerHTML = data.preview_total;
            let tableHtml = '';
            for (let i in data.domain_list) {
                d = data.domain_list[i]
                tableHtml += '<tr><td>' + d.domain + '</td><td>' +
                    d.download_counts + '</td><td>' +
                    d.preview_counts + '</td></tr>';
            }
            document.getElementById("file_domain").innerHTML = tableHtml;
        }
    }
}
