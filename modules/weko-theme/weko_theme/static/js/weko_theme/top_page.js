require([
    "jquery",
    "bootstrap"
], function () {
    $('#body').on('load', function (event, data) {
    });

    // urlからパラメタ―の値を取得
    function GetUrlParam(sParam) {
        var sURL = window.location.search.substring(1);
        var sURLVars = sURL.split('&');
        for (var i = 0; i < sURLVars.length; i++) {
            var sParamArr = sURLVars[i].split('=');
            if (sParamArr[0] == sParam) {
                return decodeURIComponent(sParamArr[1]);
            }
        }
        return false;
    }

    // urlからパラメタ―のキーを取得する
    function IsParamKey(sParam) {
        var sURL = window.location.search.substring(1);
        var sURLVars = sURL.split('&');
        for (var i = 0; i < sURLVars.length; i++) {
            var sParamArr = sURLVars[i].split('=');
            if (sParamArr[0] == sParam) {
                return true;
            }
            if (sParam) { }
        }
        return false;
    }

    // サーチ入力の表示
    function ArrangeSearch() {
        var btn = sessionStorage.getItem('btn');
        var SearchType = GetUrlParam('search_type');
        var input = '';
        var IsRec = window.location.pathname.indexOf('records') > -1;

        $('#search_detail_metadata :input:not(:checkbox), #q, #search_type :input').each(function () {
            if (IsRec) {
                input = sessionStorage.getItem($(this).attr('id'));
            } else {
                if (SearchType && SearchType != '2') {
                    if (IsParamKey($(this).attr('id'))) {
                        input = GetUrlParam($(this).attr('id'));
                    }
                } else {
                    sessionStorage.removeItem($(this).attr('id'));
                }
            }

            // 詳細展開 値入力残
            if (btn) {
                if (btn == 'detail-search') {
                    if (IsParamKey($(this).attr('id')) || IsRec) {

                        if (input && input !== '') {
                            //type is text
                            $(this).val(input);
                            if (!$('#search_detail').hasClass('expanded')) {
                                $('#top-search-btn').addClass('hidden');
                                $('#search_simple').removeClass('input-group');
                                $('#search_detail_metadata').collapse('show');
                            } else {
                                $('#search_detail_metadata').collapse('hide');
                            }
                        }
                    }
                } else if (btn == 'simple-search' && sessionStorage.getItem('q', false)) {
                    $('#search_detail_metadata').collapse('hide');
                }
            } else {
                $('#search_type_fulltext').prop('checked', true);
            }
        });

        // type is checkbox radio
        $('#search_detail_metadata :input:not(:text)').each(function () {
            if (IsRec) {
                input = sessionStorage.getItem($(this).attr('id'));
            } else {
                if (SearchType && SearchType != '2') {
                    input = sessionStorage.getItem($(this).attr('id'));
                } else {
                    sessionStorage.removeItem($(this).attr('id'));
                }
            }

            // 詳細展開 値入力残
            if (btn) {
                if (btn == 'detail-search') {
                    if (true || IsRec) {
                        if (input && input !== '') {
                            //type is checkbox
                            $(this).attr('checked', true);
                            if (!$('#search_detail').hasClass('expanded')) {
                                $('#top-search-btn').addClass('hidden');
                                $('#search_simple').removeClass('input-group');
                                $('#search_detail_metadata').collapse('show');
                            } else {
                                $('#search_detail_metadata').collapse('hide');
                            }
                        }
                    }
                } else if (btn == 'simple-search' && sessionStorage.getItem('q', false)) {
                    $('#search_detail_metadata').collapse('hide');
                }
            } else {
                $('#search_type_fulltext').prop('checked', true);
            }
        });

        // サーチラジオボタンの位置
        if (SearchType) {
            if (SearchType == '0' || SearchType == '2') {
                $('#search_type_fulltext').prop('checked', true);
            } else {
                $('#search_type_keyword').prop('checked', true);
            }
        } else {
            if (IsRec) {
                var search_type = sessionStorage.getItem('search_type', false)
                if (search_type && search_type == '1') {
                    $('#search_type_keyword').prop('checked', true);
                } else {
                    $('#search_type_fulltext').prop('checked', true);
                }
            } else {
                $('#search_type_fulltext').prop('checked', true);
                sessionStorage.removeItem('search_type');
            }
        }
    }

    // Url query コントロール
    function SearchSubmit() {
        if ($('#search_type_fulltext').prop('checked')) {
            sessionStorage.setItem('search_type', '0');
        } else {
            sessionStorage.setItem('search_type', '1');
        }

        $('#search-form').submit(function (event) {
            var search = '';
            search = insertParam(search, "page", 1);
            $('#search_type :input:checked').each(function () {
                var list_params = $(this).serializeArray();
                list_params.map(function (item) {
                    search = insertParam(search, item.name, item.value);
                })
            });
            $('#q').serializeArray().map(function (item) {
                search = insertParam(search, item.name, item.value);
            })

            if ($('#community').val() && $('#q').val.trim().length > 0) {
                $('#community').serializeArray().map(function (item) {
                    search = insertParam(search, item.name, item.value);
                })
            }

            let data = getDefaultSetting();
            let key_sort = data.dlt_keyword_sort_selected;
            let size = data.dlt_dis_num_selected;

            if (key_sort.indexOf("_asc") !== -1) {
                key_sort = key_sort.replace("_asc", "");
            }

            if (key_sort.indexOf("_desc") !== -1) {
                key_sort = key_sort.replace("_desc", "");
                key_sort = "-" + key_sort;
            }

            if (!search.includes("sort")) {
                search = insertParam(search, "sort", key_sort);
            }

            if (size !== null && size !== undefined) {
                search = insertParam(search, "size", size);
            }

            if ($("#item_management_bulk_update").length != 0) {
                search = insertParam(search, "item_management", "update");
                window.location.href = "/admin/items/search" + search;
            } else if ($("#item_management_bulk_delete").length != 0) {
                search = insertParam(search, "item_management", "delete");
                window.location.href = "/admin/items/search" + search;
            } else {
                window.location.href = "/search" + search + getFacetParameter();
            }

            // stop the form from submitting the normal way and refreshing the page
            event.preventDefault();
        })
    }

    /**
     * Returns faceted search parameters.
     * This function was created for the purpose of giving faceted search parameters to simple searches.
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

    function insertParam(search, key, value) {
        key = encodeURIComponent(key); value = encodeURIComponent(value);
        var s = search;
        var kvp = key + "=" + value;
        var r = new RegExp("(&|\\?)" + key + "=[^\&]*");
        s = s.replace(r, "$1" + kvp);
        if (!RegExp.$1) { s += (s.length > 0 ? '&' : '?') + kvp; };

        //again, do what you will here
        return s
    }

    function getDefaultSetting() {
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
        });

        return data;
    }

    function daysInMonth(month, year){
        switch(month){
            case 1:
                return (year % 4 == 0 && year % 100) || year % 400 == 0 ? 29 : 28;
            case 8: case 3: case 5: case 10:
                return 30
            default:
                return 31
        }
    }

    function validDate(elem){
        const date_pattern = /([0-9]{4})(0[1-9]|1[0-2])(0[1-9]|[1-2][0-9]|3[0-1])/
        if (elem.validity.patternMismatch){
            return true;
        }else{
            const dates = elem.value.match(date_pattern)
            if (dates){
                const year = parseInt(dates[1])
                const month = parseInt(dates[2],10) - 1
                const day = parseInt(dates[3])
                return day > daysInMonth(month, year);
            }else{
                return false
            }
        }
    }


    $(document).ready(function () {

        ArrangeSearch();

        // 詳細検索からページ遷移した場合、詳細検索のアコーディオンを開いた状態にして、ボタンのテキストを「閉じる」にセット
        var urlParams = new URLSearchParams(window.location.search);
        var isDetailSearch = Array.from(urlParams.keys()).length > 6  // 6は簡易検索の際のクエリの数
        var SearchType = GetUrlParam('search_type');

        if (isDetailSearch && SearchType && SearchType != '2' && !urlParams.has('is_facet_search')) {  // インデックスの検索に開かない
            $('#search_detail_metadata').collapse('show');
            $('.detail-search-open').hide();
            $('.detail-search-close').show();
            $('#search_detail').addClass('expanded');
        }

        // 簡易検索ボタン
        $('#top-search-btn').on('click', function () {
            sessionStorage.removeItem('detail_search_conditions');
            sessionStorage.setItem('btn', 'simple-search');
            SearchSubmit();
        });

        $('#search_type_fulltext, #search_type_keyword').on('click', function () {
            let data = getDefaultSetting();
            let key_sort = data.dlt_keyword_sort_selected;

            if (key_sort.indexOf("_asc") !== -1) {
                key_sort = key_sort.replace("_asc", "");
                document.getElementById('sortType').value = "asc";
            }

            if (key_sort.indexOf("_desc") !== -1) {
                key_sort = key_sort.replace("_desc", "");
                document.getElementById('sortType').value = "desc";
            }

            document.getElementById('selectedDisplay').value = key_sort;
            document.getElementById('page_count').value = data.dlt_dis_num_selected;
        });

        // 詳細検索の表示と隠すボタン
        $('#detail_search_main').on('click', function () {
            var isExpanded = $('#search_detail').hasClass('expanded');

            if (isExpanded) {
                $('#search_detail_metadata').collapse('hide');
                $('.detail-search-close').hide();
                $('.detail-search-open').show();
                $('#search_detail').removeClass('expanded');
            } else {
                $('#search_detail_metadata').collapse('show');
                $('.detail-search-open').hide();
                $('.detail-search-close').show();
                $('#search_detail').addClass('expanded');
            }
        });

        // bootstrap-datepickerでテキスト入力を可能にする
        $('.detail-search-date').keyup(function (event) {
            if ($('body > :last').hasClass('datepicker')
                // 13と27はそれぞれエンターキーとエスケープキーを表す
                && event.which !== 13
                && event.which !== 27) {
                var input = $(this).val()
                var kbEvent = new KeyboardEvent('keydown', {keyCode: 27});
                this.dispatchEvent(kbEvent);
                $(this).val(input);
            }
        });

        // 日付入力フォームのバリデーション
        $('.detail-search-date').keyup(function (event) {
            var elem = document.getElementById(this.id);
            // 13はエンターキー
            if (event.which === 13) {
                // サブミット時に無効な値が入力されていたら値をクリアする
                if (validDate(elem)){
                    elem.value = '';
                } else {
                    $('#' + this.id).removeClass('invalid-date');
                    var invalidDateNoticeEl = $(this).parent().next();
                    invalidDateNoticeEl.addClass('hidden-invalid-date-notice');
                }
            } else {
                if (validDate(elem)){
                    $('#' + this.id).addClass('invalid-date');
                    var invalidDateNoticeEl = $(this).parent().next();
                    invalidDateNoticeEl.removeClass('hidden-invalid-date-notice');
                } else {
                    $('#' + this.id).removeClass('invalid-date');
                    var invalidDateNoticeEl = $(this).parent().next();
                    invalidDateNoticeEl.addClass('hidden-invalid-date-notice');
                }
            }
        });

        // 詳細検索ボタン：入力値をseesionStorageに保存する
        $('#detail-search-btn').on('click', function () {
            sessionStorage.setItem('btn', 'detail-search');
            SearchSubmit();
        });

        // 詳細検索ボタン：フォームのテキスト入力でエンターキーを押したら検索する
        $('.detail-search-text').keypress(function (event) {
            // 13はエンターキー
            if (event.which == 13) {
              $('#detail-search-btn').click();
            }
        });

        // アイテム検索結果 (search_ui/static/templates/itemlist.html)
        $('#q').on('change', function () {
            $('#search_detail_metadata :input:not(:checkbox), #q').each(function () {

                if ($(this).val() !== '') {
                    sessionStorage.setItem($(this).attr('id'), $(this).val());
                } else {
                    sessionStorage.removeItem($(this).attr('id'));
                }
            });
        });

        // // アイテム検索結果 (search_ui/static/templates/itemlist.html)
        // $('#search_detail_metadata :input:not(:text)').on('click', function () {
        //   $('#search_detail_metadata :input:not(:text)').each(function () {
        //     if ($(this).is(":checked")) {
        //       sessionStorage.setItem($(this).attr('id'), $(this).val());
        //     } else {
        //       sessionStorage.removeItem($(this).attr('id'));
        //     }
        //   });
        // });
    });
});
