const MAIN_CONTENT_TYPE = "Main contents";
const FREE_DESCRIPTION_TYPE = "Free description";
const NOTICE_TYPE = "Notice";
const HIDE_REST_DEFAULT = "Hide the rest";
const READ_MORE_DEFAULT = "Read more";
const NEW_ARRIVALS = "New arrivals";
const ACCESS_COUNTER = "Access counter";
const THEME_SIMPLE = 'simple';
const THEME_SIDE_LINE = 'side_line';
const THEME_DEFAULT = 'default';
const MENU_TYPE = "Menu";
const DEFAULT_REPOSITORY = "Root Index";
const HEADER_TYPE = "Header";
const FOOTER_TYPE = "Footer";
const BORDER_STYLE_DOUBLE = "double";
const BORDER_STYLE_NONE = "none";
const INTERVAL_TIME = 60000; //one minute

(function() {
    getWidgetDesignSetting();
    window.lodash = _.noConflict();
}());

var PageBodyGrid = function() {
    this.init = function() {
        var options = {
            width: 12,
            float: true,
            verticalMargin: 4,
            cellHeight: 100,
            acceptWidgets: '.grid-stack-item'
        };
        var widget = $('#page_body');
        widget.gridstack(options);
        this.grid = widget.data('gridstack');
    };

    this.addNewWidget = function(node, index) {
        this.grid.addWidget($(this.widgetTemplate(node, index)), node.x, node.y, node.width, node.height);
        return false;
    }.bind(this);

    this.updateMainContent = function(node) {
        var mainContents = $("#main_contents");
        var titleMainContent = $("#title-main-content");
        var backgroundColorMainContent = $("#background-color-main-content");
        var indexBackground = $("#index-background");
        var panelDefault = $(".panel-default");
        var panelHeadingMainContents = $("#panel-heading-main-contents");
        var panel = $(".panel");

        var labelMainContent = node.multiLangSetting.label;
        var backgroundColor = node.background_color;
        var frameBorderColorMainContent = node.frame_border_color;
        var labelTextColor = node.label_text_color;
        var labelEnable = node.label_enable;

        titleMainContent.text(labelMainContent);
        titleMainContent.css("color", labelTextColor);
        backgroundColorMainContent.css("background-color", backgroundColor);
        indexBackground.css("background-color", backgroundColor);
        indexBackground.css("border-bottom-right-radius", "3px");
        indexBackground.css("border-bottom-left-radius", "3px");
        panelDefault.css("border-color", frameBorderColorMainContent);
        panelDefault.css("background-color", backgroundColor);
        panel.css("box-shadow", "none");

        $(".list-group-item").each(function() {
            if (!$(this).hasClass("style_li")) {
                $(this).css("background-color", backgroundColor);
            }
        });

        if (!labelEnable) {
            panelHeadingMainContents.css('display', 'none');
        }

        var style = this.addStyle(node);
        mainContents.append(style);
        this.buildMainContentTheme(node);
        this.grid.update(mainContents, node.x, node.y, node.width, node.height);
    };

    this.addStyle = function(node) {
        var backgroundColor = node.background_color;
        var frameBorderColorMainContent = node.frame_border_color;
        var labelColor = node.label_color;
        return '<style>' +
            '#main_contents .panel{' +
            'background-color: ' + backgroundColor + ' !important;' +
            'border-color: ' + frameBorderColorMainContent + ';' +
            '}' +
            '#main_contents .active > a{' +
            'background-color: ' + labelColor + ';' +
            '}' +
            '#main_contents .panel-heading{' +
            'background-color: ' + labelColor + ';' +
            '}' +
            '.panel-default > .panel-heading{' +
            'border-bottom: ' + '1px ' + 'solid ' + frameBorderColorMainContent + ';' +
            '}' +
            '</style>';
    };

    this.buildMainContentTheme = function(node) {
        var panelHeadingMainContents = $("#panel-heading-main-contents");
        var backgroundColorMainContent = $("#background-color-main-content");
        var panelMainContent = $("#panel-main-content");
        var borderStyle = node.border_style;
        var frameBorderColorMainContent = node.frame_border_color;
        var theme = node.theme;
        var borderRadius;
        var pxBorder;
        if (borderStyle === BORDER_STYLE_DOUBLE) {
            pxBorder = "3px ";
            borderRadius = "1px";
        } else if (borderStyle === BORDER_STYLE_NONE) {
            pxBorder = "0px";
            borderRadius = "3px";
        } else {
            pxBorder = "1px ";
            borderRadius = "3px";
        }

        if (theme === THEME_SIMPLE) {
            borderRadius = "0px";
            pxBorder = "none";
            panelMainContent.css("border", pxBorder);
            panelHeadingMainContents.css('border-radius', borderRadius);
            panelHeadingMainContents.css("border-bottom", pxBorder);
        } else if (theme === THEME_DEFAULT) {
            panelMainContent.css("border", pxBorder + ' ' + borderStyle + ' ' + frameBorderColorMainContent);
            backgroundColorMainContent.css("border-top", pxBorder + borderStyle + ' ' + frameBorderColorMainContent);
            backgroundColorMainContent.css('border-bottom-left-radius', borderRadius);
            backgroundColorMainContent.css('border-bottom-right-radius', borderRadius);
            panelHeadingMainContents.css("border-bottom", 'none');
            panelHeadingMainContents.css("border-top-right-radius", borderRadius);
            panelHeadingMainContents.css("border-top-left-radius", borderRadius);
        } else {
            panelMainContent.css("border-left", pxBorder + ' ' + borderStyle + ' ' + frameBorderColorMainContent);
            panelMainContent.css("border-right", 'none');
            panelMainContent.css("border-top", 'none');
            panelMainContent.css("border-bottom", 'none');
            panelMainContent.css("border-top-left-radius", '0px');
            panelMainContent.css("border-bottom-left-radius", '0px');
            panelHeadingMainContents.css('border-radius', '0px');
            panelHeadingMainContents.css('border-bottom', 'none');
        }
    };


    this.updateHeaderPage = function(node) {
        var headerElement = $("#header");
        if (headerElement.length) {
            var headerNav = $("#header_nav");
            var headerContent = $("#header_content");
            if (node.background_color) {
                headerNav.css({ "background-color": node.background_color });
            }
            if (node.multiLangSetting && node.multiLangSetting.description) {
                headerContent.css({ "width": "calc(100vw - 490px)", "height": "100px", "overflow": "hidden" });
                headerContent.html(node.multiLangSetting.description.description);
            }
            this.grid.update(headerElement, node.x, node.y, node.width, node.height);
            headerElement.removeClass("hidden");
        }
    };

    this.loadGrid = function(widgetListItems) {
        var items = GridStackUI.Utils.sort(widgetListItems);
        var hasMainContent = false;
        items.forEach(function(node) {
            if (MAIN_CONTENT_TYPE === node.type) {
                this.updateMainContent(node);
                hasMainContent = true;
                return false;
            } else if (HEADER_TYPE === node.type) {
                var community_id = $("#community-id").text();
                if (!community_id) {
                    this.updateHeaderPage(node);
                }
                return false;
            }
        }, this);

        ///Pages do not have to have main content, so hide if not in list
        if (!hasMainContent) {
            $("#main_contents").hide(); // remove(); or empty() ?
        }
        for (var i = 0; i < items.length; i++) {
            var node = items[i];
            var community_id = $("#community-id").text();
            if (node.type === HEADER_TYPE && community_id) {
                this.addNewWidget(node, i);
            } else if (![MAIN_CONTENT_TYPE, HEADER_TYPE].includes(node.type)) {
                this.addNewWidget(node, i);
            }
        }
        return false;
    }.bind(this);

    this.buildNoticeType = function(languageDescription, index) {
        var description = "";
        var moreDescriptionID = (NOTICE_TYPE + "_" + index).trim();
        var linkID = "writeMoreNotice_" + index;
        var moreDescription = "";
        var templateWriteMoreNotice = '<div id="' + moreDescriptionID + '" style="display: none;">' +
            moreDescription + '</div>';

        if (languageDescription.more_description) {
            moreDescription = languageDescription.more_description;
            var hideRest = (languageDescription.hide_the_rest) ? languageDescription.hide_the_rest : HIDE_REST_DEFAULT;
            var readMore = (languageDescription.read_more) ? languageDescription.read_more : READ_MORE_DEFAULT;
            templateWriteMoreNotice = '</br>' +
                '<div id="' + moreDescriptionID + '" style="display: none;">' + moreDescription + '</div>' +
                '<a id="' + linkID + '" class="writeMoreNoT" onclick="handleMoreNoT(\'' + moreDescriptionID + '\',\'' +
                linkID + '\',\'' + escapeHtml(readMore) + '\', \'' + escapeHtml(hideRest) + '\')">' + readMore +
                '</a>';
        }

        if (!$.isEmptyObject(languageDescription)) {
            description = languageDescription.description + templateWriteMoreNotice;
        }
        return description;
    };

    this.buildAccessCounter = function(widgetId, created_date, languageDescription) {
        var data = this.getAccessTopPageValue();
        var result = 0;
        // Convert to display-able number
        if (data && data[widgetId] && data[widgetId][created_date]) {
            var widget = data[widgetId][created_date];
            var initNum = widget.access_counter ? Number(widget.access_counter) : 0;
            result = widget.all.count ? Number(widget.all.count) : 0;
            if (!Number.isNaN(initNum)) {
                result = result + initNum;
            }
        }

        var precedingMessage = languageDescription.preceding_message ? languageDescription.preceding_message + " " : "";
        var followingMessage = languageDescription.following_message ? " " + languageDescription.following_message : "";
        var otherMessage = languageDescription.other_message ? languageDescription.other_message : "";

        return '<div>' +
            ' <div class="counter-container">' +
            precedingMessage + '<span data-widget-id="' + widgetId + '" data-created-date="' + created_date +
            '" class = "text-access-counter">' + result + '</span>' + followingMessage +
            ' </div>' +
            ' <div>' + otherMessage + '</div>' +
            '</div>';
    };

    this.buildNewArrivals = function(widgetID, term, rss, id, count) {
        $.ajax({
            method: 'GET',
            url: '/api/admin/get_new_arrivals/' + widgetID,
            headers: {
                'Content-Type': 'application/json'
            },
            success: function(response) {
                var result = response.data;
                var rssHtml = '';
                if (term == 'Today') {
                    term = 0;
                }
                if (rss) {
                    var rssURL = "/rss/records?term=" + term + "&count=" + count;
                    rssHtml = '<a class="" target="_blank" rel="noopener noreferrer" href="' + rssURL + '"><i class="fa fa-rss"></i></a>';
                }
                var innerHTML = '<div class= "rss text-right">' + rssHtml + '</div>' +
                    '<div>';
                for (var data in result) {
                    innerHTML += '<div class="no-li-style no-padding-col"><li><a class="a-new-arrivals arrival-scale" href="' + result[data].url + '">' + result[data].name + '</a></li></div>';
                }
                innerHTML += '</div>';
                $("#" + id).append(innerHTML);
            }
        });
    };

    this.buildMenu = function(repoID, widgetID, menuID, settings) {
        var current_language = $("#current_language").val() || 'en';
        $.ajax({
            method: 'GET',
            url: '/api/admin/get_page_endpoints/' + widgetID + '/' + current_language,
            headers: {
                'Content-Type': 'application/json'
            },
            success: function(response) {
                var endpoints = response.endpoints;
                var repoHomeURL = (repoID === DEFAULT_REPOSITORY) ? '/' : ('/' + '?community=' + repoID);
                var navbarID = 'widgetNav_' + widgetID; // Re-use to build unique class ids
                var navbarClass = settings.menu_orientation === 'vertical' ?
                    'nav nav-pills nav-stacked pull-left ' + navbarID : 'nav navbar-nav';
                var mainLayoutTitle = "";
                var childNavBar = "";
                var navbarHeader = "";
                for (var i in endpoints) { // Create links
                    var liClass = '';
                    var communityArgs = (repoID === DEFAULT_REPOSITORY) ? '' : '?community=' + repoID;
                    var title = endpoints[i].title;
                    var endpointsURL = endpoints[i].url;
                    if (endpoints[i].is_main_layout) {
                        mainLayoutTitle = title;
                    } else {
                        if (window.location.pathname === endpointsURL) {
                            liClass = 'class="active"';
                        }
                        childNavBar += '<li ' + liClass + '><a href="' + endpointsURL + communityArgs + '">' + title + '</a></li>';
                    }
                }

                if (mainLayoutTitle === "" && Array.isArray(settings.menu_show_pages) && settings.menu_show_pages.includes("0")) {
                    mainLayoutTitle = "Main Layout";
                }

                if (mainLayoutTitle) {
                    var mainLayoutActive = "";
                    var currentMainLayout = window.location.pathname + window.location.search;
                    var repoHomeURL2 = "/communities/" + repoID + "/?view=weko";
                    if (currentMainLayout === repoHomeURL || currentMainLayout === repoHomeURL2) {
                        mainLayoutActive = 'active';
                    }
                    navbarHeader =
                        '<div class="navbar-header">' +
                        '      <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#' + navbarID + '" aria-expanded="false">' +
                        '        <span class="icon-bar"></span>' +
                        '        <span class="icon-bar"></span>' +
                        '        <span class="icon-bar"></span>' +
                        '      </button>' +
                        '      <a class="navbar-brand ' + mainLayoutActive + '" href="' + repoHomeURL + '">' + mainLayoutTitle + '</a>' +
                        '    </div>';
                }

                var navbar =
                    '<style>' + // Renaming classes allows for multiple menus on page
                    '.navbar-default.' + navbarID + ' .navbar-brand {' +
                    '    color:' + settings.menu_default_color + ';' +
                    '}' +
                    '.navbar-default.' + navbarID + ' .navbar-header > a:hover, .navbar-default.' + navbarID + ' .navbar-header > a.active {' +
                    '    background-color:' + settings.menu_active_bg_color + ';' +
                    '    color:' + settings.menu_active_color + ';' +
                    '}' +
                    '  .navbar-default.' + navbarID + ' .navbar-nav > li > a, .nav-pills > li > a {' +
                    '    color:' + settings.menu_default_color + ';' +
                    '  }' +
                    '  .navbar-default.' + navbarID + ' .navbar-nav > li > a:hover, .nav-pills.' + navbarID + ' > li > a:hover,' +
                    '  .navbar-default.' + navbarID + ' .navbar-nav > li > a:active, .nav-pills.' + navbarID + '> li > a:active,' +
                    '  .navbar-default.' + navbarID + ' .navbar-nav > li > a:focus, .nav-pills.' + navbarID + ' > li > a:focus,' +
                    '  .nav-pills.' + navbarID + '>li.active>a, .nav-pills.' + navbarID + '>li.active>a:focus, .nav-pills.' + navbarID + '>li.active>a:hover {' +
                    '    background-color:' + settings.menu_active_bg_color + ';' +
                    '    color:' + settings.menu_active_color + ';' +
                    '  }' +
                    '  .navbar-default.' + navbarID + ' .navbar-nav > .active > a,' +
                    '  .navbar-default.' + navbarID + ' .navbar-nav > .active > a:hover,' +
                    '  .navbar-default.' + navbarID + ' .navbar-nav > .active > a:focus {' +
                    '    background-color:' + settings.menu_active_bg_color + ';' +
                    '    color:' + settings.menu_active_color + ';' +
                    '  }' +
                    '.navbar-default.' + navbarID + ' .navbar-brand:focus, .navbar-default.' + navbarID + ' .navbar-brand:hover {' +
                    '    color:' + settings.menu_active_color + ';' +
                    '    background-color: transparent;' +
                    '}' +
                    '</style>' +
                    '<nav class="widget-nav navbar navbar-default ' + navbarID + '" style="background-color:' + settings.menu_bg_color + ';">' +
                    '  <div class="container-fluid">' +
                    navbarHeader +
                    '    <div class="collapse navbar-collapse" id="' + navbarID + '">' +
                    '      <ul class="' + navbarClass + '">'; // Use id to make unique class names

                navbar += childNavBar;
                navbar += '</ul></div></div></nav>';
                $("#" + menuID).append(navbar);
                $("#" + menuID).css('height', '100%');
            }
        });
    };

    this.widgetTemplate = function(node, index) {
        var content = "";
        var multiLangSetting = node.multiLangSetting;
        var languageDescription = "";
        var id = '';

        if (!$.isEmptyObject(multiLangSetting.description)) {
            languageDescription = multiLangSetting.description;
        }

        if (node.type === FREE_DESCRIPTION_TYPE) {
            if (!$.isEmptyObject(languageDescription)) {
                content = languageDescription.description;
            }
        } else if (node.type === NOTICE_TYPE) {
            content = this.buildNoticeType(languageDescription, index);
        } else if (node.type === ACCESS_COUNTER) {
            var widgetId = 0;
            if (node.access_counter &&
                !Number.isNaN(Number(node.widget_id))) {
                widgetId = Number(node.widget_id);
            }
            content = this.buildAccessCounter(widgetId, node.created_date, languageDescription);
            setInterval(function() { this.setAccessCounterValue(); }, INTERVAL_TIME);
        } else if (node.type === NEW_ARRIVALS) {
            var innerID = 'new_arrivals' + '_' + index;
            id = 'id="' + innerID + '"';
            this.buildNewArrivals(node.widget_id, node.new_dates, node.rss_feed, innerID, node.display_result);
        } else if (node.type === MENU_TYPE) {
            var innerID = 'widget_pages_menu_' + node.widget_id + '_' + index; // Allow multiple menus
            id = 'id="' + innerID + '"';
            // Extract only the settings we want:
            var menuSettings = {};
            Object.keys(node).forEach(function(k) { if (k.startsWith('menu_')) menuSettings[k] = node[k] });
            this.buildMenu(node.id, node.widget_id, innerID, menuSettings);
        } else if (node.type === HEADER_TYPE) {
            $("#community_header").attr("hidden", true);
            if (!$.isEmptyObject(languageDescription)) {
                content = languageDescription.description;
            }
        } else if (node.type === FOOTER_TYPE) {
            $("#community_footer").attr("hidden", true);
            if (!$.isEmptyObject(languageDescription)) {
                content = languageDescription.description;
            }
        }

        var dataTheme = '';
        var widgetTheme = new WidgetTheme();
        if (node.theme) {
            if (node.theme === THEME_SIMPLE) {
                dataTheme = widgetTheme.TEMPLATE_SIMPLE;
            } else if (node.theme === THEME_SIDE_LINE) {
                dataTheme = widgetTheme.TEMPLATE_SIDE_LINE;
            } else {
                // Default
                dataTheme = widgetTheme.TEMPLATE_DEFAULT;
            }
        }
        var widget_data = {
            'header': multiLangSetting.label,
            'body': content
        };
        if (id !== '') {
            widget_data['id'] = id
        }
        return widgetTheme.buildTemplate(widget_data, node, dataTheme);
    };

    this.setAccessCounterValue = function() {
        // list access counter information: id, innit Number, created date
        var data = this.getAccessTopPageValue();
        var accessCounter = 0;
        $(".text-access-counter").each(function() {
            var widgetId = $(this).data("widgetId");
            var createdDate = $(this).data("createdDate");
            if (data && data[widgetId] && data[widgetId][createdDate]) {
                var widget = data[widgetId][createdDate];
                var result = widget.access_counter ? Number(widget.access_counter) : 0;
                accessCounter = result + (widget.all.count ? Number(widget.all.count) : 0);
            }
            $(this).text(accessCounter);
        });
    };

    this.getAccessTopPageValue = function() {
        var data = 0;
        var repository_id = $("#community-id").text();
        if (!repository_id) {
            repository_id = DEFAULT_REPOSITORY;
        }
        var current_language = $("#current_language").val();
        if (!current_language) {
            current_language = "en";
        }
        $.ajax({
            url: '/api/admin/access_counter_record/' + repository_id + '/' + current_language,
            method: 'GET',
            async: false,
            success: function(response) {
                data = response;
            }
        });
        return data;
    };
};

