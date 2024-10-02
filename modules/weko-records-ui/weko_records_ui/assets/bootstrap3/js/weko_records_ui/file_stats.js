$(document).ready(function () {
    let bucket_id = document.getElementById("bucket_id").innerText;
    let file_key = ''
    try {
        file_key = document.getElementById("file_key").innerText;
    } catch(e) {
        file_key = encodeURIComponent(document.getElementById("file_url").innerText.replaceAll('/', '{URL_SLASH}'));
    }

    statsurl = '/api/stats/' + bucket_id + '/' + file_key
    $.ajax({
        url: statsurl,
        type: 'GET',
        contentType: 'application/json; charset=UTF-8',
        success: function(data) {
            if (data != null && 'download_total' in data && 'preview_total' in data) {
                // total
                document.getElementById("file_download_num").innerHTML = data.download_total;
                document.getElementById("file_preview_num").innerHTML = data.preview_total;
                // period
                let ddl = document.getElementById("file_period");
                let ddlHtml = ddl.innerHTML;
                for (let i in data.period) {
                    ddlHtml += '<option value=' + data.period[i] + '>' + data.period[i] + '</option>';
                }
                ddl.innerHTML = ddlHtml;
                // country
                let tableHtml = '';
                for (let i in data.country_list) {
                    d = data.country_list[i]
                    tableHtml += '<tr><td>' + d.country + '</td><td>' + 
                        d.download_counts + '</td><td>' + 
                        d.preview_counts + '</td></tr>';
                }
                document.getElementById("file_country").innerHTML = tableHtml;
            } else {
                document.getElementById("file_download_num").innerHTML = 0;
                document.getElementById("file_preview_num").innerHTML = 0;
                document.getElementById("file_country").innerHTML = '';
            }
        },
        error: function() {
            document.getElementById("file_download_num").innerHTML = 0;
            document.getElementById("file_preview_num").innerHTML = 0;
            document.getElementById("file_country").innerHTML = '';
        }
    });
});

function period_change(control) {
    date = control.value;
    let bucket_id = document.getElementById("bucket_id").innerText;
    let file_key = document.getElementById("file_key").innerText;
    let statsurl = '/api/stats/' + bucket_id + '/' + file_key;
    $.ajax({
        url: statsurl,
        type: 'POST',
        data: '{"date": "' + date + '"}',
        contentType: 'application/json; charset=UTF-8',
        success: function(data) {
            if (data != null && 'download_total' in data && 'preview_total' in data) {
                document.getElementById("file_download_num").innerHTML = data.download_total;
                document.getElementById("file_preview_num").innerHTML = data.preview_total;
                let tableHtml = '';
                for (let i in data.country_list) {
                    d = data.country_list[i]
                    tableHtml += '<tr><td>' + d.country + '</td><td>' +
                        d.download_counts + '</td><td>' +
                        d.preview_counts + '</td></tr>';
                }
                document.getElementById("file_country").innerHTML = tableHtml;
            } else {
                document.getElementById("file_download_num").innerHTML = 0;
                document.getElementById("file_preview_num").innerHTML = 0;
                document.getElementById("file_country").innerHTML = '';
            }
        },
        error: function() {
            document.getElementById("file_download_num").innerHTML = 0;
            document.getElementById("file_preview_num").innerHTML = 0;
            document.getElementById("file_country").innerHTML = '';
        }
    });
}
