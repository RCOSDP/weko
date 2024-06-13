(function (angular) {
    // Bootstrap it!
    angular.element(document).ready(function () {
        angular.module('searchDetail.controllers', []);
        function searchDetailCtrl($scope, $rootScope, $http, $location) {
            $scope.condition_data = [];
            $scope.detail_search_key = [];
            $scope.default_search_key = [];
            $scope.search_community = document.getElementById('community').value;
            $scope.search_type = "0";
            $scope.default_condition_data = [];

            $scope.load_delimiter = 50;

            // page init
            $scope.initData = function (data) {
                json_obj = angular.fromJson(data)
                db_data = json_obj.condition_setting;

                angular.forEach(db_data, function (item, index, array) {
                    // useable
                    if (item.useable_status) {
                        var obj_key = {
                            id: '',
                            contents: '',
                            inx: 0,
                            disabled_flg: false
                        };
                        obj_key.id = item.id;
                        obj_key.contents = item.contents;
                        obj_key.inx = index;
                        $scope.detail_search_key.push(obj_key);
                    };

                    // default display
                    if (item.default_display) {
                        var default_key = {
                            id: '',
                            contents: '',
                            inx: 0
                        };
                        default_key.id = item.id;
                        default_key.contents = item.contents;
                        default_key.inx = index;
                        $scope.default_search_key.push(default_key);
                    };
                });

                angular.forEach($scope.default_search_key, function (item, index, array) {
                    var obj_of_condition = {
                        selected_key: '',
                        key_options: [],
                        key_value: {}
                    };
                    obj_of_condition.selected_key = item.id;
                    obj_of_condition.key_options = $scope.detail_search_key;
                    obj_of_condition.key_value = angular.copy(db_data[item.inx]);
                    if (db_data[item.inx].inputType == 'checkbox_list'){
                        $scope.generate_check_box_list_check_val(item, db_data, obj_of_condition)
                    }
                    $scope.condition_data.push(obj_of_condition)
                });

                $scope.default_condition_data = angular.fromJson(angular.toJson($scope.condition_data));

                if (sessionStorage.getItem('btn') == 'detail-search') {
                    $scope.condition_data = angular.fromJson(sessionStorage.getItem('detail_search_conditions'));
                    sessionStorage.removeItem('btn');
                }
                else {
                    $scope.reset_data();
                    sessionStorage.setItem('detail_search_conditions', angular.toJson($scope.condition_data));
                }

                $scope.update_disabled_flg();
            };

            // add button
            $scope.add_search_key = function () {
                var obj_of_condition = {
                    selected_key: '',
                    key_options: [],
                    key_value: {}
                }
                var flg = 0

                for (var sub_detail in $scope.detail_search_key) {
                    flg = 0

                    for (var sub_condition in $scope.condition_data) {
                        if ($scope.detail_search_key[sub_detail].id == $scope.condition_data[sub_condition].selected_key) {
                            flg = 1
                            break;
                        }
                    }

                    if (flg == 0) {
                        obj_of_condition.selected_key = $scope.detail_search_key[sub_detail].id;
                        obj_of_condition.key_options = $scope.detail_search_key;
                        obj_of_condition.key_value = angular.copy(db_data[$scope.detail_search_key[sub_detail].inx]);
                        if (db_data[$scope.detail_search_key[sub_detail].inx].inputType == 'checkbox_list'){
                            $scope.generate_check_box_list_check_val($scope.detail_search_key[sub_detail],db_data,obj_of_condition)
                        }
                        $scope.condition_data.push(obj_of_condition)
                        break;
                    }
                }

                $scope.update_disabled_flg();
            };

            // delete button
            $scope.delete_search_key = function (index) {
                $scope.condition_data.splice(index, 1);
                $scope.update_disabled_flg();
            };
            // change_searc_key
            $scope.change_search_key = function (index, search_key) {
                var obj = $scope.get_search_key(search_key)
                $scope.condition_data.splice(index, 1, obj);
                $scope.update_disabled_flg();
            };

            // detail search
            $rootScope.getSettingDefault = function () {
                let data = null;

                $.ajax({
                    async: false,
                    method: 'GET',
                    url: '/get_search_setting',
                    headers: { 'Content-Type': 'application/json' },
                }).then(function successCallback(response) {

                    if (response.status === 1) {
                        data = response.data;
                    }

                }, function errorCallback(error) {
                    console.log(error);
                    return null;
                });

                if (data.dlt_keyword_sort_selected !== null
                    && data.dlt_keyword_sort_selected !== undefined) {
                    let key_sort = data.dlt_keyword_sort_selected;
                    let descOrEsc = "";

                    if (key_sort.includes("_asc")) {
                        key_sort = key_sort.replace("_asc", "");
                    }

                    if (key_sort.includes("_desc")) {
                        descOrEsc = "-";
                        key_sort = descOrEsc + key_sort.replace("_desc", "");
                    }

                    return {
                        key: "sort",
                        value: key_sort
                    };
                }
            }

            $scope.detail_search = function () {
                let query_str = "";
                let data = $rootScope.getSettingDefault();

                // Add simple search query to detail search one
                $scope.search_q = document.getElementById('q').value;

                query_str = query_str + "&search_type=" + $scope.search_type + "&q=" + $scope.search_q;

                if ($scope.search_community != "") {
                    query_str = query_str + "&community=" + $scope.search_community;
                }

                angular.forEach($scope.condition_data, function (item, index, array) {
                    if (item.key_value.inputType == "text") {
                        query_str = query_str + "&" + item.key_value.id + "=" + item.key_value.inputVal;
                    }
                    if (item.key_value.inputType == "range") {
                        var inputValFrom = item.key_value.inputVal_from;
                        var inputValTo = item.key_value.inputVal_to;
                        query_str = query_str + "&" + item.key_value.id + "_from=" + inputValFrom + "&" +
                                    item.key_value.id + "_to=" + inputValTo;
                    }
                    if (item.key_value.inputType == "geo_distance") {
                        var inputValLat = item.key_value.inputVal_lat;
                        var inputValLon = item.key_value.inputVal_lon;
                        var inputValDistance = item.key_value.inputVal_distance;
                        query_str = query_str + "&" + item.key_value.id + "_lat=" + inputValLat + "&" +
                                    item.key_value.id + "_lon=" + inputValLon +  "&" +
                                    item.key_value.id + "_distance=" + inputValDistance;
                    }

                    if (item.key_value.inputType == "dateRange") {
                        var pattern_date = /^(?:[0-9]{4}|[0-9]{4}(0[1-9]|1[0-2])|[0-9]{4}(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1]))$/
                        var inputValFrom = item.key_value.inputVal_from;
                        var inputValTo = item.key_value.inputVal_to;
                        
                        if (pattern_date.test(inputValFrom)){
                            switch (inputValFrom.length) {
                                // YYYY
                                case 4:
                                    inputValFrom = inputValFrom + '01' + '01';
                                    break;
                                // YYYYMM
                                case 6:
                                    inputValFrom = inputValFrom + '01';
                                    break;
                                // YYYYMMDD
                                case 8:
                                    var y = inputValFrom.substring(0, 4);
                                    var m = inputValFrom.substring(4, 6);
                                    var d = inputValFrom.substring(6, 8);
                                    var date = new Date(y + '-' + m + '-' + d);

                                    // Fix invalid date to the first day of the month
                                    if (!(date instanceof Date) || isNaN(date) || date.getDate() != Number(d)) {
                                        var inputValFrom = y + m + '01';
                                    }

                                    break;
                                default:
                                    inputValFrom = '';
                            }
                        }else{
                            inputValFrom = '';
                        }

                        if (pattern_date.test(inputValTo)){
                            switch (inputValTo.length) {
                                // YYYY
                                case 4:
                                    inputValTo = inputValTo + '12' + '31';
                                    break;
                                // YYYYMM
                                case 6:
                                    var y = inputValTo.substring(0, 4);
                                    var m = inputValTo.substring(4, 6);
                                    var d =new Date(Number(y), Number(m), 0).getDate();
                                    inputValTo = inputValTo + String(d).padStart(2, '0');
                                    break;
                                //YYYYMMDD
                                case 8:
                                    var y = inputValTo.substring(0, 4);
                                    var m = inputValTo.substring(4, 6);
                                    var d = inputValTo.substring(6, 8);
                                    var date = new Date(y + '-' + m + '-' + d);
                                    if (date instanceof Date && !isNaN(date) && date.getDate()==Number(d)) {
                                        inputVal = String(date.getFullYear()).padStart(4, '0');
                                                   + String(date.getMonth() + 1).padStart(2, '0');
                                                   + String(date.getDate()).padStart(2, '0');

                                    // Fix invalid date to the last day of the month
                                    } else {
                                        var validDay = new Date(Number(y), Number(m), 0).getDate();
                                        inputValTo = y + m + String(validDay).padStart(2, '0');
                                    }

                                    break;
                                default:
                                    inputValTo = '';
                            }
                        }else{
                            inputValTo = '';
                        }

                        query_str = query_str + "&" + item.key_value.id + "_from=" + inputValFrom + "&" +
                                    item.key_value.id + "_to=" + inputValTo;
                    }

                    if (item.key_value.inputType == "checkbox_list") {
                        let key_arr = "";
                        let firstItem = true;
                        angular.forEach(item.key_value.check_val, function (item, index, array) {
                            if (item.checkStus) {
                                let currentKey = firstItem ? item.id : "," + item.id;
                                key_arr = key_arr + currentKey;
                                firstItem = false
                            }
                        });
                        query_str = query_str + "&" + item.key_value.id + "=" + key_arr;
                    }

                    if (item.key_value.inputType == "selectbox") {
                        query_str = query_str + "&" + item.key_value.id + "=" + item.key_value.inputVal;
                    }

                    if (item.key_value.inputType == "radio_list") {
                        query_str = query_str + "&" + item.key_value.id + "=" + item.key_value.inputVal;
                    }

                    if (item.key_value.mappingFlg) {
                        var schema_or_arr = "";
                        let firstItem = true;
                        angular.forEach(item.key_value.sche_or_attr, function (item, index, array) {
                            if (item.checkStus) {
                                let currentKey = firstItem ? item.id : "," + item.id;
                                schema_or_arr = schema_or_arr + currentKey;
                                firstItem = false;
                            }
                        });
                        query_str = query_str + "&" + item.key_value.mappingName + "=" + schema_or_arr;
                    }
                });

                sessionStorage.setItem('detail_search_conditions', angular.toJson($scope.condition_data));
                if (data !== null && data.key !== null && data.value !== null) {
                    query_str += "&" + data.key + "=" + data.value;
                }

                let url = '/search?page=1' + query_str;

                if (angular.element('#item_management_bulk_update').length != 0) {
                    url = '/admin/items' + url + '&item_management=update';
                } else if (angular.element('#item_management_bulk_delete').length != 0) {
                    url = '/admin/items' + url + '&item_management=delete';
                } else {
                    url += getFacetParameter();
                }

                // URI-encode '+' in advance for preventing from being converted to '%20'(space)
                url = url.replace(/\+/g, encodeURIComponent('+'))
                window.location.href = url
            }

            $scope.detail_search_clear = function () {
                $scope.reset_data();
                sessionStorage.setItem('detail_search_conditions', angular.toJson($scope.condition_data));
            }

            // set search options
            $scope.update_disabled_flg = function () {
                var update_flg = 0;

                for (var sub_default_key in $scope.detail_search_key) {
                    update_flg = 0;

                    for (var sub_condition in $scope.condition_data) {
                        if ($scope.detail_search_key[sub_default_key].id == $scope.condition_data[sub_condition].selected_key) {
                            update_flg = 1;
                            break;
                        }
                    }

                    if (update_flg == 1) {
                        $scope.detail_search_key[sub_default_key].disabled_flg = true;
                    } else {
                        $scope.detail_search_key[sub_default_key].disabled_flg = false;
                    }
                }

            }

            //restart
            $scope.reset_data = function () {
                $scope.condition_data = [];

                for (var sub_default_key in $scope.detail_search_key) {
                    $scope.detail_search_key[sub_default_key].disabled_flg = false;
                }

                angular.forEach($scope.default_search_key, function (item, index, array) {
                    var obj_of_condition = {
                        selected_key: '',
                        key_options: [],
                        key_value: {}
                    };
                    obj_of_condition.selected_key = item.id;
                    obj_of_condition.key_options = $scope.detail_search_key;
                    obj_of_condition.key_value = angular.copy(db_data[item.inx]);
                    if (db_data[item.inx].inputType == 'checkbox_list'){
                        $scope.generate_check_box_list_check_val(item, db_data, obj_of_condition)
                    }
                    $scope.condition_data.push(obj_of_condition);
                });

                $scope.update_disabled_flg();
            }
            $scope.loadMore = function(index){
                var now = $scope.condition_data[index].key_value.limit;
                var next = 0;
                if($scope.condition_data[index].key_value.check_val.length < now+$scope.load_delimiter){
                    next = $scope.condition_data[index].key_value.check_val.length;
                }else{
                    next = now + $scope.load_delimiter;
                }
                $scope.unescape_check_val($scope.condition_data[index].key_value.check_val,next,now)
                $scope.condition_data[index].key_value.limit = next;
            }
            $scope.generate_check_box_list_check_val = function (target, db_data, obj_of_condition) {
                if (db_data[target.inx].check_val.length>$scope.load_delimiter){
                    obj_of_condition.key_value.limit=$scope.load_delimiter;
                }else{
                    obj_of_condition.key_value.limit=db_data[target.inx].check_val.length;
                }
                $scope.unescape_check_val(obj_of_condition.key_value.check_val,obj_of_condition.key_value.limit)
            }

            $scope.unescape_check_val = function(check_val, to, from=0){
                for (var i=from; i<to; i++){
                    item = check_val[i]
                    if(typeof item.contents === "string"){
                        ele = document.createElement("div")
                        ele.innerHTML = item.contents
                        item.contents = ele.textContent
                    }
                    if(typeof item.id === "string"){
                        ele = document.createElement("div")
                        ele.innerHTML = item.id
                        item.id = ele.textContent
                    }
                }
            }
            // set search options
            $scope.get_search_key = function (search_key) {
                var obj_of_condition = {
                    selected_key: '',
                    key_options: [],
                    key_value: {}
                };

                for (var sub_default_key in $scope.detail_search_key) {

                    if ($scope.detail_search_key[sub_default_key].id == search_key) {
                        obj_of_condition.selected_key = search_key;
                        obj_of_condition.key_options = $scope.detail_search_key;
                        obj_of_condition.key_value = angular.copy(db_data[$scope.detail_search_key[sub_default_key].inx]);
                        if (db_data[$scope.detail_search_key[sub_default_key].inx].inputType == 'checkbox_list'){
                            $scope.generate_check_box_list_check_val($scope.detail_search_key[sub_default_key],db_data, obj_of_condition)
                        }
                        break;
                    }
                }

                return obj_of_condition;
            }

            $scope.daysInMonth = function (month, year){
                switch(month){
                    case 1:
                        return (year % 4 == 0 && year % 100) || year % 400 == 0 ? 29 : 28;
                    case 8: case 3: case 5: case 10:
                        return 30
                    default:
                        return 31
                }
            }
        
            $scope.validDate = function(elem){
                const date_pattern = /([0-9]{4})(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])/
                if (elem.validity.patternMismatch){
                    return true;
                }else{
                    const dates = elem.value.match(date_pattern)
                    if (dates){
                        const year = parseInt(dates[1])
                        const month = parseInt(dates[2],10) - 1
                        const day = parseInt(dates[3])
                        return day > $scope.daysInMonth(month, year);
                    }else{
                        return false
                    }
                }
            }
            $scope.validateDate = function (event) {
                let target = event.target
                var elem = document.getElementById(target.id);
                // 13はエンターキー
                if (event.which === 13) {
                    // サブミット時に無効な値が入力されていたら値をクリアする
                    if ($scope.validDate(elem)){
                        elem.value = '';
                    } else {
                        $('#' + target.id).removeClass('invalid-date');
                        var invalidDateNoticeEl = $(target).parent().next();
                        invalidDateNoticeEl.addClass('hidden-invalid-date-notice');
                    }
                } else {
                if ($scope.validDate(elem)){
                    $('#' + target.id).addClass('invalid-date');
                    var invalidDateNoticeEl = $(target).parent().next();
                    invalidDateNoticeEl.removeClass('hidden-invalid-date-notice');
                } else {
                    $('#' + target.id).removeClass('invalid-date');
                    var invalidDateNoticeEl = $(target).parent().next();
                    invalidDateNoticeEl.addClass('hidden-invalid-date-notice');
                }
            }
            }

            // $scope.inputDataOnEnter = function () {
            //     var daterangeItems = $scope.condition_data.filter(function (item) {
            //         return item.key_value.inputType == "dateRange";
            //     })

            //     angular.forEach(daterangeItems, function(item) {
            //         var elem = angular.element(document.getElementsById(item.key_value.id + '_from'));
            //         var inputVal = elem.val();
            //     })
            // }

        }

        // Inject depedencies
        searchDetailCtrl.$inject = [
            '$scope',
            '$rootScope',
            '$http',
            '$location'
        ];
        angular.module('searchDetail.controllers').controller('searchDetailCtrl', searchDetailCtrl);
        angular.module('searchDetailModule', ['searchDetail.controllers']);
        angular.module('searchDetailModule', ['searchDetail.controllers']).config(
            [
                '$interpolateProvider','$locationProvider', function ($interpolateProvider,$locationProvider) {
                $interpolateProvider.startSymbol('[[');
                $interpolateProvider.endSymbol(']]');
                $locationProvider.html5Mode({
                    enabled: true,
                    requireBase: false,
                    rewriteLinks: false,
                  });
            }]
        ).directive('whenScrolled',function(){
            return function(scope, elem, attr){
                var raw = elem[0];
                elem.bind('scroll',  function() {
                  if (raw.scrollTop + raw.offsetHeight + 1 >= raw.scrollHeight) {
                    scope.$apply(attr.whenScrolled);
                  }
                });
            }
        });
        angular.bootstrap(
            document.getElementById('search_detail'), ['searchDetailModule']);
        
        /**
         * Returns faceted search parameters.
         * This function was created for the purpose of providing faceted search parameters for detailed search.
         * Returns parameters for faceted searches from existing URLs, excluding simple, advanced, and INDEX searches.
         * 
         * @returns Faceted search parameters.
         */
        function getFacetParameter() {
            let result = "";
            let params = window.location.search.substring(1).split('&');
            const conds = ['page', 'size', 'sort', 'timestamp', 'search_type', 'q', 'title', 'creator', 'date_range1_from', 'date_range1_to','time'];
            for (let i = 0; i < params.length; i++) {
                var keyValue = decodeURIComponent(params[i]).split('=');
                var key = keyValue[0];
                var value = keyValue[1];
                if(key && !conds.includes(key) && !key.startsWith("text")) {
                    result += "&" + encodeURIComponent(key) + "=" + encodeURIComponent(value);
                }
            }
            return result;
        }
    });
})(angular);
