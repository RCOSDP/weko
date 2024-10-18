(function(angular) {
    angular.element(document).ready(function() {
        angular.module('wekoRecordDetails.controllers', [
            'ngAnimate', 'ngSanitize', 'mgcrea.ngStrap', 'mgcrea.ngStrap.modal'
        ]);

        function ItemController($scope, $modal, $http, $window) {
            $scope.openConfirm = function(message, url, rdt, id) {
                var confirmModalScope = $scope.$new();
                confirmModalScope.modalInstance = $modal({
                    templateUrl: "confirm-modal.html",
                    controller: 'ConfirmController',
                    scope: confirmModalScope,
                    show: false,
                    resolve: {
                        msg: function() {
                            return message;
                        },
                        url: function() {
                            return url;
                        },
                        rdt: function() {
                            return rdt;
                        },
                        id: function() {
                            return id;
                        }
                    }
                });
                // Resolve promise and show modal
                confirmModalScope.modalInstance.$promise.then(
                    confirmModalScope.modalInstance.show);
            };

            $scope.showChangeLog = function(deposit) {
                // call api for itself to catch field deposit
                // Call service to catch version by deposit with api /api/files/
                $('#bodyModal').children().remove();
                $http({
                    method: 'GET',
                    url: "/api/files/" + deposit + "?versions",
                }).then(function successCallback(response) {
                    $('#bodyModal').append(createRow(response['data']));
                    if ($('#billing_file_permission').val()) {
                        handleDownloadBillingFile(true);
                    }
                }, function errorCallback(response) {
                    console.log('Error when trigger api /api/files');
                });
            }

            versionPrivacyChanged = function(bucket_id, key, version_id, index, radio) {
                var showVersionPrivacyLoading = function(show) {
                    if (show) {
                        $("#version_radios_" + index).addClass('hidden');
                        $("#version_loading_" + index).removeClass('hidden');
                    } else {
                        $("#version_loading_" + index).addClass('hidden');
                        $("#version_radios_" + index).removeClass('hidden');
                    }
                }

                var revertCheckedStatus = function(value) {
                    if (value == 1) {
                        // Change radio 0 to checked
                        $("input[name=radio_" + index + "][value='0']").prop("checked", true);
                    } else {
                        // Change radio 1 to checked
                        $("input[name=radio_" + index + "][value='1']").prop("checked", true);
                    }
                }

                // Call the API to change the privacy status of version
                // If api success, show the download link (attach to version file name) if public checked
                // Otherwise, revert the checked status and do nothing + output error to console
                var updateVersionPrivacy = function(value) {
                    $.ajax({
                        method: 'PUT',
                        url: '/file_version/update',
                        async: true,
                        cache: false,
                        data: {
                            "bucket_id": bucket_id,
                            "key": key,
                            "version_id": version_id,
                            "is_show": value
                        },
                        success: function(data, status, xhr) {
                            showVersionPrivacyLoading(false);

                            if (data.status != 1) {
                                // Revert the checked radio
                                revertCheckedStatus(radio.value);
                                // Log to console
                                console.log(data.msg);
                            }
                        },
                        error: function(status, error) {
                            showVersionPrivacyLoading(false);
                            // Revert the checked radio
                            revertCheckedStatus(radio.value);
                            // Log to console
                            console.log(error);
                        }
                    });
                }

                showVersionPrivacyLoading(true);
                updateVersionPrivacy(radio.value);
            }

            function createRow(response) {
                let results = '';
                const bucket_id = response.id;
                const contents = response.contents;
                response.contents.sort(function(first, second) {
                    return second.updated - first.updated;
                });
                let txt_filename = $('#txt_filename').val();
                let txt_show = $('#txt_show').val();
                let txt_hide = $('#txt_hide').val();
                let is_logged_in = $('#txt_is_logged_in').val();
                let can_update_version = $('#txt_can_update_version').val();
                let billing_file_permission = $('#billing_file_permission').val();
                let billing_file_price = $('#billing_file_price').val();

                // Remove the versions which does not match the current file
                for (let index = 0; index < contents.length; index++) {
                    const ele = contents[index];
                    if (ele.key != txt_filename) {
                        // Remove this item
                        contents.splice(index, 1);
                        index--;
                    }
                }

                for (let index = 0; index < contents.length; index++) {
                    const ele = contents[index];

                    const version_id = ele.version_id;
                    const key = ele.key;
                    const nameRadio = "radio_" + index;
                    let checked = ele.is_show ? " checked " : "";
                    let radio = index == 0 || can_update_version == 'False' ? "" :
                        '<div id="version_radios_' + index + '" class="radio">' +
                        '<label style="margin-left: 5px">' +
                        '<input type="radio" name="' + nameRadio + '" value="1" ' + checked + ' onchange="versionPrivacyChanged(\'' + bucket_id + ', ' + key + '\', \'' + version_id + '\', ' + index + ', this)">' + txt_show +
                        '</label>' +
                        '<label style="margin-left: 5px">' +
                        '<input type="radio" name="' + nameRadio + '" value="0" ' + checked + ' onchange="versionPrivacyChanged(\'' + bucket_id + '\', \'' + key + '\', \'' + version_id + '\', ' + index + ', this)">' + txt_hide +
                        ' <label >' +
                        '</div>' +
                        '<div id = "version_loading_' + index + '"' +
                        'class = "hidden fa fa-circle-o-notch fa-spin text-center" > < /div>';
                    // if (!isPublished) {
                    //   radio = `
                    //     <div class="radio">
                    //       <div class="row">
                    //         <div>
                    //             <label><input type="radio" name="${nameRadio}">Published</label>
                    //         </div>
                    //         <div>
                    //           <label><input type="radio" name="${nameRadio}" checked>Private</label>
                    //         </div>
                    //       </div>
                    //     </div>
                    //   `;
                    // }

                    let version = contents.length - index;
                    if (index === 0) {
                        version = 'Current';
                    }

                    if (ele.links.self == '') {
                        // User does not have the permission to show this version, so that we would not render this row
                        continue;
                    }

                    // Hide the extension
                    var filename = ele.key;
                    var lastIndex = filename.lastIndexOf(".");
                    if (lastIndex != -1) {
                        filename = filename.substr(0, lastIndex);
                    }
                    if (filename == "") {
                        filename = ele.key
                    }
                    let txt_link;
                    if (billing_file_permission) {
                        let selfLink = "";
                        let permission = "data-billing-file-permission=";
                        if (billing_file_permission === "True") {
                            selfLink = 'data-billing-file-url="' + ele.links.self + '"';
                            permission += '"true" data-billing-file-price="' + billing_file_price + '"';
                        } else {
                            permission += '"false"';
                        }
                        txt_link = '<a class="billing-file-version"' + permission + selfLink + 'href="javascript:void(0);">' + filename + '</a>';
                    } else {
                        txt_link = '<a href="' + ele.links.self + '">' + filename + '</a>';
                    }

                    let size = formatBytes(ele.size, 2);

                    // Checksum
                    var checksum = ele.checksum
                    var checksumIndex = ele.checksum.indexOf(":")
                    if (checksumIndex != -1) {
                        checksum = ele.checksum.substr(0, checksumIndex) + "<span class=\"wrap\">" + ele.checksum.substr(checksumIndex + 1) + "</span>";
                    }

                    var username = '';
                    if (is_logged_in == 'True' && ele.uploaded_owners && ele.uploaded_owners.created_user) {
                        username = ele.uploaded_owners.created_user.username;
                    }
                    results += '<tr>' +
                        '<td>' + version + '</td>' +
                        '<td class="nowrap">' + formatDate(new Date(ele.updated)) + '</td>' +
                        '<td>' + txt_link + '</td>' +
                        '<td>' + size + '</td>' +
                        '<td class="wrap">' + checksum + '</td>' +
                        '<td class="nowrap">' + username + '</td>' +
                        '<td>' + radio + '</td>' +
                        '</tr>';

                }
                return results;
            }

            function formatDate(date) {
                let month = '' + (date.getMonth() + 1);
                let day = '' + date.getDate();
                let year = date.getFullYear();

                let hour = '' + date.getHours();
                let minute = '' + date.getMinutes();
                let second = '' + date.getSeconds();

                if (month.length < 2) month = '0' + month;
                if (day.length < 2) day = '0' + day;
                if (hour.length < 2) hour = '0' + hour;
                if (minute.length < 2) minute = '0' + minute;
                if (second.length < 2) second = '0' + second;

                return [year, month, day].join('-') + '\t' + [hour, minute, second].join(':');
            }

            function formatBytes(a, b) {
                if (0 == a) return "0 Bytes";
                var c = 1024,
                    d = b || 2,
                    e = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
                    f = Math.floor(Math.log(a) / Math.log(c));
                return parseFloat((a / Math.pow(c, f)).toFixed(d)) + " (" + e[f] + ")";
            }
        }

        // Inject depedencies
        ItemController.$inject = [
            '$scope',
            '$modal',
            '$http',
            '$window',
        ];

        //function ConfirmController($scope, $modalInstance, msg) {
        function ConfirmController($scope, $http, $window, msg, url, rdt, id) {
            $scope.message = msg;

            $scope.ok = function() {
                $scope.modalInstance.hide();
                $('body').removeClass('modal-open');
                $http({
                    method: 'GET',
                    url: "/api/items/check_record_doi/" + id,
                }).then(function successCallback(response) {
                    if (0 == response.data.code) {
                        $('[role="alert"]').css('display', 'inline-block');
                        $('[role="alert"]').text($("#delete_message").val());
                      } else {
                        $http.post(url).then(
                            function(response) {
                                if (response.data.code === -1 && response.data.is_locked) {
                                    $('[role="alert"]').css('display', 'inline-block');
                                    $('[role="alert"]').text(response.data.msg);
                                } else {
                                    // success callback
                                    $window.location.href = rdt;
                                }
                            },
                            function(response) {
                                // failure call back
                                console.log(response);
                            }
                        );
                      };
                }, function errorCallback(response) {
                    console.log('Error api /api/items/check_public_status');
                });
            };

            $scope.cancel = function() {
                $scope.modalInstance.hide();
                $('body').removeClass('modal-open');
            };
        };

        // Register controllers
        angular.module('wekoRecordDetails.controllers')
            .controller('ItemController', ItemController)
            .controller('ConfirmController', ConfirmController);

        angular.module('wekoRecordDetails', [
            'wekoRecordDetails.controllers'
        ]);

        // Strap it to element(initialize)
        angular.bootstrap(document.getElementById('detail-item'), [
            'wekoRecordDetails', 'ngAnimate', 'ngSanitize', 'mgcrea.ngStrap',
            'mgcrea.ngStrap.modal'
        ]);
    });
})(angular);

