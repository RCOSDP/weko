(function(angular) {
    angular.element(document).ready(function() {
        angular.module('wekoRecordDetails.controllers', [
            'ngAnimate', 'ngSanitize', 'mgcrea.ngStrap', 'mgcrea.ngStrap.modal'
        ]);

        function ItemController($scope, $modal, $http, $window) {
            $scope.openConfirm = function(type, url, rdt, id) {
                var confirmModalScope = $scope.$new();
                confirmModalScope.modalInstance = $modal({
                    //templateUrl: "confirm-modal.html",
                    template: '<div class="modal" tabindex="-1" role="dialog"><div class="modal-dialog"><div class="modal-content"><div class="modal-header"><h3 class="modal-title"><span class="glyphicon glyphicon-info-sign"></span>{{ confirm_title }}</h3></div><div class="modal-body"><p>{{ check_msg }}</p></div><div class="modal-footer"><button class="btn btn-primary ok-button" ng-click="ok()">{{ ok_label }}</button><button class="btn btn-info cancel-button" ng-click="cancel()">{{ cancel_label }}</button></div></div></div></div>',
                    controller: 'ConfirmController',
                    scope: confirmModalScope,
                    show: false,
                    resolve: {
                        type: function() {
                            return type;
                        },
                        url: function() {
                            return url;
                        },
                        rdt: function() {
                            return rdt;
                        },
                        id: function() {
                            return id;
                        },
                        label_title: function() {
                            return {
                                confirm_title: document.getElementById('confirm_title').textContent,
                                del_ver_msg: document.getElementById('del_ver_msg').textContent,
                                del_msg: document.getElementById('del_msg').textContent,
                                ok_label: document.getElementById('ok_label').textContent,
                                cancel_label: document.getElementById('cancel_label').textContent 
                            }
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
        function ConfirmController($scope, $http, $window, type, url, rdt, id, label_title) {
            if (type === "del_ver") {
                $scope.check_msg = label_title.del_ver_msg;
            } else {
                $scope.check_msg = label_title.del_msg;
            }
            $scope.confirm_title = label_title.confirm_title;
            $scope.ok_label = label_title.ok_label;
            $scope.cancel_label = label_title.cancel_label;
            $scope.ok = function() {
                $('[role="alert"]').hide();
                $('[role="msg"]').css('display', 'inline-block');
                $('#btn_edit').attr("disabled", true);
                $('#btn_delete').attr("disabled", true);
                $('#btn_ver_delete').attr("disabled", true);
                $scope.modalInstance.hide();
                $('body').removeClass('modal-open');
                $http({
                    method: 'GET',
                    url: "/api/items/check_record_doi/" + id,
                }).then(function successCallback(response) {
                    if (0 == response.data.code) {
                        $('[role="msg"]').hide();
                        $('[role="alert"]').css('display', 'inline-block');
                        $('[role="alert"]').text($("#delete_message").val());
                        $('#btn_edit').removeAttr("disabled");
                        $('#btn_delete').removeAttr("disabled");
                        $('#btn_ver_delete').removeAttr("disabled");
                      } else {
                        $http.post(url, { pid_value: id }, {
                            headers: { 'Content-Type': 'application/json' }
                        }).then(
                            function(response) {
                                $('[role="msg"]').hide();
                                if (response.data.code === -1 && response.data.is_locked) {
                                    $('#btn_edit').removeAttr("disabled");
                                    $('#btn_delete').removeAttr("disabled");
                                    $('#btn_ver_delete').removeAttr("disabled");
                                    $('[role="alert"]').css('display', 'inline-block');
                                    if (response.data.msg) {
                                        $('[role="alert"]').text(response.data.msg);
                                    } else {
                                        $('[role="alert"]').text("INTERNAL SERVER ERROR");
                                    }
                                } else {
                                    // success callback
                                    $window.location.href = response.data?.data?.redirect || rdt;
                                }
                            },
                            function(response) {
                                $('[role="msg"]').hide();
                                $('#btn_edit').removeAttr("disabled");
                                $('#btn_delete').removeAttr("disabled");
                                $('#btn_ver_delete').removeAttr("disabled");
                                $('[role="alert"]').css('display', 'inline-block');
                                if (response.data.msg) {
                                    $('[role="alert"]').text(response.data.msg);
                                } else {
                                    $('[role="alert"]').text("INTERNAL SERVER ERROR");
                                }
                                // failure call back
                                console.log(response);
                            }
                        );
                      };
                }, function errorCallback(response) {
                    $('#btn_edit').removeAttr("disabled");
                    $('#btn_delete').removeAttr("disabled");
                    $('#btn_ver_delete').removeAttr("disabled");
                    $('[role="msg"]').hide();
                    $('[role="alert"]').text('Check DOI fail.');
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