var WidgetTheme = function() {
    this.TEMPLATE_DEFAULT = {
        'border': {
            'border-radius': '5px !important',
            'border-style': 'outset'
        },
        'scroll-bar': ''
    };
    this.TEMPLATE_SIDE_LINE = {
        'border': {
            'border-radius': '0px !important',
            'border-style-left': 'groove',
            'border-right-style': 'none',
            'border-top-style': 'none',
            'border-bottom-style': 'none'
        },
        'scroll-bar': ''
    };
    this.TEMPLATE_SIMPLE = {
        'border': {
            'border-style': 'none',
            'border-radius': '0px !important'
        },
        'scroll-bar': ''
    };

    this.buildTemplate = function(widget_data, widget_settings, template) {
        if (!widget_data || !widget_settings) {
            return undefined;
        }
        var panel = $(".panel");
        panel.css('box-shadow', 'none');
        var id = (widget_data.id) ? widget_data.id : '';
        var labelTextColor = (widget_settings.label_text_color) ? widget_settings.label_text_color : '';
        var labelColor = (widget_settings.label_color) ? widget_settings.label_color : '';
        var borderColor = (widget_settings.frame_border_color) ? widget_settings.frame_border_color : '';
        var panelClasses = "panel-body no-padding-side ql-editor";
        var overFlowBody = "";
        if (template === this.TEMPLATE_SIDE_LINE) {
            template.border['border-left-style'] = (widget_settings.border_style) ? widget_settings.border_style : 'groove';
            if (widget_settings.border_style === BORDER_STYLE_DOUBLE) {
                delete template.border['border-style-left'];
                template.border['border-left'] = '3px double'; //3px is necessary to display double type
            }
        } else {
            template.border['border-style'] = (widget_settings.border_style) ? widget_settings.border_style : template.border['border-style'];
            if (widget_settings.border_style === BORDER_STYLE_DOUBLE) {
                delete template.border['border-style'];
                template.border['border'] = '3px double'; //3px is necessary to display double type
            }
        }
        var headerBorder = '';
        if (template === this.TEMPLATE_SIMPLE || template === this.TEMPLATE_SIDE_LINE) {
            headerBorder = 'border-top-right-radius: 0px; border-top-left-radius: 0px; ';
        } else {
            headerBorder = 'border-bottom:';
            if (widget_settings.border_style === BORDER_STYLE_DOUBLE) {
                headerBorder += ' 3px double ' + borderColor + ';'
            } else {
                headerBorder += ' 1px ' + widget_settings.border_style + ' ' + borderColor + ';'
            }
        }
        var header = (widget_settings.label_enable) ?
            '        <div class="panel-heading no-padding-side widget-header widget-header-position" style="' + headerBorder + this.buildCssText('color', labelTextColor) + this.buildCssText('background-color', labelColor) + '">' +
            '            <strong>' + widget_data.header + '</strong>' +
            '        </div>' : '';
        var headerClass = (widget_settings.label_enable) ? '' : 'no-pad-top-30';
        headerClass += (widget_settings.type === NEW_ARRIVALS || widget_settings.type === HEADER_TYPE || widget_settings.type === FOOTER_TYPE) ? ' no-before-content' : '';
        if (widget_settings.type === MENU_TYPE || widget_settings.type === ACCESS_COUNTER || widget_settings.type === HEADER_TYPE || widget_settings.type === FOOTER_TYPE) {
            overFlowBody = "overflow-y: hidden; overflow-x: hidden; ";
        }
        if (widget_settings.type === MENU_TYPE) {
            panelClasses = "panel-body";
        }
        var borderStyle = (template === this.TEMPLATE_SIMPLE) ? '' : this.buildBorderCss(template.border, borderColor);
        var backgroundColor = (widget_settings.background_color) ? widget_settings.background_color : '';

        var setClass = "grid-stack-item-content panel widget";
        if (widget_settings.type === HEADER_TYPE || widget_settings.type === FOOTER_TYPE) {
            setClass = "grid-stack-item-content panel header-footer-type";
        }
        var result = '<div class="grid-stack-item widget-resize">' +
            '    <div class="' + setClass + '" style="' + borderStyle + '">' +
            header +
            '        <div class="' + panelClasses + ' ' + headerClass + '" style="padding-top: 30px; bottom: 10px; overflow: auto; ' + this.buildCssText('background-color', backgroundColor) + ' ' + overFlowBody + '"' + id + '>' + widget_data.body +
            '        </div>' +
            '    </div>' +
            '</div>';
        return result;
    };

    this.buildCssText = function(keyword, data) {
        var cssStr = '';
        if (data === '') {
            return cssStr;
        }
        switch (keyword) {
            case 'color':
                cssStr = 'color: ' + data + '; ';
                break;
            case 'background-color':
                cssStr = 'background-color: ' + data + '; ';
                break;
            default:
                break;
        }
        return cssStr;
    };

    this.buildBorderCss = function(borderSettings, borderColor) {
        var borderStyle = '';
        for (var key in borderSettings) {
            if (key && borderSettings[key]) {
                borderStyle += key + ': ' + borderSettings[key] + '; ';
            }
        }
        borderStyle += 'border-color:' + borderColor + '; ';
        return borderStyle;
    }
};