$(function() {
    handleDownloadBillingFile();
    handleConfirmButton();
    handleChargeBillingFile();
});

function handleDownloadBillingFile(isVersionTable) {
    if (isVersionTable === undefined) {
        isVersionTable = false;
    }
    let billingFileHandleName = 'a.billing-file';
    if (isVersionTable) {
        billingFileHandleName = 'a.billing-file-version';
    }
    $(billingFileHandleName).on('click', function() {
        let downloadPermission = $(this).data('billingFilePermission');
        if (downloadPermission) {
            let url = $(this).data('billingFileUrl');
            let price = $(this).data('billingFilePrice');
            let confirmMsg = $("#download_confirm_message").val().replace("XXXXX", price);
            $("#download_confirm_content").text(confirmMsg);
            $("#confirm_download_button").data('billingFileUrl', url);
            $("#confirm_download").modal("show");
        } else {
            let permissionErrorMsg = $("#download_permission_error").val();
            $("#inputModal").html(permissionErrorMsg);
            $("#allModal").modal("show");
        }
    });
}

function handleConfirmButton() {
    $('button#confirm_download_button').on('click', function() {
        let url = $(this).data('billingFileUrl');
        let link = document.createElement("a");
        link.download = "";
        link.href = url;
        link.click();
        $("#confirm_download").modal('toggle');
        $("#download_confirm_content").text("");
    });
}

