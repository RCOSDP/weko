(function (angular) {
    // Bootstrap it!
    angular.element(document).ready(function () {
        angular.module('searchDetail.controllers', []);

        function searchDetailCtrl($scope, $rootScope, $http, $location) {
            $scope.condition_data = [];
            $scope.detail_search_key = [];
            $scope.default_search_key = [];
            $scope.search_q = "";
            $scope.search_community = document.getElementById('community').value;
            $scope.search_type = "0";
            $scope.default_condition_data = []

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
                    }
                    obj_of_condition.selected_key = item.id;
                    obj_of_condition.key_options = $scope.detail_search_key;
                    obj_of_condition.key_value = angular.copy(db_data[item.inx]);
                    $scope.condition_data.push(obj_of_condition)
                });
                $scope.default_condition_data = angular.fromJson(angular.toJson($scope.condition_data));
                if (sessionStorage.getItem('btn') == 'detail-search') {
                    $scope.condition_data = angular.fromJson(sessionStorage.getItem('detail_search_conditions'));
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
                for (var sub_detail of $scope.detail_search_key) {
                    flg = 0
                    for (var sub_condition of $scope.condition_data) {
                        if (sub_detail.id == sub_condition.selected_key) {
                            flg = 1
                            break;
                        }
                    }
                    if (flg == 0) {
                        obj_of_condition.selected_key = sub_detail.id;
                        obj_of_condition.key_options = $scope.detail_search_key;
                        obj_of_condition.key_value = angular.copy(db_data[sub_detail.inx]);
                        $scope.condition_data.push(obj_of_condition)
                        break;
                    }
                }
                $scope.update_disabled_flg();
            }
            // delete button
            $scope.delete_search_key = function (index) {
                $scope.condition_data.splice(index, 1);
                $scope.update_disabled_flg();
            }
            // change_searc_key
            $scope.change_search_key = function (index, search_key) {
                var obj = $scope.get_search_key(search_key)
                $scope.condition_data.splice(index, 1, obj);
                $scope.update_disabled_flg();
            }
            // detail search
            $scope.detail_search = function () {
                var query_str = "";
                query_str = query_str + "&search_type=" + $scope.search_type + "&q=" + $scope.search_q;
                if ($scope.search_community != "") {
                    query_str = query_str + "&community=" + $scope.search_community;
                }
                angular.forEach($scope.condition_data, function (item, index, array) {
                    //
                    if (item.key_value.inputType == "text") {
                        query_str = query_str + "&" + item.key_value.id + "=" + item.key_value.inputVal
                    }
                    if (item.key_value.inputType == "dateRange") {
                        query_str = query_str + "&" + item.key_value.id + "_from=" + item.key_value.inputVal_from + "&" +
                            item.key_value.id + "_to=" + item.key_value.inputVal_to;
                    }
                    if (item.key_value.inputType == "checkbox_list") {
                        var key_arr = ""
                        angular.forEach(item.key_value.check_val, function (item, index, array) {
                            if (item.checkStus) {
                                key_arr = key_arr + item.id + ",";
                            }
                        });
                        query_str = query_str + "&" + item.key_value.id + "=" + key_arr;
                    }
                    if (item.key_value.inputType == "selectbox") {
                        query_str = query_str + "&" + item.key_value.id + "=" + item.key_value.inputVal
                    }
                    if (item.key_value.inputType == "radio_list") {
                        query_str = query_str + "&" + item.key_value.id + "=" + item.key_value.inputVal
                    }
                    if (item.key_value.mappingFlg) {
                        var schema_or_arr = "";
                        angular.forEach(item.key_value.sche_or_attr, function (item, index, array) {
                            if (item.checkStus) {
                                schema_or_arr = schema_or_arr + item.id + ",";
                            }
                        });
                        query_str = query_str + "&" + item.key_value.mappingName + "=" + schema_or_arr;
                    }
                });
                sessionStorage.setItem('detail_search_conditions', angular.toJson($scope.condition_data));
                var url = '/search?page=1' + query_str
                if(angular.element('#item_management_bulk_update').length != 0) {
                  url = url + '&item_management=update';
                }

                window.location.href = url
            }
            //
            $scope.detail_search_clear = function () {
                $scope.reset_data();
                sessionStorage.setItem('detail_search_conditions', angular.toJson($scope.condition_data));
            }
            // set search options
            $scope.update_disabled_flg = function () {
                var update_flg = 0;
                for (var sub_default_key of $scope.detail_search_key) {
                    update_flg = 0;
                    for (var sub_condition of $scope.condition_data) {
                        if (sub_default_key.id == sub_condition.selected_key) {
                            update_flg = 1;
                            break;
                        }
                    }
                    if (update_flg == 1) {
                        sub_default_key.disabled_flg = true;
                    } else {
                        sub_default_key.disabled_flg = false;
                    }
                }

            }
            //restart
            $scope.reset_data = function () {
                $scope.condition_data = [];
                for (var sub_default_key of $scope.detail_search_key) {
                    sub_default_key.disabled_flg = false;
                }
                angular.forEach($scope.default_search_key, function (item, index, array) {
                    var obj_of_condition = {
                        selected_key: '',
                        key_options: [],
                        key_value: {}
                    }
                    obj_of_condition.selected_key = item.id;
                    obj_of_condition.key_options = $scope.detail_search_key;
                    obj_of_condition.key_value = angular.copy(db_data[item.inx]);
                    $scope.condition_data.push(obj_of_condition)
                });
                $scope.update_disabled_flg();
            }

            // set search options
            $scope.get_search_key = function (search_key) {
                var obj_of_condition = {
                    selected_key: '',
                    key_options: [],
                    key_value: {}
                }
                for (var sub_default_key of $scope.detail_search_key) {
                    if (sub_default_key.id == search_key) {
                        obj_of_condition.selected_key = search_key;
                        obj_of_condition.key_options = $scope.detail_search_key;
                        obj_of_condition.key_value = angular.copy(db_data[sub_default_key.inx]);
                        break;
                    }
                }
                return obj_of_condition;
            }
        }
        // Inject depedencies
        searchDetailCtrl.$inject = [
          '$scope',
          '$rootScope',
          '$http',
          '$location'
        ];
        angular.module('searchDetail.controllers')
            .controller('searchDetailCtrl', searchDetailCtrl);

        angular.module('searchDetailModule', ['searchDetail.controllers']);

        angular.module('searchDetailModule', ['searchDetail.controllers']).config(['$interpolateProvider', function (
                $interpolateProvider) {
                $interpolateProvider.startSymbol('[[');
                $interpolateProvider.endSymbol(']]');　　
            }]);

        angular.bootstrap(
            document.getElementById('search_detail'), ['searchDetailModule']);
    });
})(angular);
























