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
const DEFAULT_WIDGET_HEIGHT = 5;
const MAIN_CONTENTS = "main_contents";
const MIN_WIDTH = 768;

(function () {
    getWidgetDesignSetting();
    window.lodash = _.noConflict();
}());

let widgetList;
let mainContentSensor;
let headerSensor;
let otherSensor;
let widgetBodyGrid;
let widgetOtherList = {};
let isHeaderContent = false;
let isRegenerate = false;
let isClickMainContent = false;

const PageBodyGrid = function () {
    this.intervalId;
    this.init = function () {
        let options = {
            width: 12,
            verticalMargin: 4,
            cellHeight: 10,
            acceptWidgets: '.grid-stack-item'
        };
        let widget = $('#page_body');
        widget.gridstack(options);
        this.grid = widget.data('gridstack');
    };

    this.addNewWidget = function (node, index) {
        this.grid.addWidget($(this.widgetTemplate(node, index)), node.x, node.y, node.width, node.height);
        return false;
    }.bind(this);

    this.resizeWidget = function (widget, width, height) {
       this.grid.resize(widget, width, height);
    };

    this.getCellHeight = function () {
      return this.grid.cellHeight();
    };

    this.getVerticalMargin = function () {
      return this.grid.opts.verticalMargin;
    };

    this.updateMainContent = function (node) {
        let mainContents = $("#" + MAIN_CONTENTS);
        let titleMainContent = $("#title-main-content");
        let backgroundColorMainContent = $("#background-color-main-content");
        let indexBackground = $("#index-background");
        let panelDefault = $(".panel-default");
        let panelHeadingMainContents = $("#panel-heading-main-contents");
        let panel = $(".panel");

        let labelMainContent = node.multiLangSetting.label;
        let backgroundColor = node.background_color;
        let frameBorderColorMainContent = node.frame_border_color;
        let labelTextColor = node.label_text_color;
        let labelEnable = node.label_enable;

        titleMainContent.text(labelMainContent);
        titleMainContent.css("color", labelTextColor);
        backgroundColorMainContent.css("background-color", backgroundColor);
        indexBackground.css("background-color", backgroundColor);
        indexBackground.css("border-bottom-right-radius", "3px");
        indexBackground.css("border-bottom-left-radius", "3px");
        panelDefault.css("border-color", frameBorderColorMainContent);
        panelDefault.css("background-color", backgroundColor);
        panel.css("box-shadow", "none");

        $(".list-group-item").each(function () {
            if (!$(this).hasClass("style_li")) {
                $(this).css("background-color", backgroundColor);
            }
        });

        if (!labelEnable) {
            panelHeadingMainContents.css('display', 'none');
        }

        let style = this.addStyle(node);
        mainContents.append(style);
        this.buildMainContentTheme(node);
        this.grid.update(mainContents, node.x, node.y, node.width, node.height);
    };

    this.addStyle = function(node){
        let backgroundColor = node.background_color;
        let frameBorderColorMainContent = node.frame_border_color;
        let labelColor = node.label_color;
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
                    '.pagination > .active > a, .pagination > .active > span, .pagination > .active > a:hover,' +
                    '.pagination > .active > span:hover, .pagination > .active > a:focus, .pagination > .active > span:focus {' +
                        'background-color: #337ab7 !important;' +
                    '}' +
                '</style>';
    };

    this.buildMainContentTheme = function (node){
        let panelHeadingMainContents = $("#panel-heading-main-contents");
        let backgroundColorMainContent = $("#background-color-main-content");
        let panelMainContent = $("#panel-main-content");
        let borderStyle = node.border_style;
        let frameBorderColorMainContent = node.frame_border_color;
        let theme = node.theme;
        let borderRadius;
        let pxBorder;
        if (borderStyle === BORDER_STYLE_DOUBLE) {
            pxBorder = "3px ";
            borderRadius = "1px";
        }else if(borderStyle === BORDER_STYLE_NONE){
            pxBorder = "0px";
            borderRadius = "3px";
        }else {
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


    this.updateHeaderPage = function (node) {
      let headerElement = $("#header");
      let headerNav = $("#header_nav");
      let fixedHeader = $("#fixed_header");
      if (headerElement.length) {
        // Set Background color and text color for Fixed Header
        let fixedHeaderBackgroundColor = node.fixedHeaderBackgroundColor || "#ffffff";
        let fixedHeaderTextColor = node.fixedHeaderTextColor || "#808080";
        fixedHeader.css({"background-color": fixedHeaderBackgroundColor});
        $("#language-code-form  span").css({"color": fixedHeaderTextColor});
        $("#fixed_header a").css({"color": fixedHeaderTextColor});
        $("#lang-code").css({"color": fixedHeaderTextColor});

        // Update widget setting for Header Widget.
        let headerContent = $("#header_content");
        if (node.background_color) {
          headerNav.css({"background-color": node.background_color});
        }
        if (node.multiLangSetting && node.multiLangSetting.description) {
          isHeaderContent = true
          headerContent.html(node.multiLangSetting.description.description);
          headerContent.css({"width": "100%"})
        }
        this.grid.update(headerElement, node.x, node.y, node.width, node.height);
        headerElement.removeClass("hidden");
      }
    };

    this.loadGrid = function (widgetListItems) {
        let items = GridStackUI.Utils.sort(widgetListItems);
        let hasMainContent = false;
        items.forEach(function (node) {
            if (MAIN_CONTENT_TYPE === node.type) {
                this.updateMainContent(node);
                hasMainContent = true;
                return false;
            } else if (HEADER_TYPE === node.type) {
                let community_id = $("#community-id").text();
                if (!community_id){
                    this.updateHeaderPage(node);
                }
                return false;
            }
        }, this);

        ///Pages do not have to have main content, so hide if not in list
        if(!hasMainContent) {
            $("#" + MAIN_CONTENTS).hide();  // remove(); or empty() ?
        }
        for (let i = 0; i < items.length; i++) {
            let node = items[i];
            let community_id = $("#community-id").text();
            if (node.type === HEADER_TYPE && community_id) {
              this.addNewWidget(node, i);
            } else if ([MAIN_CONTENT_TYPE, HEADER_TYPE].indexOf(node.type) === -1) {
              this.addNewWidget(node, i);
            }
        }
        return false;
    }.bind(this);

    this.buildNoticeType = function (languageDescription, index) {
        let description = "";
        let moreDescriptionID = (NOTICE_TYPE + "_" + index).trim();
        let linkID = "writeMoreNotice_" + index;
        let moreDescription = "";
        let templateWriteMoreNotice = '<div id="' + moreDescriptionID + '" style="display: none;">' +
            moreDescription + '</div>';

        if (languageDescription.more_description) {
            moreDescription = languageDescription.more_description;
            let hideRest = (languageDescription.hide_the_rest) ? languageDescription.hide_the_rest : HIDE_REST_DEFAULT;
            let readMore = (languageDescription.read_more) ? languageDescription.read_more : READ_MORE_DEFAULT;
            templateWriteMoreNotice = '</br>' +
                '<div id="' + moreDescriptionID + '" class="hidden">' + moreDescription + '</div>' +
                '<a style="padding-bottom:35px;" id="' + linkID + '" class="writeMoreNoT" onclick="handleMoreNoT(\'' + moreDescriptionID + '\',\'' +
                linkID + '\',\'' + escapeHtml(readMore) + '\', \'' + escapeHtml(hideRest) + '\')">' + readMore +
                '</a>';
        }

        if (!$.isEmptyObject(languageDescription)) {
            description = languageDescription.description + templateWriteMoreNotice;
        }
        return description;
    };

    this.buildAccessCounter = function (widgetId, created_date, languageDescription) {
        let precedingMessage = languageDescription.preceding_message ? languageDescription.preceding_message + " " : "";
        let followingMessage = languageDescription.following_message ? " " + languageDescription.following_message : "";
        let otherMessage = languageDescription.other_message ? languageDescription.other_message : "";
        let countStartDate = languageDescription.count_start_date ? languageDescription.count_start_date : created_date;
        let data = this.getAccessTopPageValue();
        let result = 0;
        // Convert to display-able number
        if (data && data[widgetId] && data[widgetId][countStartDate]) {
          let widget = data[widgetId][countStartDate];
            let initNum = widget.access_counter ? Number(widget.access_counter) : 0;
            result = widget.all.count ? Number(widget.all.count) : 0;
            if (typeof(initNum) == 'number') {
                result = result + initNum;
            }
        }

        return '<div>'
                + ' <div class="counter-container">'
                +       precedingMessage
                + '<span data-widget-id="' + widgetId + '" data-created-date="' + created_date + '"data-count-start-date="'+ countStartDate
                + '" class = "text-access-counter">' + result + '</span>' + followingMessage
                + ' </div>'
                + ' <div>' + otherMessage + '</div>'
                + '</div>';
    };

    const currentTime = new Date().getTime();

    this.buildNewArrivals = function (widgetID, term, rss, id, count) {
        $.ajax({
            method: 'GET',
            url: '/api/admin/get_new_arrivals/' + widgetID ,
            contentType: 'application/json',
            success: function(response) {
                var result = response.data;
                var rssHtml = '';
                if (term == 'Today') {
                    term = 0;
                }
                if (rss) {
                    let rssURL = "/rss/records?term=" + term + "&count=" + count;
                    rssHtml = '<a class="" target="_blank" rel="noopener noreferrer" href="' + rssURL + '"><i class="fa fa-rss"></i></a>';
                }
                let innerHTML = '<div class= "rss text-right">' + rssHtml + '</div>'
                    + '<div>';
                for (let data in result) {
                    innerHTML += '<div class="no-li-style no-padding-col"><li><a class="a-new-arrivals arrival-scale" href="' + result[data].url + '">' + result[data].name + '</a></li></div>';
                }
                innerHTML += '</div>';
                $("#" + id).append(innerHTML);
            }
        });
    };

    this.buildMenu = function (repoID, widgetID, menuID, settings) {
        let current_language = $("#current_language").val() || 'en';
        $.ajax({
            method: 'GET',
            url: '/api/admin/get_page_endpoints/' + widgetID + '/' + current_language,
            headers: {
                'Content-Type': 'application/json'
            },
            success: function(response) {
                var endpoints = response.endpoints;
                var repoHomeURL = (repoID === DEFAULT_REPOSITORY) ? '/' : ('/' + '?c=' + repoID);
                var navbarID = 'widgetNav_' + widgetID; // Re-use to build unique class ids
                var navbarClass = settings.menu_orientation === 'vertical' ?
                    'nav nav-pills nav-stacked pull-left ' + navbarID : 'nav navbar-nav';
                let mainLayoutTitle = "";
                let childNavBar = "";
                let navbarHeader = "";
                for (let i in endpoints) {  // Create links
                  let liClass = '';
                  let communityArgs = (repoID === DEFAULT_REPOSITORY) ? '' : '?c=' + repoID;
                  let communityPath = (repoID === DEFAULT_REPOSITORY) ? '' : '/c/' + repoID + '/page';
                  let title = endpoints[i].title;
                  let endpointsURL = endpoints[i].url;
                  if (endpoints[i].is_main_layout) {
                    mainLayoutTitle = title;
                  } else {
                    if (window.location.pathname === endpointsURL) {
                      liClass = 'class="active"';
                    }
                    if (endpointsURL.charAt(0) === '/'){
                      if (communityPath === '') {
                        childNavBar += '<li ' + liClass + '><a href="' + endpointsURL + communityArgs + '">' + title + '</a></li>';
                      } else {
                        let provisionalURL = endpointsURL.replace(communityPath, '')
                        if (provisionalURL.charAt(0) === '/'){
                          childNavBar += '<li ' + liClass + '><a href="' + endpointsURL + communityArgs + '">' + title + '</a></li>';
                        } else {
                          childNavBar += '<li ' + liClass + '><a href="' + provisionalURL + '">' + title + '</a></li>';
                        }
                      }
                    } else {
                      childNavBar += '<li ' + liClass + '><a href="' + endpointsURL + '">' + title + '</a></li>';
                    }
                  }
                }

                if (mainLayoutTitle === "" && Array.isArray(settings.menu_show_pages) && settings.menu_show_pages.indexOf("0") > -1) {
                    mainLayoutTitle = "Main Layout";
                }

                if (mainLayoutTitle) {
                  let mainLayoutActive = "";
                  let currentMainLayout = window.location.pathname + window.location.search;
                  let repoHomeURL2 = "/communities/" + repoID + "/?view=weko";
                  if (currentMainLayout === repoHomeURL || currentMainLayout === repoHomeURL2) {
                      mainLayoutActive = 'active';
                  }
                  navbarHeader =
                    '<div class="navbar-header">' +
                    '  <a class="navbar-brand '+ mainLayoutActive +'" href="' + repoHomeURL + '">' + mainLayoutTitle + '</a>' +
                    '</div>';
                }

                let navbar =
                '<style>' +  // Renaming classes allows for multiple menus on page
                '.navbar-default.' + navbarID + ' .navbar-brand {' +
                '    color:' + settings.menu_default_color + ';' +
                '}' +
                '.navbar-default.' + navbarID + ' .navbar-header > a:hover, .navbar-default.' + navbarID + ' .navbar-header > a.active {' +
                '    background-color:' + settings.menu_active_bg_color + ';' +
                '    color:' +  settings.menu_active_color + ';' +
                '}' +
                '  .navbar-default.' + navbarID + ' .navbar-nav > li > a, .nav-pills > li > a {' +
                '    color:' +  settings.menu_default_color + ';' +
                '  }' +
                '  .navbar-default.' + navbarID + ' .navbar-nav > li > a:hover, .nav-pills.' + navbarID + ' > li > a:hover,' +
                '  .navbar-default.' + navbarID + ' .navbar-nav > li > a:active, .nav-pills.' + navbarID + '> li > a:active,' +
                '  .navbar-default.' + navbarID + ' .navbar-nav > li > a:focus, .nav-pills.' + navbarID + ' > li > a:focus,' +
                '  .nav-pills.' + navbarID + '>li.active>a, .nav-pills.' + navbarID + '>li.active>a:focus, .nav-pills.'+ navbarID + '>li.active>a:hover {' +
                '    background-color:' + settings.menu_active_bg_color + ';' +
                '    color:' +  settings.menu_active_color + ';' +
                '  }' +
                '  .navbar-default.' + navbarID + ' .navbar-nav > .active > a,' +
                '  .navbar-default.' + navbarID + ' .navbar-nav > .active > a:hover,' +
                '  .navbar-default.' + navbarID + ' .navbar-nav > .active > a:focus {' +
                '    background-color:' + settings.menu_active_bg_color + ';' +
                '    color:' +  settings.menu_active_color + ';' +
                '  }' +
                '.navbar-default.' + navbarID + ' .navbar-brand:focus, .navbar-default.' + navbarID + ' .navbar-brand:hover {' +
                '    color:' + settings.menu_active_color + ';' +
                '    background-color: transparent;' +
                '}' +
                '</style>' +
                '<nav class="widget-nav navbar navbar-default ' + navbarID + '" style="border:0;background-color:' + settings.menu_bg_color + ';">' +
                '  <div class="container-fluid container-fluid2">' +
                    navbarHeader +
                '    <div class="collapse navbar-collapse in" aria-expanded="true" id="' + navbarID + '">' +
                '      <ul class="' + navbarClass + '">';  // Use id to make unique class names

                navbar += childNavBar;
                navbar +='</ul></div></div></nav>';
                $("#" + menuID).append(navbar);
                $("#" + menuID).css('height', '100%');
            }
        });
    };

    this.widgetTemplate = function (node, index) {
      let loginElement = "";
      let content = "";
        let multiLangSetting = node.multiLangSetting;
        let languageDescription = "";
        let id = 'id="widget_body_' + index + '"';

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
            let widgetId = 0;
            if (node.access_counter &&
                typeof(node.widget_id) == 'number') {
                widgetId = node.widget_id;
            }
            content = this.buildAccessCounter(widgetId, node.created_date, languageDescription);
            let _this = this
            if (!this.intervalId) {
                this.intervalId = setInterval(function() {
                    return _this.setAccessCounterValue(widgetId);
                }, INTERVAL_TIME);
            }
        } else if (node.type === NEW_ARRIVALS) {
            let innerID = 'new_arrivals' + '_' + index;
            id = 'id="' + innerID + '"';
            this.buildNewArrivals(node.widget_id, node.new_dates, node.rss_feed, innerID, node.display_result);
        } else if (node.type === MENU_TYPE) {
          let innerID = 'widget_pages_menu_' + node.widget_id + '_' + index;  // Allow multiple menus
          id = 'id="' + innerID + '"';
          // Extract only the settings we want:
          var menuSettings = {};
          Object.keys(node).forEach(function(k) { if (k.indexOf('menu_') == 0) menuSettings[k] = node[k] });
          this.buildMenu(node.id, node.widget_id, innerID, menuSettings);
        } else if (node.type === HEADER_TYPE) {
            $("#community_header").attr("hidden", true);
            let content_area = document.querySelector('.navbar-right');
            if (content_area !== null) {
              loginElement = content_area.cloneNode(true);
            }
            if (!$.isEmptyObject(languageDescription)) {
                content = languageDescription.description;
            }
        } else if (node.type === FOOTER_TYPE) {
            $("#community_footer").attr("hidden", true);
            if (!$.isEmptyObject(languageDescription)) {
                content = languageDescription.description;
            }
        }

        let dataTheme = '';
        let widgetTheme = new WidgetTheme();
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
        let widget_data = {
            'header': multiLangSetting.label,
            'body': content,
            'id': id
        };
        return widgetTheme.buildTemplate(widget_data, node, dataTheme, loginElement);
    };

    this.setAccessCounterValue = function () {
        // list access counter information: id, innit Number, created date
        let data = this.getAccessTopPageValue();
        let accessCounter = 0;
        $(".text-access-counter").each(function () {
            let widgetId = $(this).data("widgetId");
            let countStartDate = $(this).data("countStartDate") ? $(this).data("countStartDate") : $(this).data("createdDate");
            if (data && data[widgetId] && data[widgetId][countStartDate]) {
                var widget = data[widgetId][countStartDate];
                let result = widget.access_counter ? Number(widget.access_counter) : 0;
                accessCounter = result + (widget.all.count ? Number(widget.all.count) : 0);
            }
            $(this).text(accessCounter);
        });
    };

    this.getAccessTopPageValue = function () {
        let data = 0;
        let repository_id = $("#community-id").text();
        if (!repository_id) {
            repository_id = DEFAULT_REPOSITORY;
        }
        let current_language = $("#current_language").val();
        if (!current_language) {
            current_language = "en";
        }
        var currentTime = new Date().getTime();
        var current_path=location.pathname
        var path_parts = current_path.split('/').filter(Boolean)
        var url = (
          current_path === "/" || 
          current_path.startsWith("/c/") && path_parts.length === 2
        ) ? "/main" : current_path;
        var _this = this
        $.ajax({
            url: '/api/admin/access_counter_record/' + 
              repository_id + url + '/' + current_language,
            method: 'GET',
            async: false,
            success: function(response) {
                data = response;
            },
            error: function() {
                clearInterval(_this.intervalId);
            }
        });
        return data;
    };
};

let WidgetTheme = function () {
    this.TEMPLATE_DEFAULT = {
        'border': {
            'border-radius': '0px !important',
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

    this.buildTemplate = function (widget_data, widget_settings, template, element) {
        if (!widget_data || !widget_settings) {
            return undefined;
        }
        let panel = $(".panel");
        panel.css('box-shadow', 'none');
        let id = (widget_data.id) ? widget_data.id : '';
        let labelTextColor = (widget_settings.label_text_color) ? widget_settings.label_text_color : '';
        let labelColor = (widget_settings.label_color) ? widget_settings.label_color : '';
        let borderColor = (widget_settings.frame_border_color) ? widget_settings.frame_border_color : '';
        let panelClasses = "panel-body no-padding-side trumbowyg-editor";
        let overFlowX = "";
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
        let headerBorder;
        if (template === this.TEMPLATE_SIMPLE || template === this.TEMPLATE_SIDE_LINE) {
            headerBorder = 'border-top-right-radius: 0px; border-top-left-radius: 0px; ';
        }else {
            headerBorder = 'border-bottom:';
            if (widget_settings.border_style === BORDER_STYLE_DOUBLE) {
                headerBorder += ' 3px double ' + borderColor + ';'
            }else {
                headerBorder += ' 1px ' + widget_settings.border_style + ' ' + borderColor + ';'
            }
        }
        let header = (widget_settings.label_enable) ?
            '        <div class="panel-heading no-padding-side widget-header widget-header-position" ' +
                            'style="' + headerBorder + this.buildCssText('color', labelTextColor)
                            + this.buildCssText('background-color', labelColor) + '">' +
            '            <strong>' + widget_data.header + '</strong>' +
            '        </div>' : '';
        let headerClass = (widget_settings.label_enable) ? '' : 'no-pad-top-30';
        headerClass += ([NEW_ARRIVALS, HEADER_TYPE, FOOTER_TYPE].indexOf(widget_settings.type) > -1) ? ' no-before-content' : '';
        if ([MENU_TYPE, ACCESS_COUNTER, HEADER_TYPE, FOOTER_TYPE].indexOf(widget_settings.type) > -1) {
            overFlowX = "overflow-x: hidden;";
        }
        if (widget_settings.type === MENU_TYPE) {
            panelClasses = "panel-body";
        }
        let borderStyle = (template === this.TEMPLATE_SIMPLE) ? '' : this.buildBorderCss(template.border, borderColor);
        let backgroundColor = (widget_settings.background_color) ? widget_settings.background_color : '';

        let setClass = "grid-stack-item-content panel widget";
        if(widget_settings.type === HEADER_TYPE || widget_settings.type === FOOTER_TYPE){
            setClass = "grid-stack-item-content panel header-footer-type";
        }
        let overflowY = "overflow-y: hidden !important;";
        let noAutoHeight = "";
        if (!this.validateWidgetHeight(widget_settings.type, widget_data.body)) {
            noAutoHeight = "no-auto-height";
            overflowY = "";
        }
        if ( element == "") {
          return '<div class="grid-stack-item widget-resize">' +
          '    <div class="' + setClass + '" style="' + borderStyle + '">' +
          header +
          '        <div class="' + panelClasses + ' ' + headerClass + ' ' + noAutoHeight + ' " style="padding-top: 0px; padding-bottom: 0!important;'
          + overflowY + overFlowX + this.buildCssText('background-color', backgroundColor) + ' "' + id + '>'
          + widget_data.body +
          '        </div>' +
          '    </div>'+
          '</div>';
        } else {
          return '<div class="grid-stack-item widget-resize over">' +
              '    <div class="' + setClass + '" style="' + borderStyle + '">' +
              header +
              '        <div class="' + panelClasses + ' ' + headerClass + ' ' + noAutoHeight + ' " style="padding-top: 0px; padding-bottom: 0!important;'
              + overflowY + overFlowX + this.buildCssText('background-color', backgroundColor) + ' "' + id + '>'
              + widget_data.body +
              '        </div>' +
              '    </div>' + element.outerHTML +
              '</div>' +
              '<style>' +
              '.over{overflow: visible !important;}' +
              '.grid-stack-item-content.panel.header-footer-type{ z-index: -1 !important }' +
              '.navbar-right{ margin-right: 15px; }' +
              '</style>';
        }
      };

  this.validateWidgetHeight = function (widgetType, widgetData) {
    if ([FREE_DESCRIPTION_TYPE, NOTICE_TYPE, HEADER_TYPE, FOOTER_TYPE].indexOf(widgetType) > -1) {
      let heightPattern = /height *: *(9[1-9]|\d{3,}) *%/;
      let searchCSSInlinePattern = new RegExp(/style=((?!<).)*/.source
        + heightPattern.source
        + /((?!<).)*?>/.source);
      let searchCSSClassPattern = new RegExp(/{(.|\n)*/.source
        + heightPattern.source
        + /(.|\n)*}/.source);
      return (widgetData.search(searchCSSInlinePattern) < 0 && widgetData.search(searchCSSClassPattern) < 0);
    }
    return true;
  };

    this.buildCssText = function (keyword, data) {
        let cssStr = '';
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

    this.buildBorderCss = function (borderSettings, borderColor) {
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

/**
 * Get new widget height
 * @param pageBodyGrid
 * @param scrollHeight
 * @returns {number}
 */
function getNewWidgetHeight(pageBodyGrid, scrollHeight) {
  let cellHeight = pageBodyGrid.getCellHeight();
  let verticalMargin = pageBodyGrid.getVerticalMargin();
  return Math.ceil(
    (scrollHeight + verticalMargin) / (cellHeight + verticalMargin)
  );
}

/**
 * Resize widget to default height
 */
function resizeWidgetToDefaultHeight() {
  // Other widget
  Object.keys(widgetOtherList).forEach(function (key) {
    let widget = widgetOtherList[key]['widget'];
    widget.data("isResize", true);
  });
  // Header widget
  $('#header').data("isResize", true);
  // Main Content widget
  $("#" + MAIN_CONTENTS).data("isResize", true);
}

/**
 * Auto adjust widget height.
 * @param widgetElement: widget element (Main Content widget or Header widget)
 * @param pageBodyGrid: Widget body object.
 * @param otherElement: Other widget element.
 */
function autoAdjustWidgetHeight(widgetElement, pageBodyGrid, otherElement) {
  if (otherElement) {
    let isResize = otherElement.data("isResize");
    if (isResize) {
      let parent = otherElement.closest(".grid-stack-item");
      let width = parent.data("gsWidth");
      pageBodyGrid.resizeWidget(parent, width, DEFAULT_WIDGET_HEIGHT);
      otherElement.data("isResize", false);
      otherElement.data("isUpdated", true);
    }
    let scrollHeight = otherElement.prop("scrollHeight");
    let clientHeight = otherElement.prop("clientHeight");
    if (scrollHeight > clientHeight) {
      let parent = otherElement.closest(".grid-stack-item");
      let width = parent.data("gsWidth");
      let isUpdated = otherElement.data("isUpdated");
      let newHeight, widgetHeight;
      widgetHeight = newHeight = getNewWidgetHeight(pageBodyGrid, scrollHeight);
      // In the case of IE 11, increase the widget height by three unit.
      if (isIE11()) {
        widgetHeight = widgetHeight + 3;
      }
      // Check whether the widget has been rendered for the first time
      if (isUpdated) {
        let cellHeight = pageBodyGrid.getCellHeight();
        let verticalMargin = pageBodyGrid.getVerticalMargin();
        let currentClientHeight = newHeight * (cellHeight + verticalMargin);
        if (currentClientHeight > scrollHeight) {
          let height = DEFAULT_WIDGET_HEIGHT > widgetHeight - 1 ? DEFAULT_WIDGET_HEIGHT : widgetHeight - 1;
          pageBodyGrid.resizeWidget(parent, width, height);
          //pageBodyGrid.resizeWidget(parent, width, height);
          console.log("currentClientHeight: "+ currentClientHeight);
          console.log("scrollHeight: "+ scrollHeight);


        } else {
          let height = DEFAULT_WIDGET_HEIGHT > widgetHeight ? DEFAULT_WIDGET_HEIGHT : widgetHeight;
          pageBodyGrid.resizeWidget(parent, width, height);
        }

      } else {
        pageBodyGrid.resizeWidget(parent, width, newHeight - 10);

        otherElement.data("isUpdated", true);
      }
      let widgetId = otherElement.attr('id');
      widgetOtherList[widgetId] = {
        'parent': parent,
        'widget': otherElement
      }
    }
  } else {
    let width = widgetElement.data("gsWidth");
    let isResize = widgetElement.data("isResize");
    if (isResize) {
      pageBodyGrid.resizeWidget(widgetElement, width, DEFAULT_WIDGET_HEIGHT);
      widgetElement.data("isResize", false);
    }
    let scrollHeight = widgetElement.prop("scrollHeight");
    let clientHeight = widgetElement.prop("clientHeight");
    let currentHeight = widgetElement.data("gsHeight");
    if (scrollHeight > clientHeight) {
      let newHeight = getNewWidgetHeight(pageBodyGrid, scrollHeight);
      if (newHeight > currentHeight) {
        pageBodyGrid.resizeWidget(widgetElement, width, newHeight);
      } else if (newHeight === currentHeight) {
        pageBodyGrid.resizeWidget(widgetElement, width, newHeight + 1);
      } else {
        pageBodyGrid.resizeWidget(widgetElement, width, newHeight);
      }
    }
  }
}

/**
 * Get Widget design setting.
 */
function getWidgetDesignSetting() {
    let community_id = $("#community-id").text();
    let current_language = $("#current_language").val();
    let url;
    if (!community_id) {
        community_id = DEFAULT_REPOSITORY;
    }
    if (!current_language) {
        current_language = "en";
    }

    // If the current page is a widget page get
    let is_page = false;
    let widgetPageId = $('#widget-page-id');
    let currentTime = new Date().getTime();
    let request;
    if (widgetPageId.length) {
        let page_id = widgetPageId.text();
        url = '/api/admin/load_widget_design_page_setting/' + page_id + '/' + current_language;
        is_page = true;
        request = $.ajax({
            url: url,
            type: "GET",
            contentType: "application/json",
            headers: {
                "Content-Type": "application/json"
            }
        });
    }
    else {
        let data = {
            repository_id: community_id
        };
        url = '/api/admin/load_widget_design_setting/' + current_language ;
        request = $.ajax({
            url: url,
            type: "POST",
            contentType: "application/json",
            headers: {
                "Content-Type": "application/json"
            },
            data: JSON.stringify(data)
        });
    }
    // Display page loading.
    $(".lds-ring-background").removeClass("hidden");

  request
    .done(function(data) {
      if (data.error) {
        console.log(data.error);
        toggleWidgetUI();
        return;
      } else {
        widgetList = data["widget-settings"];
        if (Array.isArray(widgetList) && widgetList.length) {
          $("#page_body").removeClass("hidden");
          $("#" + MAIN_CONTENTS).addClass("grid-stack-item");
          $("#header").addClass("grid-stack-item no-scroll-bar");
          $("#footer").addClass("grid-stack-item no-scroll-bar");

          // Check browser/tab is active
          if (!document.hidden) {
            buildWidget();
          } else {
            // In case browser/tab is inactive,
            // create an event build widget when browser/tab active
            window.addEventListener("focus", buildWidget);
          }
        } else {
          // Pages are able to not have main content, so hide if widget is not present
          if (is_page) {
            $("#" + MAIN_CONTENTS).hide();
          }
          if (community_id !== DEFAULT_REPOSITORY) {
            $("#community_header").removeAttr("hidden");
            $("footer > #community_footer").removeAttr("hidden");
            $("#page_body").removeClass("hidden");
          }
        }
      }
      if (!document.hidden) {
        toggleWidgetUI();
      } else {
        window.addEventListener("focus", toggleWidgetUI);
      }
    })
    .fail(function() {
      console.log(data.error);
      toggleWidgetUI();
    });
}

/**
 * Build widget
 */
function buildWidget() {
  if (Array.isArray(widgetList) && widgetList.length) {
    widgetBodyGrid = new PageBodyGrid();
    widgetBodyGrid.init();
    widgetBodyGrid.loadGrid(widgetList);
    // Adjust widget height.
    handleAutoAdjustWidget(widgetBodyGrid);
    // Remove event listener build widget.
    window.removeEventListener('focus', buildWidget);
    // In case the browser is resized,
    // The height of the widgets are set to default.
    window.addEventListener('resize', function () {
      fixBrowserResize();
      resizeWidgetToDefaultHeight();
    });
    // Resize Image.
    setTimeout(resizeImage, 0);
    // Resize Widget Name.
    new ResizeSensor($('.widget-resize'), function () {
      $('.widget-resize').each(function () {
        let headerElementHeight = $(this).find('.panel-heading').height();
        if (headerElementHeight) {
          $(this).find('.panel-body').css("padding-top", String(headerElementHeight + 11) + "px");
        }
      });
    });
  }
}

function resizeImage() {
  $('.trumbowyg-editor img').each(function () {
    let notAutoHeight = $(this).closest(".no-auto-height");
    if (!notAutoHeight.length && $(this).attr('src')) {
      let currentWidget = $(this).closest(".grid-stack-item");
      let currentTrumbowyg = $(this).closest(".trumbowyg-editor");
      let currentHeight = currentWidget.data("gsHeight");
      let currentWidth = currentWidget.data("gsWidth");
      let img = new Image();
      img.src = $(this).attr('src');
      img.onload = function () {
        let childElement = currentTrumbowyg.children();
        let widgetHeight = 0;
        for (let i = 0; i < childElement.length; i++) {
          let element = $(childElement[i]);
          if (!element.hasClass("resize-sensor") && element.height()) {
            widgetHeight += element.height();
          }
        }
        let newHeight = getNewWidgetHeight(widgetBodyGrid, widgetHeight);
        if (newHeight > currentHeight) {
          widgetBodyGrid.resizeWidget(currentWidget, currentWidth, newHeight);
        } else if (newHeight === currentHeight) {
          widgetBodyGrid.resizeWidget(currentWidget, currentWidth, newHeight + 1);
        }else{
          widgetBodyGrid.resizeWidget(currentWidget, currentWidth, newHeight);
        }
      }
    }
  });
}

/**
 * Remove resize sensor
 * @param sensor
 */
function removeSensor(sensor) {
  if (sensor !== 'undefined') {
    sensor.detach();
  }
}

/**
 * Fix bug layout when the browser is resized.
 */
function fixBrowserResize() {
  isClickMainContent = false;
  if (window.innerWidth < MIN_WIDTH) {
    if (isFireFox() && !isRegenerate) {
      isRegenerate = true;
      // Remove resize sensor.
      removeSensor(otherSensor);
      removeSensor(headerSensor);
      removeSensor(mainContentSensor);
      // Add  resize sensor.
      handleAutoAdjustWidget(widgetBodyGrid);
    }
  } else {
    isRegenerate = false;
  }

}

/**
 * Check if the current browser is Firefox.
 * @returns {boolean}
 */
function isFireFox() {
  return navigator.userAgent.toLowerCase().indexOf('firefox') > -1;
}

/**
 * Check if the current page is a registration workflow
 * @returns {boolean}
 */
function isItemRegistrationWorkFlow() {
  return $("#item_registration_workflow").length > 0;
}

/**
 * Check if the current browser is IE11
 * @returns {boolean}
 */
function isIE11() {
  return !!window.MSInputMethodContext && !!document.documentMode;
}

/**
 * Fix widget layout on IE 11
 */
function fixWidgetIE11() {
  $(".header-footer-type").parent().removeClass("widgetIE");
  setTimeout(function () {
    if (isIE11()) {
      // Add class fix css IE11
      $("#page_body").addClass("ie");
      // scroll-x when content > div
      $(".trumbowyg-editor").each(function () {
        if ($(this).find("img").length !== 0) {
          $(this).addClass("scroll_x");
        }
      });
    }
  }, 1000)
}

/**
 * Handle auto adjust the height of widget
 * @param pageBodyGrid Widget body object.
 */
function handleAutoAdjustWidget(pageBodyGrid) {
  if (isIE11()){
    $('.header-footer-type').parent().addClass('widgetIE');
  }

  // Auto adjust Other widget
  otherSensor = new ResizeSensor($('.grid-stack-item-content .panel-body'), function () {
    $('.grid-stack-item-content .panel-body').each(function () {
      let _this = $(this);
      if (!_this.hasClass("no-auto-height")) {
        autoAdjustWidgetHeight(null, pageBodyGrid, _this);
      }
    });
  });

  // Auto adjust Header widget
  headerSensor = new ResizeSensor($('#header_content'), function () {
    let headerContent = $('#header_content').closest(".grid-stack-item");
    autoAdjustWidgetHeight(headerContent, pageBodyGrid);
  });

  // Auto adjust Main Content widget
  createMainContentSensor()

  // Fix widget display on IE 11
  fixWidgetIE11();
}

/**
 * Create Main content sensor.
 */
function createMainContentSensor() {
  mainContentSensor = new ResizeSensor($('#' + MAIN_CONTENTS), function () {
    let mainContent = $('#' + MAIN_CONTENTS);
    $("#weko-records").click(function () {
      isClickMainContent = true;
    });
    if (!(isClickMainContent && isItemRegistrationWorkFlow())) {
      autoAdjustWidgetHeight(mainContent, widgetBodyGrid);
    }
  });
}

function toggleWidgetUI() {
    $("div#page_body").each(function () {
        $(this).css("display", "block");
    });
    $('footer#footer').css("display", "block");
    $('footer-fix#footer').remove();
    setTimeout(function () {
      // Remove page loading.
      $(".lds-ring-background").addClass("hidden");
    }, 500);
    window.removeEventListener("focus", toggleWidgetUI);
}

function handleMoreNoT(moreDescriptionID, linkID, readMore, hideRest) {
  let moreDes = $("#" + moreDescriptionID);
  let textLink = $("#" + linkID);
  if (moreDes) {
    let parentElement = moreDes.parent();
    if (moreDes.hasClass("hidden")) {
      moreDes.removeClass("hidden");
      textLink.text(hideRest);
      parentElement.removeClass('without-after-element');
    } else {
      moreDes.addClass("hidden");
      parentElement.addClass('without-after-element');
      textLink.text(readMore);
    }
    parentElement.data("isResize", true);
    autoAdjustWidgetHeight(null, widgetBodyGrid, parentElement);
  }
}

/**
 * Escape HTML
 * @param unsafe
 * @returns {*}
 */
function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
 }