function handleChargeBillingFile() {
    // 課金ボタン押下時の処理
    $('button#charge-button').on('click', function () {
        const data = $(this).data();
        const message = data.unit + data.price + ' ' + $('#charge_confirmation').val();
        $('#charge_confirmation_message').html(message);
        $('#action_charge_confirmation').modal('show');
    });

    // 課金ボタン押下時の処理（課金確認メッセージOK時の処理）
    $('button#modal_charge').on('click', function () {
        $('#action_charge_confirmation').modal('hide');
        const data = $('button#charge-button').data();
        let params = {
            'item_id': data.itemid,
            'file_name': data.filename,
            'title': data.title,
            'price': data.price,
        }
        params = Object.keys(params).map(key => key + '=' + params[key]).join('&');
        $.ajax({
            url: '/charge' + '?' + params,
            type: 'GET',
            contentType: 'application/json',
            success: function (data) {
                if (data.status == 'success') {
                    $('#success_flag').val('true')
                    // 課金成功メッセージ表示
                    const message = $('#charge_success').val();
                    $('#charge_success_message').html(message);
                    $('#action_charge_success').modal('show');
                }
                else if (data.status == 'already') {
                    // 課金済みメッセージ表示
                    const message = $('#charge_already').val();
                    $('#charge_success_message').html(message);
                    $('#action_charge_success').modal('show');
                }
                else if (data.status == 'credit_error') {
                    // 課金失敗メッセージ表示
                    const message = $('#charge_credit_error').val();
                    $('#charge_success_message').html(message);
                    $('#action_charge_success').modal('show');
                }
                else {
                    // 課金失敗メッセージ表示
                    const message = $('#charge_error').val();
                    $('#charge_success_message').html(message);
                    $('#action_charge_success').modal('show');
                }
            },
            error: function (error) {
                // 課金失敗メッセージ表示
                const message = $('#charge_error').val();
                $('#charge_success_message').html(message);
                $('#action_charge_success').modal('show');
            }
        });
    });

    $('button#charge_modal_ok').on('click', function () {
        $('#action_charge_success').modal('hide');
        if ($('#success_flag').val() == 'true') {
            // 画面を更新
            location.reload();
        }
    });

    $('button#charge_modal_close_icon').on('click', function () {
        $('#action_charge_success').modal('hide');
        if ($('#success_flag').val() == 'true') {
            // 画面を更新
            location.reload();
        }
    });
}

/* Hide preview area show photo. */
if (Number($('#preview_count').val()) == 0) {
    $('#preview_carousel_panel').addClass('hide')
}

function OnLinkClick(uri, pid_value, accessrole) {
    let data = {
        uri: uri,
        pid_value: pid_value,
        accessrole: accessrole
    };
    $.ajax({
        url: '/get_uri',
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify(data),
        success: function(data) {
            console.log(data);
        },
        error: function(error) {
          console.log(error);
        }
      });
    window.open(uri);
}
function confirm_login(action){
    let future_date_message = $('#future_date_message').val();
    let displaytype = $('#displaytype').val();
    let download_preview_message = $('#download_preview_message').val();
    let download_message = $("#download_message").val();
    let preview_message = $("#preview_message").val();
    if(action === 'download'){
        message = download_message;
    }else{
        message = preview_message;
    }
    if(displaytype == 'preview' && download_preview_message){
        date_message = download_preview_message;
    }else{
        date_message = future_date_message;
    }
    if(!confirm(date_message + message)){
        window.location.href = window.location.pathname;
        return false;
    } else {
        return true;
    }
}