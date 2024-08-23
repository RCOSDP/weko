import jQuery from "jquery";
jQuery.noConflict();
jQuery(document).ready(function($) {
    /*
    --------------------------------------------------------
    suggest.js - Input Suggest
    Version 2.2 (Update 2010/09/14)

    Copyright (c) 2006-2010 onozaty (http://www.enjoyxstudy.com)

    Released under an MIT-style license.

    For details, see the web site:
     http://www.enjoyxstudy.com/javascript/suggest/

    --------------------------------------------------------
    */
    function checkDiscofeedList(json, list) {
        var newList = new Array();
        var index = 0;
        var matchFlg = false;

        for (var j = 0, length = list.length; j < length; j++) {
            for (var i in json) {
                if (json[i].entityID == list[j][0]) {
                    newList[index] = list[j];
                    matchFlg = true;
                    index++;
                    break;
                }
            }
        }
        return newList;
    }

    function setDiscofeedList(json) {
        if (!json) return;
        let inc_search_list = checkDiscofeedList(json, inc_search_list);
        let favorite_list = checkDiscofeedList(json, favorite_list);
        let hint_list = checkDiscofeedList(json, hint_list);
    }

    // It adds it to window event.
    function start() {
        new Suggest.Local(
            "keytext", // element id of input area
            "view_incsearch", // element id of IdP list display area
            "view_incsearch_animate", // element id of IdP list display animate area
            "view_incsearch_scroll", // element id of IdP list display scroll area
            inc_search_list, // IdP list
            favorite_list, // IdP list (Favorite)
            hint_list, // IdP list (Hint IP, Domain)
            "dropdown_img", // element id of dropdown image
            "wayf_submit_button", // element id of select button
            "clear_a", // element id of clear
            initdisp, // Initial display of input area
            dispDefault, // Select IdP display of input area
            dropdown_down, // URL of deropdown down image
            dropdown_up, // URL of deropdown up image
            favorite_idp_group, // favorite idp list group
            hint_idp_group, // hint idp list group
            { dispMax: 500, showgrp: wayf_show_categories }); // option
    }

    // DiscoFeed
    if (typeof(wayf_discofeed_url) != "undefined" && wayf_discofeed_url != '') {
        var urldomain = wayf_discofeed_url.split('/')[2];
        if (window.location.hostname != urldomain && window.XDomainRequest) {
            var xdr = new XDomainRequest();
            xdr.onload = function() {
                setDiscofeedList(eval("(" + xdr.responseText + ")"));
            }
            xdr.open("get", wayf_discofeed_url, false);
            xdr.send(null);
        } else {
            $.ajax({
                type: 'get',
                url: wayf_discofeed_url,
                dataType: 'json',
                async: false,
                success: function(json) {
                    setDiscofeedList(json);
                }
            });
        }
    }

    window.addEventListener ?
        window.addEventListener('load', start, false) :
        window.attachEvent('onload', start);

    if (!Suggest) {
        var Suggest = {};
    }
    /*-- KeyCodes -----------------------------------------*/
    Suggest.Key = {
        TAB: 9,
        RETURN: 13,
        ESC: 27,
        UP: 38,
        DOWN: 40
    };

    /*-- Utils --------------------------------------------*/
    Suggest.copyProperties = function(dest, src) {
        for (var property in src) {
            dest[property] = src[property];
        }
        return dest;
    };

    /*-- Suggest.Local ------------------------------------*/
    Suggest.Local = function() {
        this.initialize.apply(this, arguments);
    };
    Suggest.Local.prototype = {
        initialize: function(input, suggestArea, animateArea, scrollArea, candidateList, favoriteList, hintList,
            dnupImgElm, selectElm, clearElm, initDisp, dispDefault, dnImgURL, upImgURL, favoriteIdpGroup, hintIdpGroup) {

            this.input = this._getElement(input);
            this.suggestArea = this._getElement(suggestArea);
            this.animateArea = this._getElement(animateArea);
            this.scrollArea = this._getElement(scrollArea);
            this.candidateList = candidateList;
            this.favoriteList = favoriteList;
            this.hintList = hintList;
            this.dnupImgElm = this._getElement(dnupImgElm);
            this.selectElm = this._getElement(selectElm);
            this.clearElm = this._getElement(clearElm);
            this.initDisp = initDisp;
            this.dispDefault = dispDefault;
            this.dnImgURL = dnImgURL;
            this.upImgURL = upImgURL;
            this.favoriteIdpGroup = favoriteIdpGroup;
            this.hintIdpGroup = hintIdpGroup;
            this.setInputText(dispidp);
            this.oldText = (this.initDisp == this.getInputText()) ?
                '' : this.getInputText();
            this.searchFlg = false;
            this.noMatch = true;
            this.userAgentFlg = 0;
            this.discofeedFlg = false;

            if (this.candidateList.length > 0) {
                // favorite IdP List
                if (this.favoriteList.length > 0) {
                    this.candidateList = this.favoriteList.concat(this.candidateList);
                }
                // hint(IP, Domain) IdP List
                if (this.hintList.length > 0) {
                    this.candidateList = this.hintList.concat(this.candidateList);
                }
            }
            if (this.candidateList.length == 0) {
                this.setInputText(this.initDisp);
            }

            if (arguments[16]) this.setOptions(arguments[16]);

            // reg event
            this._addEvent(this.input, 'focus', this._bind(this.tabFocus));
            this._addEvent(this.input, 'blur', this._bind(this.tabBlur));

            var keyevent = 'keydown';
            if (window.opera || (navigator.userAgent.indexOf('Gecko') >= 0 && navigator.userAgent.indexOf('KHTML') == -1)) {
                keyevent = 'keypress';
            }
            this._addEvent(this.input, keyevent, this._bindEvent(this.keyEvent));
            this._addEvent(this.dnupImgElm, keyevent, this._bindEvent(this.keyEvent));
            this._addEvent(this.clearElm, keyevent, this._bindEvent(this.keyEvent));
            this._addEvent(this.dnupImgElm, 'click', this._bindEvent(this.elementClick));
            this._addEvent(this.clearElm, 'click', this._bindEvent(this.elementClick));
            this._addEvent(this.clearElm, 'focus', this._bindEvent(this.changeClass, this.classActive));
            this._addEvent(this.clearElm, 'blur', this._bindEvent(this.changeClass, this.classDefault));
            this._addEvent(this.clearElm, 'mouseover', this._bindEvent(this.changeClass, this.classActive));
            this._addEvent(this.clearElm, 'mouseout', this._bindEvent(this.changeClass, this.classDefault));

            // init
            this.clearSuggestArea();
            $('#' + this.animateArea.id).hide();
            this.checkUserAgent();
            this.checkNoMatch(this.oldText);
            if (this.userAgentFlg == 1) {
                this.touchScroll();
            }


        },

        // options
        interval: 500,
        dispMax: 20,
        listTagName: 'div',
        prefix: false,
        ignoreCase: true,
        highlight: false,
        dispAllKey: false,
        classMouseOver: 'over',
        classSelect: 'select',
        classDefault: 'default',
        classActive: 'active',
        classGroup: 'list_group',
        classIdPNm: 'list_idp',
        classGroupFavorite: 'list_group_favorite',
        classIdPNmFavorite: 'list_idp_favorite',
        classGroupHint: 'list_group_hint',
        classIdPNmHint: 'list_idp_hint',
        dispListTime: 300,
        showgrp: true,
        hookBeforeSearch: function() {},

        setOptions: function(options) {
            Suggest.copyProperties(this, options);
        },

        checkUserAgent: function() {
            if (navigator.userAgent.indexOf('Android 2') > 0) {
                this.userAgentFlg = 1;
            } else if (navigator.userAgent.indexOf('iPhone') > 0 ||
                navigator.userAgent.indexOf('iPad') > 0 ||
                navigator.userAgent.indexOf('iPod') > 0 ||
                navigator.userAgent.indexOf('Android') > 0) {
                this.userAgentFlg = 2;
            } else {
                this.userAgentFlg = 0;
            }
        },

        checkNoMatch: function(text) {
            var flg = true;

            if (text != '') {
                for (var i = 0, length = this.candidateList.length; i < length; i++) {
                    for (var j = 3, length2 = this.candidateList[i].length; j < length2; j++) {
                        if (text.toLowerCase() == this.candidateList[i][j].toLowerCase()) {
                            flg = false;
                            break;
                        }
                    }
                    if (!flg) {
                        break;
                    }
                }
            }

            var search_cnt = 0;
            if (this.suggestList) {
                search_cnt = this.suggestList.length - this.hintList.length - this.favoriteList.length;
            }
            if (search_cnt == 1) {
                this.setStyleActive(this.suggestList[this.hintList.length + this.favoriteList.length]);
                let hiddenKeyText = this.candidateList[this.suggestIndexList[this.hintList.length + this.favoriteList.length]][2];
                this.activePosition = this.hintList.length + this.favoriteList.length;
                flg = false;
            }

            this.noMatch = flg;
        },

        elementClick: function(event) {
            var element = this._getEventElement(event);
            if (element.id == this.input.id) {
                this.execSearch();
            } else if (element.id == this.dnupImgElm.id) {
                if (this.dnupImgElm.src == this.dnImgURL) {
                    if (this.getInputText() == this.initDisp) this.setInputText('');
                    this.execSearch();
                } else {
                    this.closeList();
                }
            } else if (element.id == this.clearElm.id) {
                // Reset all search
                $("input[name='wayf_categories_name']").attr("checked", false);
                $("input[name='wayf_categories_name'][value='']").attr("checked", true);
                $("input[name='wayf_type_name']").attr("checked", false);
                $("input[name='wayf_type_name'][value='All']").attr("checked", true);
                this.candidateList = inc_search_list;
                this.setInputText('');
                this.execSearch();
            }
        },

        changeClass: function(event, classname) {
            var element = this._getEventElement(event);
            element.className = classname;
        },

        execSearch: function() {
            this.input.focus();
            if (!this.suggestList) {
                this.searchFlg = true;
                this.checkLoop();
            }
        },

        tabFocus: function() {
            if (!this.suggestList) {
                if (this.getInputText() == this.initDisp) this.setInputText('');
            }
        },

        tabBlur: function() {
            if (!this.suggestList) {
                if (this.getInputText() == '') this.setInputText(this.initDisp);
            }
        },

        closeList: function() {
            this.changeUnactive();
            this.oldText = (this.initDisp == this.getInputText()) ?
                '' : this.getInputText();
            $('#' + this.animateArea.id).hide();

            if (this.timerId) clearTimeout(this.timerId);
            this.timerId = null;

            setTimeout(this._bind(this.clearSuggestArea), 100);
            if (document.activeElement.id != this.input.id && this.getInputText() == '')
                this.setInputText(this.initDisp);
        },

        checkLoop: function() {
            var text = this.getInputText();
            if (text == this.initDisp) {
                text = '';
            }

            this.noMatch = true;

            if (text != this.oldText || this.searchFlg) {
                hiddenKeyText = '';
                this.searchFlg = false;
                this.oldText = text;
                this.search();
            }

            if (this.timerId) clearTimeout(this.timerId);
            this.timerId = setTimeout(this._bind(this.checkLoop), this.interval);
        },

        search: function() {
            var radioValue = $("input[name='wayf_type_name']:checked").val();

            // init
            this.clearSuggestArea();

            var text = this.getInputText();

            if (text == null || text == this.initDisp) return;

            var categoriesFilterText = $("input[name='wayf_categories_name']:checked").val();
            if (categoriesFilterText != undefined) text = categoriesFilterText;

            if (!this.discofeedFlg || radioValue != undefined) {
                this.candidateList = inc_search_list;
                this.favoriteList = favorite_list;
                this.hintList = hint_list;
                if (this.candidateList.length > 0) {
                    // favorite IdP List
                    if (this.favoriteList.length > 0) {
                        this.candidateList = this.favoriteList.concat(this.candidateList);
                    }
                    // hint(IP, Domain) IdP List
                    if (this.hintList.length > 0) {
                        this.candidateList = this.hintList.concat(this.candidateList);
                    }
                }
                if (this.candidateList.length == 0) {
                    this.setInputText(this.initDisp);
                }
                this.discofeedFlg = true;
            }

            this.hookBeforeSearch(text);
            var resultList = this._search(text);
            if (resultList.length != 0) {
                this.createSuggestArea(resultList);
            } else {
                $('#' + this.animateArea.id).hide();
            }
            this.checkNoMatch(this.getInputText());
            this.selectElm.disabled = this.noMatch;
        },

        _search: function(text) {

            var resultList = [];
            var temp;
            this.suggestIndexList = [];

            for (var i = 0, length = this.candidateList.length; i < length; i++) {
                for (var j = 3, length2 = this.candidateList[i].length; j < length2; j++) {
                    if (text == '' ||
                        this.isMatch(this.candidateList[i][j], text) != null ||
                        this.candidateList[i][1] == this.hintIdpGroup ||
                        this.candidateList[i][1] == this.favoriteIdpGroup) {
                        resultList.push(this.candidateList[i]);
                        this.suggestIndexList.push(i);
                        break;
                    }
                }
                if (this.dispMax != 0 && resultList.length >= this.dispMax) break;
            }
            return resultList;
        },

        isMatch: function(value, pattern) {

            if (value == null) return null;

            var pos = (this.ignoreCase) ?
                value.toLowerCase().indexOf(pattern.toLowerCase()) :
                value.indexOf(pattern);

            if ((pos == -1) || (this.prefix && pos != 0)) return null;
            if (this.highlight) {
                return (this._escapeHTML(value.substr(0, pos)) + '<strong>' +
                    this._escapeHTML(value.substr(pos, pattern.length)) +
                    '</strong>' + this._escapeHTML(value.substr(pos + pattern.length)));
            } else {
                return this._escapeHTML(value);
            }
        },

        clearSuggestArea: function() {
            this.suggestArea.innerHTML = '';
            this.suggestList = null;
            this.suggestIndexList = null;
            this.activePosition = null;
            this.dnupImgElm.src = this.dnImgURL;


        },

        createSuggestArea: function(resultList) {

            this.suggestList = [];
            var typeList = [];
            this.inputValueBackup = this.input.value;

            if (this.userAgentFlg == 1) {
                $('#' + this.scrollArea.id).flickable('disable');
            }
            var oldGroup = '';
            $('#' + this.suggestArea.id).css('width', '');
            for (var i = 0, length = resultList.length; i < length; i++) {
                if (this.showgrp && oldGroup != resultList[i][1]) {
                    var element = document.createElement(this.listTagName);
                    if (resultList[i][1] == this.hintIdpGroup) {
                        element.className = this.classGroupHint;
                        element.innerHTML = '&nbsp;' + this.hintIdpGroup;
                    } else if (resultList[i][1] == this.favoriteIdpGroup) {
                        element.className = this.classGroupFavorite;
                        element.innerHTML = '&nbsp;' + this.favoriteIdpGroup;
                    } else {
                        var typeListText = resultList.push(resultList[i][1]);
                        element.className = this.classGroup;
                        element.innerHTML = '&nbsp;' + resultList[i][1];
                    }
                    this.suggestArea.appendChild(element);
                    oldGroup = resultList[i][1];
                }

                var element = document.createElement(this.listTagName);
                if (resultList[i][1] == this.hintIdpGroup) {
                    element.className = this.classIdPNmHint;
                } else if (resultList[i][1] == this.favoriteIdpGroup) {
                    element.className = this.classIdPNmFavorite;
                } else {
                    element.className = this.classIdPNm;
                }
                if (this.userAgentFlg == 0) {
                    element.innerHTML = resultList[i][2];
                } else {
                    element.innerHTML = '<a onclick="">' + resultList[i][2] + '</a>';
                }
                this.suggestArea.appendChild(element);

                this._addEvent(element, 'click', this._bindEvent(this.listClick, i));
                this._addEvent(element, 'mouseover', this._bindEvent(this.listMouseOver, i));
                this._addEvent(element, 'mouseout', this._bindEvent(this.listMouseOut, i));

                this.suggestList.push(element);

            }

            this.scrollArea.scrollTop = 0;
            this.dnupImgElm.src = this.upImgURL;
            $('#' + this.animateArea.id).slideDown(this.dispListTime);
            var scrollbarWidth = 0;
            if (this.userAgentFlg == 0) scrollbarWidth = 19;
            var scrollAreaWidth = Number($('#' + this.scrollArea.id).css('width').replace('px', ''));
            var suggestAreaWidth = Number($('#' + this.suggestArea.id).css('width').replace('px', ''));
            if (scrollAreaWidth > suggestAreaWidth) {
                $('#' + this.suggestArea.id).css('width', scrollAreaWidth - scrollbarWidth + 'px');
            }
            if (this.userAgentFlg == 1) {
                $('#' + this.scrollArea.id).flickable('enable');
                $('#' + this.scrollArea.id).flickable('disable');
                $('#' + this.scrollArea.id).flickable('enable');
            }
        },

        touchScroll: function() {
            $('#' + this.scrollArea.id).flickable({
                disabled: false,
                elasticConstant: 0.2,
                friction: 0.7
            });
        },

        getInputText: function() {
            return this.input.value;
        },

        setInputText: function(text) {
            this.input.value = text;
        },

        // key event
        keyEvent: function(event) {

            if (!this.timerId) {
                this.timerId = setTimeout(this._bind(this.checkLoop), this.interval);
            }

            if (this._getEventElement(event).id == this.dnupImgElm.id ||
                this._getEventElement(event).id == this.clearElm.id) {
                if (event.keyCode == Suggest.Key.RETURN) {
                    this._stopEvent(event);
                    this.elementClick(event);
                }
            } else if (this.dispAllKey && event.ctrlKey &&
                this.getInputText() == '' &&
                !this.suggestList &&
                event.keyCode == Suggest.Key.DOWN) {
                // dispAll
                this._stopEvent(event);
                this.keyEventDispAll();
            } else if (event.keyCode == Suggest.Key.UP ||
                event.keyCode == Suggest.Key.DOWN) {
                // search
                if (!this.suggestList && event.keyCode == Suggest.Key.DOWN) {
                    this.execSearch();
                }
                // key move
                if (this.suggestList && this.suggestList.length != 0) {
                    hiddenKeyText = '';
                    this._stopEvent(event);
                    this.keyEventMove(event.keyCode);
                }
            } else if (event.keyCode == Suggest.Key.RETURN) {
                // fix
                if (this.selectElm.disabled == true) {
                    if (this.suggestList.length != 1) {
                        this._stopEvent(event);
                        //          this.keyEventReturn();
                    }
                }
            } else if (event.keyCode == Suggest.Key.ESC) {
                // clear
                this._stopEvent(event);
                setTimeout(this._bind(this.keyEventEsc), 5);
            } else if (event.keyCode == Suggest.Key.TAB) {
                if (this.getInputText() == '') this.setInputText(this.initDisp);
                if (this.suggestList) this.closeList();
            } else {
                this.keyEventOther(event);
            }
        },

        keyEventDispAll: function() {

            // init
            this.clearSuggestArea();

            this.oldText = this.getInputText();

            this.suggestIndexList = [];
            for (var i = 0, length = this.candidateList.length; i < length; i++) {
                this.suggestIndexList.push(i);
            }

            this.createSuggestArea(this.candidateList);
        },

        keyEventMove: function(keyCode) {

            this.changeUnactive();

            if (keyCode == Suggest.Key.UP) {
                // up
                if (this.activePosition == null) {
                    this.activePosition = this.suggestList.length - 1;
                } else {
                    this.activePosition--;
                    if (this.activePosition < 0) {
                        this.activePosition = null;
                        this.input.value = this.inputValueBackup;
                        this.scrollArea.scrollTop = 0;
                        return;
                    }
                }
            } else {
                // down
                if (this.activePosition == null) {
                    this.activePosition = 0;
                } else {
                    this.activePosition++;
                }

                if (this.activePosition >= this.suggestList.length) {
                    this.activePosition = null;
                    this.input.value = this.inputValueBackup;
                    this.scrollArea.scrollTop = 0;
                    return;
                }
            }

            this.changeActive(this.activePosition);
        },

        keyEventReturn: function() {

            if (this.activePosition != null && this.activePosition >= 0) {
                this.selectElm.disabled = false;
            }
            this.clearSuggestArea();
            this.moveEnd();
        },

        keyEventEsc: function() {

            this.setInputText('');
            this.selectElm.disabled = true;
            hiddenKeyText = '';
            this.closeList();
        },

        keyEventOther: function(event) {},

        changeActive: function(index) {

            this.setStyleActive(this.suggestList[index]);

            this.setInputText(this.candidateList[this.suggestIndexList[index]][2]);

            this.oldText = this.getInputText();
            this.input.focus();
            this.selectElm.disabled = false;
        },

        changeUnactive: function() {

            if (this.suggestList != null &&
                this.suggestList.length > 0 &&
                this.activePosition != null) {
                this.setStyleUnactive(this.suggestList[this.activePosition], this.activePosition);
            }
        },

        listClick: function(event, index) {

            this.closeList();
            this.changeUnactive();
            this.activePosition = index;
            this.changeActive(index);

            this.moveEnd();

            if (index != null && index >= 0) {
                this.selectElm.disabled = false;
            }
        },

        listMouseOver: function(event, index) {
            this.setStyleMouseOver(this._getEventElement(event));
        },

        listMouseOut: function(event, index) {

            if (!this.suggestList) return;

            var element = this._getEventElement(event);

            if (index == this.activePosition) {
                this.setStyleActive(element);
            } else {
                this.setStyleUnactive(element, index);
            }
        },

        setStyleActive: function(element) {
            element.className = this.classSelect;

            // auto scroll
            var offset = element.offsetTop;
            var offsetWithHeight = offset + element.clientHeight;

            if (this.scrollArea.scrollTop > offset) {
                this.scrollArea.scrollTop = offset
            } else if (this.scrollArea.scrollTop + this.scrollArea.clientHeight < offsetWithHeight) {
                this.scrollArea.scrollTop = offsetWithHeight - this.scrollArea.clientHeight;
            }
        },

        setStyleUnactive: function(element, index) {
            if (index < this.hintList.length + this.favoriteList.length) {
                if (this.hintList.length > 0 && index < this.hintList.length) {
                    element.className = this.classIdPNmHint;
                } else {
                    element.className = this.classIdPNmFavorite;
                }
            } else {
                element.className = this.classIdPNm;
            }
        },

        setStyleMouseOver: function(element) {
            element.className = this.classMouseOver;
        },

        moveEnd: function() {

            if (this.input.createTextRange) {
                this.input.focus(); // Opera
                var range = this.input.createTextRange();
                range.move('character', this.input.value.length);
                range.select();
            } else if (this.input.setSelectionRange) {
                this.input.setSelectionRange(this.input.value.length, this.input.value.length);
            }
        },

        // Utils
        _getElement: function(element) {
            return (typeof element == 'string') ? document.getElementById(element) : element;
        },
        _addEvent: (window.addEventListener ?
            function(element, type, func) {
                element.addEventListener(type, func, false);
            } :
            function(element, type, func) {
                element.attachEvent('on' + type, func);
            }),
        _stopEvent: function(event) {
            if (event.preventDefault) {
                event.preventDefault();
                event.stopPropagation();
            } else {
                event.returnValue = false;
                event.cancelBubble = true;
            }
        },
        _getEventElement: function(event) {
            return event.target || event.srcElement;
        },
        _bind: function(func) {
            var self = this;
            var args = Array.prototype.slice.call(arguments, 1);
            return function() { func.apply(self, args); };
        },
        _bindEvent: function(func) {
            var self = this;
            var args = Array.prototype.slice.call(arguments, 1);
            return function(event) {
                event = event || window.event;
                func.apply(self, [event].concat(args));
            };
        },
        _escapeHTML: function(value) {
            return value.replace(/\&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                .replace(/\"/g, '&quot;').replace(/\'/g, '&#39;');
        }
    };

    /*-- Suggest.LocalMulti ---------------------------------*/
    Suggest.LocalMulti = function() {
        this.initialize.apply(this, arguments);
    };
    Suggest.copyProperties(Suggest.LocalMulti.prototype, Suggest.Local.prototype);

    Suggest.LocalMulti.prototype.delim = ' '; // delimiter

    Suggest.LocalMulti.prototype.keyEventReturn = function() {

        this.clearSuggestArea();
        this.input.value += this.delim;
        this.moveEnd();
    };

    Suggest.LocalMulti.prototype.keyEventOther = function(event) {

        if (event.keyCode == Suggest.Key.TAB) {
            // fix
            if (this.suggestList && this.suggestList.length != 0) {
                this._stopEvent(event);

                if (!this.activePosition) {
                    this.activePosition = 0;
                    this.changeActive(this.activePosition);
                }

                this.clearSuggestArea();
                this.input.value += this.delim;
                if (window.opera) {
                    setTimeout(this._bind(this.moveEnd), 5);
                } else {
                    this.moveEnd();
                }
            }
        }
    };

    Suggest.LocalMulti.prototype.listClick = function(event, index) {

        this.changeUnactive();
        this.activePosition = index;
        this.changeActive(index);

        this.input.value += this.delim;
        this.moveEnd();
    };

    Suggest.LocalMulti.prototype.getInputText = function() {

        var pos = this.getLastTokenPos();

        if (pos == -1) {
            return this.input.value;
        } else {
            return this.input.value.substr(pos + 1);
        }
    };

    Suggest.LocalMulti.prototype.setInputText = function(text) {

        var pos = this.getLastTokenPos();

        if (pos == -1) {
            this.input.value = text;
        } else {
            this.input.value = this.input.value.substr(0, pos + 1) + text;
        }
    };

    Suggest.LocalMulti.prototype.getLastTokenPos = function() {
        return this.input.value.lastIndexOf(this.delim);
    };
});
