// Confirm manual send
$('#confirm_send_button').on('click', function () {
    $("#manual_send_mail").attr('disabled', true);
    $("#manual_send_mail").attr('data-target', null);
    let s = Number($("#from_year_select").val() + paddingLeft($("#from_month_select").val(), 2));
    let e = Number($("#to_year_select").val() + paddingLeft($("#to_month_select").val(), 2));
    if (s > e) {
        alert('Selected period is wrong!');
        return;
    }
    let start_month = $("#from_year_select").val() + '-' + paddingLeft($("#from_month_select").val(), 2); 
    let end_month = $("#to_year_select").val() + '-' + paddingLeft($("#to_month_select").val(), 2);
    $.ajax({
        url: '/api/admin/sitelicensesendmail/send/' + start_month + '/' + end_month,
        type: 'POST',
        success: function (data) {
            alert('Send successfully');
        },
        error: function (error) {
            console.log(error);
            alert('Send erroneously');
        }
    });
    $('#send_mail_confirm_modal').modal('hide');
    $("#manual_send_mail").attr('data-target', '#send_mail_confirm_modal');
    $("#manual_send_mail").attr('disabled', null);
});

$('input:radio[name="dis_enable_auto_send"]').change(function() {
    //document.getElementById("manual_send_mail").enabled = false
    $("#manual_send_mail").attr('disabled', true);
    $("#manual_send_mail").attr('data-target', null);
});

let checked_list = {};
$('input:checkbox[id^="send_mail_flag_"]').change(function() {
    $("#manual_send_mail").attr('disabled', true);
    $("#manual_send_mail").attr('data-target', null);
    checked_list[$(this)[0].name] = $(this)[0].checked ? 'T': 'F';
});

$('#save_settings').on('click', function() {
    let auto_send_flag = $('input:radio[id="enable_auto_send"]')[0].checked ? true : false;
    //let check_list = document.querySelectorAll("[id^=send_mail_flag_]");
    let data = {};
    data['auto_send_flag'] = auto_send_flag;
    data['checked_list'] = checked_list
    $.ajax({
        url: '/admin/sitelicensesendmail/',
        type: "POST",
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function (data) {
            alert('Update successfully');
            location.reload();
        },
        error: function (error) {
            console.log(error);
            alert('Update erroneously');
            location.reload();
        }
    });
});

function paddingLeft(str,lenght){
    if(str.length >= lenght)
    return str;
    else
    return paddingLeft("0" +str,lenght);
}
