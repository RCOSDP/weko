const MAIN_CONTENT_TYPE = "Main contents";
const FREE_DESCRIPTION_TYPE = "Free description";
const NOTICE_TYPE = "Notice";
const HIDE_REST_DEFAULT = "Hide the rest";
const READ_MORE_DEFAULT = "Read more";
const NEW_ARRIVALS = "New arrivals";
const ACCESS_COUNTER = "Access counter";
const INTERVAL_TIME = 60000; //one minute

(function () {
    getWidgetDesignSetting();
    window.lodash = _.noConflict();
}());

let PageBodyGrid = function () {
    this.init = function () {
        let options = {
            width: 12,
            float: true,
            verticalMargin: 4,
            cellHeight: 100,
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

    this.updateMainContent = function (node) {
        let mainContents = $("#main_contents");
        this.grid.update(mainContents, node.x, node.y, node.width, node.height);
    };

    this.loadGrid = function (widgetListItems) {
        let items = GridStackUI.Utils.sort(widgetListItems);
        items.forEach(function (node) {
            if (MAIN_CONTENT_TYPE == node.type) {
                this.updateMainContent(node);
                return false;
            }
        }, this);

        for (var i = 0; i < items.length; i++) {
            let node = items[i];
            if (MAIN_CONTENT_TYPE != node.type) {
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
                '<div id="' + moreDescriptionID + '" style="display: none;">' + moreDescription + '</div>' +
                '<a id="' + linkID + '" class="writeMoreNoT" onclick="handleMoreNoT(\'' + moreDescriptionID + '\',\'' +
                linkID + '\',\'' + readMore + '\', \'' + hideRest + '\')">' + readMore +
                '</a>';
        }

        if (!$.isEmptyObject(languageDescription)) {
            description = languageDescription.description + templateWriteMoreNotice;
        }
        return description;
    };

    this.buildAccessCounter = function (initNumber, languageDescription) {
        let data = this.getAccessTopPageValue();
        // Convert to display-able number
        let initNum = Number(initNumber);
        let result = Number(data);
        if (!Number.isNaN(initNum)) {
            result = result + initNumber;
        }

        let precedingMessage = languageDescription.preceding_message ? languageDescription.preceding_message + "&nbsp;" : "";
        let followingMessage = languageDescription.following_message ? "&nbsp;" + languageDescription.following_message : "";
        let otherMessage = languageDescription.other_message ? languageDescription.other_message : "";

        return '<div>'
                + ' <div class="counter-container">'
                +       precedingMessage + '<span data-init-number="' + initNumber + '" class = "text-access-counter">' + result + '</span>' + followingMessage
                + ' </div>'
                + ' <div>' + otherMessage + '</div>'
                + '</div>';
    };

    this.buildNewArrivals = function (widgetID, term, rss, id, count) {
        $.ajax({
            method: 'GET',
            url: '/api/admin/get_new_arrivals/' + widgetID,
            headers: {
                'Content-Type': 'application/json'
            },
            success: (response) => {
                let result = response.data;
                let rssHtml = '';
                if (term == 'Today') {
                    term = 0;
                }
                if (rss) {
                    let rssURL = "/rss/records?term=" + term + "&count=" + count;
                    rssHtml = '<a class="" target="_blank" rel="noopener noreferrer" href="' + rssURL + '"><i class="fa fa-rss"></i></a>';
                }
                let innerHTML = '<div class= "rss text-right">' + rssHtml + '</div>'
                                +'<div>';
                for (let data in result) {
                    innerHTML += '<div class="no-li-style no-padding-col"><li><a class="a-new-arrivals arrival-scale" href="' + result[data].url + '">' + result[data].name + '</a></li></div>';
                }
                innerHTML +='</div>';
                $("#" + id).append(innerHTML);
            }
        });
    };

    this.widgetTemplate = function (node, index) {
        let content = "";
        let multiLangSetting = node.multiLangSetting;
        let languageDescription = "";
        // Handle css style
        if (node.background_color) {
            backgroundColor = "background-color: " + node.background_color + "; ";
        }

        if(node.frame_border && node.frame_border_color) {
            frameBorderColor = "border-color: " + node.frame_border_color + "; ";
        }

        if (node.label_color) {
            labelColor = "color: " + node.label_color + "; ";
        }

        if (!$.isEmptyObject(multiLangSetting.description)) {
            languageDescription = multiLangSetting.description;
        }

        if (node.type == FREE_DESCRIPTION_TYPE) {
            if (!$.isEmptyObject(languageDescription)){
                content = languageDescription.description;
            }
        } else if (node.type == NOTICE_TYPE) {
            content = this.buildNoticeType(languageDescription, index);
        } else if (node.type == ACCESS_COUNTER) {
            let initNumber = 0;
            if (node.access_counter &&
                !Number.isNaN(Number(node.access_counter))) {
                initNumber = Number(node.access_counter);
            }
            content = this.buildAccessCounter(initNumber, languageDescription);
            rightStyle = "right: unset; ";
            paddingHeading = "";
            overFlowBody = "overflow-y: hidden; ";
            setInterval(() => { this.setAccessCounterValue(); }, INTERVAL_TIME);
        } else if (node.type == NEW_ARRIVALS) {
            let innerID = 'new_arrivals' + '_' + index;
            id = 'id="' + innerID + '"';

            this.buildNewArrivals(node.widget_id, node.new_dates, node.rss_feed, innerID, node.display_result);
        }

        let widgetTheme = new WidgetTheme();
        let widget_data = {
            'header': multiLangSetting.label,
            'body': content
        }
        return widgetTheme.buildTemplate(widget_data, node, widgetTheme.TEMPLATE_SIDE_LINE);
    };

    this.setAccessCounterValue = function(){
      let data = this.getAccessTopPageValue();
      let result = Number(data);
      $(".text-access-counter").each(function(){
        let initNumber = $(this).data("initNumber");
        let accessCounter = result + initNumber;
        $(this).text(accessCounter);
      });
    };

    this.getAccessTopPageValue = function(){
        let data= 0;
        $.ajax({
                  url: '/api/stats/top_page_access/0/0',
                  method: 'GET',
                  async: false,
                  success: (response) => {
                      if (response.all && response.all.count) {
                          data = response.all.count;
                      }
                  }
              })
         return data;
    };
};

let WidgetTheme = function() {
	this.TEMPLATE_DEFAULT = {
		'border': {
			'border-radius': '5px',
			'border-style': 'outset'
		},
		'scroll-bar': ''
	};
	this.TEMPLATE_SIDE_LINE = {
		'border': {
            'border-radius': '0px !important',
			'border-left-style': 'groove',
			'border-right-style': 'none',
			'border-top-style': 'none',
			'border-bottom-style': 'none'
		},
		'scroll-bar': ''
	};
	this.TEMPLATE_SIMPLE = {
		'border': {
			'border-style': 'none'
		},
		'scroll-bar': ''
	};

	this.buildTemplate = function (widget_data, widget_settings, template) {
		if (!widget_data || !widget_settings) {
			return undefined;
		}
		let id = (widget_data.id) ? widget_data.id : '';
		let labelColor = (widget_settings.label_color) ? widget_settings.label_color : '';
		let borderColor = (widget_settings.frame_border_color) ? widget_settings.frame_border_color : '';
		if (template == this.TEMPLATE_SIDE_LINE) {
			template.border['border-left-style'] = (widget_settings.border_style) ? widget_settings.border_style : 'groove';
		}else {
			template.border['border-style'] = (widget_settings.border_style) ? widget_settings.border_style : template.border['border-style'];
		}
        let borderStyle = (template == this.TEMPLATE_SIMPLE) ? '' : this.buildBorderCss(template.border, borderColor);
		let backgroundColor = (widget_settings.background_color) ? widget_settings.background_color : '';

		let result = '<div class="grid-stack-item widget-resize">' +
			'    <div class="grid-stack-item-content panel widget" style="' + this.buildCssText('background-color', backgroundColor) + borderStyle + '">' +
			'        <div class="panel-heading widget-header widget-header-position" style="' + this.buildCssText('color', labelColor) + '">' +
			'            <strong>' + widget_data.header + '</strong>' +
			'        </div>' +
			'        <div class="panel-body ql-editor"' + this.buildCssText('id', id)+ '">' + widget_data.body +
			'        </div>' +
			'    </div>' +
            '</div>';
        return result
	}

	this.buildCssText = function(keyword, data) {
		let cssStr = '';
		if (data == '') {
			return cssStr;
		}
		switch (keyword) {
			case 'color':
				cssStr = 'color: ' + data + '; ';
				break;
			case 'background-color':
				cssStr = 'background-color: ' + data + '; ';
				break;
			case 'id':
				let innerID = 'new_arrivals' + '_' + index;
				cssStr = 'id="' + innerID + '"';
			default:
				break;
		}
		return cssStr;
	}

	this.buildBorderCss = function(borderSettings, borderColor) {
        let borderStyle = '';
		for (let [key, value] of Object.entries(borderSettings)) {
			if (key && value) {
				borderStyle += key + ': ' + value + '; '
			}
		}
		borderStyle += 'border-color:' + borderColor + '; ';
		return borderStyle;
	}
};

function getWidgetDesignSetting() {
    let community_id = $("#community-id").text();
    let current_language = $("#current_language").val();
    if (!community_id) {
        community_id = 'Root Index';
    }
    if (!current_language) {
        current_language = "en";
    }
    let url = '/api/admin/load_widget_design_setting/' + community_id + '/' + current_language;
    $.ajax({
        type: 'GET',
        url: url,
        success: function (data) {
            if (data.error) {
                console.log(data.error);
                toggleWidgetUI();
                return;
            } else {
                let widgetList = data['widget-settings'];
                if (Array.isArray(widgetList) && widgetList.length) {
                    $("#main_contents").addClass("grid-stack-item");
                    let pageBodyGrid = new PageBodyGrid();
                    pageBodyGrid.init();
                    pageBodyGrid.loadGrid(widgetList);
                    new ResizeSensor($('.widget-resize'), function(){
                        $('.widget-resize').each(function(){
                            let headerElementHeight = $(this).find('.panel-heading').height();
                            $(this).find('.panel-body').css("padding-top", String(headerElementHeight+11) + "px");
                        });
                    });
                }
            }
            toggleWidgetUI();
        }
    });
}

function toggleWidgetUI() {
    $("div#page_body").each(function () {
        $(this).css("display", "block");
        $('footer#footer').css("display", "block");
        $('footer-fix#footer').remove();
    });
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

