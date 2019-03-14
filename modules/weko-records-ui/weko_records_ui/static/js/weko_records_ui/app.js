angular.module('myApp', ['ui.bootstrap'])
 .controller("ItemController",
  function($scope, $modal, $http, $window) {
   $scope.openConfirm = function(message, url, rdt) {
    var modalInstance = $modal.open({
     templateUrl: "confirm-modal.html",
     controller: "ConfirmController",
     resolve: {
      msg: function() {
       return message;
      }
     }
    });
    modalInstance.result.then(function() {
     $http.delete(url).then(
      function(response) {
       // success callback
       $window.location.href = rdt;
      },
      function(response) {
       // failure call back
       console.log(response);
      }
     );
    });
   };

    $scope.showChangeLog = function(deposit) {
        // call api for itself to catch field deposit
        // Call service to catch version by deposit with api /api/files/
        $('#bodyModal').children().remove();
        $http({
            method: 'GET',
            url: `/api/files/${deposit}?versions`,
        }).then(function successCallback(response) {
            $('#bodyModal').append(createRow(response['data']));
            $('#basicExampleModal').modal({
                show: true
            });
        }, function errorCallback(response) {
            console.log('Error when trigger api /api/files');
        });
    }

    function createRow(response) {
        let results = '';
        const contents = response.contents;
        response.contents.sort(function(first, second) {
            return second.updated - first.updated;
        });
        let txt_published = $('#txt_published').val()
        let txt_private = $('#txt_private').val()
        let txt_username = $('#txt_username').val()
        let txt_displayname = $('#txt_displayname').val()
        let txt_email = $('#txt_email').val()
        let is_logged_in = $('#txt_is_logged_in').val()
        for (let index = 0; index < contents.length; index++) {
            const ele = contents[index];

            // const isPublished = ele.pubPri === 'Published' ? 1 : 0;
            const nameRadio = `radio${index}`;
            let radio = index == 0 ? "" : `
            <div class="radio">
                <label style="margin-left: 5px"><input type="radio" name="${nameRadio}">${txt_published}</label>
                <label style="margin-left: 5px"><input type="radio" name="${nameRadio}" checked>${txt_private}</label>
            </div>
            `;
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

            // TODO: Check the permission of file to be able download or not
            let txt_link = index == 0 ? `<a href="${ele.links.self}">${ele.key}</a>` : ele.key

            let size = formatBytes(ele.size, 2);

            // Checksum
            var checksum = ele.checksum
            var checksumIndex = ele.checksum.indexOf(":")
            if (checksumIndex != -1) {
              checksum = ele.checksum.substr(0, checksumIndex) + " <span class=\"wrap\">" + ele.checksum.substr(checksumIndex + 1) + "</span>"
            }

            var username = txt_username == '' ? txt_email : txt_username
            if (!is_logged_in) {
              username = ""
            }

            results += `
            <tr>
                <td>
                    ${version}
                </td>
                <td class="nowrap">
                    ${formatDate(new Date(ele.updated))}
                </td>
                <td>
                    ${txt_link}
                </td>
                <td>
                    ${size}
                </td>
                <td class="wrap">
                    ${checksum}
                </td>
                <td class="nowrap">
                  ${username}
                </td>
                <td>${radio}</td>
            </tr>
            `;

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

        return `${[year, month, day].join('-')}\t${[hour, minute, second].join(':')}`;
    }

    function formatBytes(a,b) {
        if (0 == a) return "0 Bytes";
        var c = 1024, d=b||2, e = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"], f = Math.floor(Math.log(a)/Math.log(c));
        return parseFloat((a/Math.pow(c,f)).toFixed(d)) + " (" + e[f] + ")";
    }
  }
 ).controller('ConfirmController',
  function($scope, $modalInstance, msg) {
   $scope.message = msg;

   $scope.ok = function() {
    $modalInstance.close();
   };
   $scope.cancel = function() {
    $modalInstance.dismiss();
   };
  });