function getWidgetDesignSetting() {
    var community_id = $("#community-id").text();
    var current_language = $("#current_language").val();
    var url;
    if (!community_id) {
        community_id = DEFAULT_REPOSITORY;
    }
    if (!current_language) {
        current_language = "en";
    }

    // If the current page is a widget page get
    var is_page = false;
    var request_param = {};
    var widgetPageId = $('#widget-page-id');
    if (widgetPageId.length) {
        var page_id = widgetPageId.text();
        url = '/api/admin/load_widget_design_page_setting/' + page_id + '/' + current_language;
        is_page = true;
        request_param = {
            type: 'GET',
            url: url
        }
    } else {
        var data = {
            repository_id: community_id
        };
        url = '/api/admin/load_widget_design_setting/' + current_language;
        request_param = {
            url: url,
            type: "POST",
            contentType: "application/json",
            headers: {
                "Content-Type": "application/json"
            },
            data: JSON.stringify(data)
        }
    }


    $.ajax({
        url: url,
        type: "POST",
        contentType: "application/json",
        headers: {
            "Content-Type": "application/json"
        },
        data: JSON.stringify(data),
        success: function(data) { // TODO: If no settings default to main layout
            if (data.error) {
                console.log(data.error);
                toggleWidgetUI();
                return;
            } else {
                var widgetList = data['widget-settings'];
                if (Array.isArray(widgetList) && widgetList.length) {
                    $("#page_body").removeClass("hidden");
                    $("#main_contents").addClass("grid-stack-item");
                    $("#header").css("height", "100px");
                    $("#footer").addClass("grid-stack-item no-scroll-bar");
                    var pageBodyGrid = new PageBodyGrid();
                    pageBodyGrid.init();
                    pageBodyGrid.loadGrid(widgetList);
                    new ResizeSensor($('.widget-resize'), function() {
                        $('.widget-resize').each(function() {
                            var headerElementHeight = $(this).find('.panel-heading').height();
                            $(this).find('.panel-body').css("padding-top", String(headerElementHeight + 11) + "px");
                            $(this).find('.panel-body').css("bottom", "10px");
                        });
                    });
                } else { // Pages are able to not have main content, so hide if widget is not present
                    if (is_page) {
                        $("#main_contents").hide();
                    }
                    if (community_id !== DEFAULT_REPOSITORY) {
                        $("#community_header").removeAttr("hidden");
                        $("footer > #community_footer").removeAttr("hidden");
                        $("#page_body").removeClass("hidden");
                    }
                }
            }
            toggleWidgetUI();
        }
    });
}

function toggleWidgetUI() {
    $("div#page_body").each(function() {
        $(this).css("display", "block");
    });
    $('footer#footer').css("display", "block");
    $('footer-fix#footer').remove();
}

function handleMoreNoT(moreDescriptionID, linkID, readMore, hideRest) {
    var moreDes = $("#" + moreDescriptionID);
    if (moreDes) {
        if (moreDes.is(":hidden")) {
            moreDes.show();
            $("#" + linkID).text(hideRest);
        } else {
            moreDes.hide();
            $("#" + linkID).text(readMore);
        }
    }
}

function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
