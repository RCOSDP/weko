import $ from 'jquery';

$(document).ready(function () {
    $('#add_row').on('click', function () {
        var currentLength = parseInt($('#ip_addresses_length').val());

        $(makeRow(currentLength)).insertBefore('#remove_row');
        $('#ip_address_' + currentLength).append(' &nbsp;');
        $('#ip_addresses_length').val((currentLength + 1));
    });

    $('#remove_row').on('click', function () {
        var currentLength = parseInt($('#ip_addresses_length').val());
        if (currentLength > 1) {
            for (var i = 0; i < 3; i++) {
                $('#remove_row').prev().remove();
            }
            $('#ip_addresses_length').val((currentLength - 1));
        }
    });

    // Restrict input to numbers
    $('.ip-address-input').keyup(function () {
        var cleanValue = $(this).val().replace(/[^0-9]+/g, '');
        $(this).val(cleanValue);
    });

    $('#submit_button').on('click', function () {
        $('#log_analysis_form').submit();
    });
});

function makeRow(index) {
    var parentId = 'ip_address_' + index;
    var listId = 'address_list_' + index;
    return '<p></p><br/><div id="' + parentId + '" class="form-group">' + '\n' +
        '<input name="' + listId + '" id="' + parentId + '_0' + '" type="text" class="ip-address-input form-control input-sm" size="1" maxlength="3" placeholder="0"> . ' + '\n' +
        '<input name="' + listId + '" id="' + parentId + '_1' + '" type="text" class="ip-address-input form-control input-sm" size="1" maxlength="3" placeholder="0"> . ' + '\n' +
        '<input name="' + listId + '" id="' + parentId + '_2' + '" type="text" class="ip-address-input form-control input-sm" size="1" maxlength="3" placeholder="0"> . ' + '\n' +
        '<input name="' + listId + '" id="' + parentId + '_3' + '" type="text" class="ip-address-input form-control input-sm" size="1" maxlength="3" placeholder="0">' + '\n' +
        '</div>&nbsp;&nbsp;' + '\n';
}
