webpackJsonp(["main"],{

/***/ "../../../../../src/$$_lazy_route_resource lazy recursive":
/***/ (function(module, exports) {

function webpackEmptyAsyncContext(req) {
	// Here Promise.resolve().then() is used instead of new Promise() to prevent
	// uncatched exception popping up in devtools
	return Promise.resolve().then(function() {
		throw new Error("Cannot find module '" + req + "'.");
	});
}
webpackEmptyAsyncContext.keys = function() { return []; };
webpackEmptyAsyncContext.resolve = webpackEmptyAsyncContext;
module.exports = webpackEmptyAsyncContext;
webpackEmptyAsyncContext.id = "../../../../../src/$$_lazy_route_resource lazy recursive";

/***/ }),

/***/ "../../../../../src/app/app.component.css":
/***/ (function(module, exports, __webpack_require__) {

exports = module.exports = __webpack_require__("../../../../css-loader/lib/css-base.js")(false);
// imports


// module
exports.push([module.i, "", ""]);

// exports


/*** EXPORTS FROM exports-loader ***/
module.exports = module.exports.toString();

/***/ }),

/***/ "../../../../../src/app/app.component.html":
/***/ (function(module, exports) {

module.exports = "<!--The content below is only a placeholder and can be replaced.-->\r\n<app-tree-list2 [templflg]=\"0\" [journalFlg]=\"journalDisplayFlg\"></app-tree-list2>\r\n"

/***/ }),

/***/ "../../../../../src/app/app.component.ts":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "a", function() { return AppComponent; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__angular_core__ = __webpack_require__("../../../core/esm5/core.js");
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};

var AppComponent = /** @class */ (function () {
    function AppComponent(elementRef) {
        this.elementRef = elementRef;
        // display journal Flag: 0-Index Edit (not journal), 1- Journal
        this.journalDisplayFlg = "0";
        this.journalDisplayFlg = this.elementRef.nativeElement.getAttribute('journalDisplayFlg');
    }
    AppComponent.prototype.ngOnInit = function () {
    };
    __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Input"])(),
        __metadata("design:type", String)
    ], AppComponent.prototype, "journalDisplayFlg", void 0);
    AppComponent = __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Component"])({
            selector: 'app-root-tree-hensyu',
            template: __webpack_require__("../../../../../src/app/app.component.html"),
            styles: [__webpack_require__("../../../../../src/app/app.component.css")]
        }),
        __metadata("design:paramtypes", [__WEBPACK_IMPORTED_MODULE_0__angular_core__["ElementRef"]])
    ], AppComponent);
    return AppComponent;
}());



/***/ }),

/***/ "../../../../../src/app/app.module.ts":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "a", function() { return AppModule; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__angular_platform_browser__ = __webpack_require__("../../../platform-browser/esm5/platform-browser.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__angular_core__ = __webpack_require__("../../../core/esm5/core.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2__angular_forms__ = __webpack_require__("../../../forms/esm5/forms.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_3_ng2_tree__ = __webpack_require__("../../../../ng2-tree/index.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_3_ng2_tree___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_3_ng2_tree__);
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_4__angular_http__ = __webpack_require__("../../../http/esm5/http.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_5__app_component__ = __webpack_require__("../../../../../src/app/app.component.ts");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_6__tree_list2_tree_list2_component__ = __webpack_require__("../../../../../src/app/tree-list2/tree-list2.component.ts");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_7__cofirm_modal_cofirm_modal_component__ = __webpack_require__("../../../../../src/app/cofirm-modal/cofirm-modal.component.ts");
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};








var AppModule = /** @class */ (function () {
    function AppModule() {
    }
    AppModule = __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_1__angular_core__["NgModule"])({
            declarations: [
                __WEBPACK_IMPORTED_MODULE_5__app_component__["a" /* AppComponent */],
                __WEBPACK_IMPORTED_MODULE_6__tree_list2_tree_list2_component__["a" /* TreeList2Component */],
                __WEBPACK_IMPORTED_MODULE_7__cofirm_modal_cofirm_modal_component__["a" /* CofirmModalComponent */]
            ],
            imports: [
                __WEBPACK_IMPORTED_MODULE_0__angular_platform_browser__["BrowserModule"],
                __WEBPACK_IMPORTED_MODULE_2__angular_forms__["a" /* FormsModule */],
                __WEBPACK_IMPORTED_MODULE_3_ng2_tree__["TreeModule"],
                __WEBPACK_IMPORTED_MODULE_4__angular_http__["c" /* HttpModule */]
            ],
            exports: [__WEBPACK_IMPORTED_MODULE_6__tree_list2_tree_list2_component__["a" /* TreeList2Component */]],
            providers: [],
            bootstrap: [__WEBPACK_IMPORTED_MODULE_5__app_component__["a" /* AppComponent */]],
        })
    ], AppModule);
    return AppModule;
}());



/***/ }),

/***/ "../../../../../src/app/cofirm-modal/cofirm-modal.component.css":
/***/ (function(module, exports, __webpack_require__) {

exports = module.exports = __webpack_require__("../../../../css-loader/lib/css-base.js")(false);
// imports


// module
exports.push([module.i, "  \r\n  /* The Close Button */\r\n  .close {\r\n    color: rgb(251, 5, 5);\r\n    position: absolute;\r\n    top: 10px;\r\n    right: 25px;\r\n    font-size: 35px;\r\n    font-weight: bold;\r\n  }\r\n  .close:hover,\r\n  .close:focus {\r\n    color: rgb(253, 5, 5);\r\n    text-decoration: none;\r\n    cursor: pointer;\r\n  }\r\n  .modFooter{\r\n    text-align: center;\r\n  }\r\n\r\n  \r\n\r\n  ", ""]);

// exports


/*** EXPORTS FROM exports-loader ***/
module.exports = module.exports.toString();

/***/ }),

/***/ "../../../../../src/app/cofirm-modal/cofirm-modal.component.html":
/***/ (function(module, exports) {

module.exports = "<div class=\"Mymodal\" id=\"CofirmModalComponent\" [style.display]=\"modalAberto.status\">\r\n  <div class=\"modal-content\">\r\n    <div class=\"modal-header\">\r\n      <button type=\"button\" class=\"close\" data-dismiss=\"modal\" (click)=\"delCancle()\">\r\n        &times;\r\n      </button>\r\n      <h4 class=\"modal-title\" id=\"myModalLabel\">\r\n        WEKO\r\n      </h4>\r\n    </div>\r\n    <div class=\"modal-body\">\r\n      <p>\r\n        <span class=\"glyphicon glyphicon-warning-sign\"></span>\r\n      </p>\r\n      <!-- DELETEインデックス以下のインデックスおよびアイテムに対する処理を選択してください -->\r\n      <!-- Please choose processing about index and items! -->\r\n      {{langJsonM.Choose_Processing[1]}}\r\n    </div>\r\n    <div class=\"modal-footer modFooter\">\r\n      <button type=\"button\" class=\"btn btn-primary\" (click)=\"delAll();\"> \r\n        <!-- すべて削除 -->\r\n        <!-- Delete all -->\r\n        {{langJsonM.Delete_all[1]}}\r\n      </button>\r\n      <button *ngIf=\"!parentIsRoot\" type=\"button\" class=\"btn btn-primary\" (click)=\"delAndMove();\"> \r\n        <!-- 親インデックスへ移動 -->\r\n        <!-- Move items to parent Index -->\r\n        {{langJsonM.Move_items_to_parent_Index[1]}}\r\n      </button>\r\n      <button type=\"button\" class=\"btn btn-default\" data-dismiss=\"modal\" (click)=\"delCancle();\">\r\n        <!-- キャンセル -->\r\n        <!-- Cancle -->\r\n        {{langJsonM.Cancle[1]}}\r\n      </button>\r\n    </div>\r\n  </div>\r\n</div>"

/***/ }),

/***/ "../../../../../src/app/cofirm-modal/cofirm-modal.component.ts":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "a", function() { return CofirmModalComponent; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__angular_core__ = __webpack_require__("../../../core/esm5/core.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__tree_list2_service__ = __webpack_require__("../../../../../src/app/tree-list2.service.ts");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_jquery__ = __webpack_require__("../../../../jquery/dist/jquery.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_jquery___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_2_jquery__);
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var CofirmModalComponent = /** @class */ (function () {
    function CofirmModalComponent(treeList2Service) {
        this.treeList2Service = treeList2Service;
        //
        this.buttonClickEvent = new __WEBPACK_IMPORTED_MODULE_0__angular_core__["EventEmitter"]();
        this.parentIsRoot = false;
        this.langJsonM = {
            Choose_Processing: [],
            Delete_all: [],
            Move_items_to_parent_Index: [],
            Cancle: []
        };
    }
    CofirmModalComponent.prototype.ngOnInit = function () {
        this.setI18n();
    };
    CofirmModalComponent.prototype.ngAfterViewInit = function () {
        this.modalAberto.status = "none";
    };
    /**
     * i18n
     */
    CofirmModalComponent.prototype.setI18n = function () {
        var _this = this;
        var lang = __WEBPACK_IMPORTED_MODULE_2_jquery__("#lang-code").val();
        var js = document.scripts;
        var jsUrl = js[js.length - 1].src;
        var strUrl = jsUrl.substring(0, jsUrl.lastIndexOf('static'));
        var jsonUrl = strUrl + "static/json/weko_index_tree/translations/" + lang + "/messages.json";
        this.treeList2Service.getLnagJson(jsonUrl).then(function (res) {
            _this.langJsonM = res;
        }).catch();
    };
    CofirmModalComponent.prototype.closeModal = function () {
        this.modalAberto.status = "none";
    };
    /**
     * キャンセルボタン
     */
    CofirmModalComponent.prototype.delCancle = function () {
        this.buttonClickEvent.emit("delCancle");
        //modal close
        this.closeModal();
    };
    /**
     * すべて削除
     */
    CofirmModalComponent.prototype.delAll = function () {
        this.buttonClickEvent.emit("delAll");
        this.closeModal();
    };
    /**
     *
     */
    CofirmModalComponent.prototype.delAndMove = function () {
        this.buttonClickEvent.emit("delAndMove");
        this.closeModal();
    };
    __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Output"])(),
        __metadata("design:type", __WEBPACK_IMPORTED_MODULE_0__angular_core__["EventEmitter"])
    ], CofirmModalComponent.prototype, "buttonClickEvent", void 0);
    __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Input"])(),
        __metadata("design:type", Object)
    ], CofirmModalComponent.prototype, "modalAberto", void 0);
    __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Input"])(),
        __metadata("design:type", Boolean)
    ], CofirmModalComponent.prototype, "parentIsRoot", void 0);
    CofirmModalComponent = __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Component"])({
            selector: 'app-cofirm-modal',
            template: __webpack_require__("../../../../../src/app/cofirm-modal/cofirm-modal.component.html"),
            styles: [__webpack_require__("../../../../../src/app/cofirm-modal/cofirm-modal.component.css")]
        }),
        __metadata("design:paramtypes", [__WEBPACK_IMPORTED_MODULE_1__tree_list2_service__["a" /* TreeList2Service */]])
    ], CofirmModalComponent);
    return CofirmModalComponent;
}());



/***/ }),

/***/ "../../../../../src/app/tree-list2.service.ts":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "a", function() { return TreeList2Service; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__angular_core__ = __webpack_require__("../../../core/esm5/core.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__angular_http__ = __webpack_require__("../../../http/esm5/http.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_rxjs_add_operator_toPromise__ = __webpack_require__("../../../../rxjs/_esm5/add/operator/toPromise.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_rxjs_add_operator_toPromise___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_2_rxjs_add_operator_toPromise__);
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var TreeList2Service = /** @class */ (function () {
    function TreeList2Service(http) {
        this.http = http;
        //サービスの設定
        this.headers = new __WEBPACK_IMPORTED_MODULE_1__angular_http__["a" /* Headers */]({ 'Content-Type': 'application/json' });
        this.options = new __WEBPACK_IMPORTED_MODULE_1__angular_http__["d" /* RequestOptions */]({ headers: this.headers });
    }
    /**
     * 選択したNODEの情報を取得する
     * @param nodeId: 選択したNodeId
     */
    TreeList2Service.prototype.getNodeInfo = function (url) {
        //APIからtree情報を取得する
        return this.http.get(url)
            .toPromise()
            .then(function (response) { return response.json(); })
            .catch(this.handleError);
    };
    ;
    /**
     *最新tree情報を取得する
    */
    TreeList2Service.prototype.getTreeInfo = function (url) {
        //APIからtree情報を取得する
        return this.http.get(url)
            .toPromise()
            .then(function (response) { return response.json(); })
            .catch(this.handleError);
    };
    ;
    /**
      *最新tree情報を取得する
     */
    TreeList2Service.prototype.getJournalInfo = function (url) {
        //APIからtree情報を取得する
        return this.http.get(url)
            .toPromise()
            .then(function (response) { return response.json(); })
            .catch(this.handleError);
    };
    ;
    /**
     *最新Tree情報をApiへ設定する
     */
    TreeList2Service.prototype.setTreeInfo = function (parentNodeId, treeModel) {
        var urlArr = window.location.href.split('/');
        var url = urlArr[0] + "//" + urlArr[2] + "/api/tree/index/" + parentNodeId;
        return this.http
            .post(url, treeModel, this.options)
            .toPromise()
            .then(function (response) { return null; })
            .catch(this.handleError);
    };
    /**
     * nodeの情報を設定する
     */
    TreeList2Service.prototype.setNodeInfo = function (nodeId, data) {
        var urlArr = window.location.href.split('/');
        var url = urlArr[0] + "//" + urlArr[2] + "/api/tree/index/" + nodeId;
        return this.http
            .put(url, data)
            .toPromise()
            .then(function (response) { return response.json(); })
            .catch(this.handleError);
    };
    /**
     *
     *最新Tree情報をApiへ設定する
     *@param nodeId selected nodeId
     *@param action move , all
     */
    TreeList2Service.prototype.delOrMoveNodeInfo = function (nodeId, action) {
        var urlArr = window.location.href.split('/');
        var url = urlArr[0] + "//" + urlArr[2] + "/api/tree/index/" + nodeId + "?action=" + action;
        return this.http
            .delete(url)
            .toPromise()
            .then(function (response) { return response.json(); })
            .catch(this.handleError);
    };
    /**
    * 多言語対応
   */
    TreeList2Service.prototype.getLnagJson = function (url) {
        return this.http
            .get(url)
            .toPromise()
            .then(function (response) { return response.json(); })
            .catch(this.handleError);
    };
    /**
     * node move
     */
    TreeList2Service.prototype.setNodeMoved = function (nodeId, infoJson) {
        var urlArr = window.location.href.split('/');
        var url = urlArr[0] + "//" + urlArr[2] + "/api/tree/move/" + nodeId;
        return this.http
            .put(url, infoJson)
            .toPromise()
            .then(function (response) { return response.json(); })
            .catch(this.handleError);
    };
    TreeList2Service.prototype.upload = function (formData, nodeId) {
        var headers = new __WEBPACK_IMPORTED_MODULE_1__angular_http__["a" /* Headers */]();
        // headers.append('enctype', 'multipart/form-data');
        headers.append('Accept', 'application/json');
        var options = new __WEBPACK_IMPORTED_MODULE_1__angular_http__["d" /* RequestOptions */]({ headers: headers });
        var urlArr = window.location.href.split('/');
        var url = urlArr[0] + "//" + urlArr[2] + "/indextree/upload";
        return this.http
            .post(url, formData, options)
            .toPromise()
            .then(function (response) { return response.json(); })
            .catch(this.handleError);
    };
    /**
     * エラー処理
     */
    TreeList2Service.prototype.handleError = function (error) {
        console.error('An error occurred', error); // 
        return Promise.reject(error.message || error);
    };
    TreeList2Service = __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Injectable"])(),
        __metadata("design:paramtypes", [__WEBPACK_IMPORTED_MODULE_1__angular_http__["b" /* Http */]])
    ], TreeList2Service);
    return TreeList2Service;
}());



/***/ }),

/***/ "../../../../../src/app/tree-list2/tree-list2.component.css":
/***/ (function(module, exports, __webpack_require__) {

exports = module.exports = __webpack_require__("../../../../css-loader/lib/css-base.js")(false);
// imports


// module
exports.push([module.i, ".button-create {\r\n  margin-left: 40px;\r\n}\r\n.button-delete {\r\n  margin-left: 10px;\r\n}\r\n#display_no {\r\n  width: 10%;\r\n  text-align: right;\r\n}", ""]);

// exports


/*** EXPORTS FROM exports-loader ***/
module.exports = module.exports.toString();

/***/ }),

/***/ "../../../../../src/app/tree-list2/tree-list2.component.html":
/***/ (function(module, exports) {

module.exports = "<p></p>\r\n<div class=\"col-sm-12 col-md-12\">\r\n  <div class=\"row\">\r\n    <div class=\"col-sm-3 col-md-3 col-lg-3\">\r\n      <p>\r\n        <button id=\"add\" value=\"New\" class=\"btn btn-info button-create\" (click)=\"addNode()\">\r\n          <!-- 新規 -->\r\n          <!-- Add -->\r\n          {{langJson.Add[1]}}\r\n        </button>\r\n        <button id=\"del\" value=\"Delete\" class=\"btn btn-info button-delete\" (click)=\"deleNode()\">\r\n          <!-- 削除 -->\r\n          <!-- Delete -->\r\n          {{langJson.Delete[1]}}\r\n        </button>\r\n      </p>\r\n      <div>\r\n        <tree [tree]=\"treeH\" [settings]=\"checkboxSettings\" (nodeMoved)=\"handleMoved($event)\" (nodeSelected)=\"seleNode($event)\" #treeList></tree>\r\n      </div>\r\n    </div>\r\n    <div *ngIf=\"templflg=='0' && journalFlg=='0'\" class=\"col-sm-8 col-md-8 col-lg-8\">\r\n      <fieldset *ngIf=\"!inputFlg\" disabled>\r\n        <div class=\"panel panel-default\">\r\n          <div class=\"panel-heading\">\r\n            <h3 class=\"panel-title\">\r\n              <!-- インデックス編集 -->\r\n              <!-- INDEX EDIT -->\r\n              {{langJson.Index_Edit[1]}}\r\n            </h3>\r\n          </div>\r\n          <div class=\"panel-body\">\r\n            <div class=\"panel-group\">\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">\r\n                      <!-- インデックス -->\r\n                      <!-- Index -->\r\n                      {{langJson.Index[1]}}\r\n                    </div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <div class=\"input-group\">\r\n                        <span class=\"input-group-addon\">\r\n                          <!-- 日本語 -->\r\n                          <!-- Janpanese -->\r\n                          {{langJson.Janpanese[1]}}\r\n                        </span>\r\n                        <input type=\"text\" class=\"form-control\" id=\"inputTitle_ja\" placeholder=\"\" [(ngModel)]=\"detailData.index_name\">\r\n                      </div>\r\n                      <div class=\"row-line-space\"></div>\r\n                      <div class=\"input-group\">\r\n                        <span class=\"input-group-addon\">\r\n                          <!-- 英語 -->\r\n                          <!-- English -->\r\n                          {{langJson.English[1]}}\r\n                        </span>\r\n                        <input type=\"text\" class=\"form-control\" id=\"inputTitle_en\" placeholder=\"\" [(ngModel)]=\"detailData.index_name_english\">\r\n                      </div>\r\n                    </div>\r\n                  </div>\r\n                </div>\r\n              </div>\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">\r\n                      <!-- コメント -->\r\n                      <!-- Comment -->\r\n                      {{langJson.Comment[1]}}\r\n                    </div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <textarea class=\"form-control\" rows=\"3\" id=\"inputComment\" [(ngModel)]=\"detailData.comment\"></textarea>\r\n                    </div>\r\n                  </div>\r\n                </div>\r\n              </div>\r\n            </div>\r\n          </div>\r\n          <div class=\"panel-footer\">\r\n            <button id=\"index-detail-submit\" class=\"btn btn-info\" (click)=\"sendingdetail()\">\r\n              <!-- 送信 -->\r\n              <!-- Send -->\r\n              {{langJson.Send[1]}}\r\n            </button>\r\n          </div>\r\n        </div>\r\n      </fieldset>\r\n      <fieldset *ngIf=\"inputFlg\">\r\n        <div class=\"panel panel-default\">\r\n          <div class=\"panel-heading\">\r\n            <h3 class=\"panel-title\">{{langJson.Index_Edit[1]}}</h3>\r\n          </div>\r\n          <div class=\"panel-body\">\r\n            <div class=\"panel-group\">\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">{{langJson.Index[1]}}</div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <div class=\"input-group\">\r\n                        <span class=\"input-group-addon\">{{langJson.Janpanese[1]}}</span>\r\n                        <input type=\"text\" class=\"form-control\" id=\"inputTitle_ja\" placeholder=\"\" [(ngModel)]=\"detailData.index_name\">\r\n                      </div>\r\n                      <div class=\"row-line-space\"></div>\r\n                      <div class=\"input-group\">\r\n                        <span class=\"input-group-addon\">{{langJson.English[1]}}<span class=\"text-danger\">＊</span></span>\r\n                        <input type=\"text\" class=\"form-control\" id=\"inputTitle_en\" placeholder=\"\" [(ngModel)]=\"detailData.index_name_english\">\r\n                      </div>\r\n                      <span *ngIf=\"checkFlg\" class=\"text-danger\">英語で入力は必要です。</span>\r\n                    </div>\r\n                  </div>\r\n                </div>\r\n              </div>\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">{{langJson.Comment[1]}}</div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <textarea class=\"form-control\" rows=\"3\" id=\"inputComment\" [(ngModel)]=\"detailData.comment\"></textarea>\r\n                    </div>\r\n                  </div>\r\n                </div>\r\n              </div>\r\n              <!-- 0611 add start -->\r\n              <!-- 公開 -->\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">\r\n                      <!-- Display range -->\r\n                      <!-- {{langJson.Display_Range[1]}} -->\r\n                      {{langJson.Publish[1]}}\r\n                    </div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <input type=\"checkbox\" id=\"rss_display\" [(ngModel)]=\"detailData.public_state\">{{langJson.Open_To_Public[1]}}\r\n                      <p>\r\n                        <div *ngIf=\"detailData.public_state\" class=\"input-group\">\r\n                          <span class=\"input-group-addon\">\r\n                            <!-- {{langJson.Janpanese[1]}} -->\r\n                            {{langJson.Date[1]}}：\r\n                          </span>\r\n                          <input type=\"text\" class=\"form-control\" id=\"datepicker\" placeholder=\"例：20180628\" [(ngModel)]=\"detailData.public_date\">\r\n                        </div>\r\n                        <p>\r\n                        <div *ngIf=\"detailData.public_state\">\r\n                          <input type=\"checkbox\" id=\"rss_display\" [(ngModel)]=\"detailData.recursive_public_state\">{{langJson.Set_Publish_Date_Recursively[1]}}\r\n                        </div>\r\n                    </div>\r\n                  </div>\r\n                </div>\r\n              </div>\r\n              <!-- index link -->\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">\r\n                      <!-- Display range -->\r\n                      {{langJson.Index_Link[1]}}\r\n                    </div>\r\n                      <div class=\"col-sm-10 col-md-10\">\r\n                        <div>\r\n                          <input type=\"checkbox\" id=\"index_link_enabled\" [(ngModel)]=\"detailData.index_link_enabled\"> Enable\r\n                        </div>\r\n                        <p>\r\n                        <div class=\"input-group\">\r\n                          <span class=\"input-group-addon\">{{langJson.Janpanese[1]}}</span>\r\n                          <input type=\"text\" class=\"form-control\" id=\"indexLink_ja\" placeholder=\"\" [(ngModel)]=\"detailData.index_link_name\">\r\n                        </div>\r\n                        <div class=\"row-line-space\"></div>\r\n                        <div class=\"input-group\">\r\n                          <span class=\"input-group-addon\">{{langJson.English[1]}}<span class=\"text-danger\">＊</span></span>\r\n                          <input type=\"text\" class=\"form-control\" id=\"indexLink_en\" placeholder=\"\" [(ngModel)]=\"detailData.index_link_name_english\">\r\n                        </div>\r\n                        <span *ngIf=\"checkFlg\" class=\"text-danger\">英語で入力は必要です。</span>\r\n                      </div>\r\n                  </div>\r\n                </div>\r\n              </div>\r\n              <!-- more 機能 -->\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">\r\n                      <!-- Display range -->\r\n                      {{langJson.More_Function[1]}}\r\n                    </div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <div class=\"checkbox\">\r\n                        <label>\r\n                          <input *ngIf=\"detailData.have_children; else is_disable\" type=\"checkbox\" id=\"more_check\" [(ngModel)]=\"detailData.more_check\">\r\n                          <ng-template #is_disable>\r\n                            <input type=\"checkbox\" id=\"more_check\" [(ngModel)]=\"detailData.more_check\" disabled='disabled'>\r\n                          </ng-template>\r\n                          {{langJson.More_Check[1]}}\r\n                        </label>\r\n                      </div>\r\n                      <div *ngIf=\"detailData.more_check\">\r\n                        <p>{{langJson.More_No[1]}}<br>\r\n                        <input type=\"text\" id=\"display_no\" class=\"form-control\" [(ngModel)]=\"detailData.display_no\">\r\n                      </div>\r\n                    </div>\r\n                  </div>\r\n                </div>\r\n              </div>\r\n              <!-- OAI-PMH -->\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">\r\n                      {{langJson.Harvest_Publish[1]}}\r\n                    </div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <div class=\"checkbox\">\r\n                        <label>\r\n                          <input type=\"checkbox\" id=\"rss_display\" [(ngModel)]=\"detailData.harvest_public_state\"> \r\n                          {{langJson.Open_To_Public[1]}}\r\n                        </label>\r\n                        <p>\r\n                          <span class=\"text-danger\">※{{langJson.Harvest_Message[1]}}</span>\r\n                      </div>\r\n                    </div>\r\n                  </div>\r\n                </div>\r\n              </div>\r\n              <!-- 閲覧権限設定 -->\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">\r\n                        <!-- Display range -->\r\n                        <!-- {{langJson.Display_Range[1]}} -->\r\n                        {{langJson.Browsing_Privilege[1]}}\r\n                    </div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <div class=\"col-sm-5 col-md-5\">\r\n                        <p>{{langJson.Role[1]}}<br>{{langJson.Authorized[1]}}\r\n                          <select multiple class=\"form-control\" id=\"browsing_role_able\" [(ngModel)]=\"roleModel.browsing_role_able\">\r\n                            <option *ngFor=\"let browRoleAble of detailData.browsing_role.allow;let i = index\" [value]=\"i\">{{browRoleAble.name}}</option>\r\n                          </select>\r\n                      </div>\r\n                      <div class=\"col-sm-2 col-md-2\">\r\n                        &nbsp;&nbsp;\r\n                        <p><br>\r\n                        <button type=\"button\" class=\"btn btn-default\" (click)=\"setBrowsingAllowToDeny(roleModel.browsing_role_able)\">\r\n                          <span class=\"glyphicon glyphicon-arrow-right\"></span>\r\n                        </button>\r\n                        <p></p>\r\n                        <button type=\"button\" class=\"btn btn-default\" (click)=\"setBrowsingDenyToAllow(roleModel.browsing_role_unable)\">\r\n                          <span class=\"glyphicon glyphicon-arrow-left\"></span>\r\n                        </button>\r\n                      </div>\r\n                      <div class=\"col-sm-5 col-md-5\">\r\n                        <p><br>{{langJson.Unauthorized[1]}}\r\n                          <select multiple class=\"form-control\" id=\"browsing_role_unable\" [(ngModel)]=\"roleModel.browsing_role_unable\">\r\n                            <option *ngFor=\"let browsing_role_unable of detailData.browsing_role.deny;let i = index\" [value]=\"i\">{{browsing_role_unable.name}}</option>\r\n                          </select>\r\n                      </div>\r\n                    </div>\r\n                  </div>\r\n                  <div class=\"row\">\r\n                      <div class=\"col-sm-2 col-md-2\"></div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                        &nbsp;&nbsp;&nbsp;\r\n                        <input type=\"checkbox\" id=\"rss_display\" [(ngModel)]=\"detailData.recursive_browsing_role\">{{langJson.Set_Role_Recursively[1]}}\r\n                    </div>\r\n                  </div>\r\n                  <!-- 20180925 add start -->\r\n                  <!-- Read Permission by Group -->\r\n                  <div class=\"row\">&nbsp;</div>\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\"></div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <div class=\"col-sm-5 col-md-5\">\r\n                        <p>{{langJson.Group[1]}}<br>{{langJson.Authorized[1]}}\r\n                          <select multiple class=\"form-control\" id=\"browsing_group_able\" [(ngModel)]=\"groupModel.browsing_group_able\">\r\n                            <option *ngFor=\"let browGroupAble of detailData.browsing_group.allow;let i = index\" [value]=\"i\">{{browGroupAble.name}}</option>\r\n                          </select>\r\n                      </div>\r\n                      <div class=\"col-sm-2 col-md-2\">\r\n                        &nbsp;&nbsp;\r\n                        <p><br>\r\n                        <button type=\"button\" class=\"btn btn-default\" (click)=\"setBrowsingGroupAllowToDeny(groupModel.browsing_group_able)\">\r\n                          <span class=\"glyphicon glyphicon-arrow-right\"></span>\r\n                        </button>\r\n                        <p></p>\r\n                        <button type=\"button\" class=\"btn btn-default\" (click)=\"setBrowsingGroupDenyToAllow(groupModel.browsing_group_unable)\">\r\n                          <span class=\"glyphicon glyphicon-arrow-left\"></span>\r\n                        </button>\r\n                      </div>\r\n                      <div class=\"col-sm-5 col-md-5\">\r\n                        <p><br>{{langJson.Unauthorized[1]}}\r\n                          <select multiple class=\"form-control\" id=\"browsing_group_unable\" [(ngModel)]=\"groupModel.browsing_group_unable\">\r\n                            <option *ngFor=\"let browsing_group_unable of detailData.browsing_group.deny;let i = index\" [value]=\"i\">{{browsing_group_unable.name}}</option>\r\n                          </select>\r\n                        </p>\r\n                      </div>\r\n                    </div>\r\n                  </div>\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\"></div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      &nbsp;&nbsp;&nbsp;\r\n                      <input type=\"checkbox\" id=\"rss_display\" [(ngModel)]=\"detailData.recursive_browsing_group\">{{langJson.Set_Group_Recursively[1]}}\r\n                    </div>\r\n                  </div>\r\n                  <!-- 20180925 add end -->\r\n                </div>\r\n              </div>\r\n              <!-- 投稿権限設定 -->\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\">\r\n                      <!-- Display range -->\r\n                      <!-- {{langJson.Display_Range[1]}} -->\r\n                      {{langJson.Deposit_Privilege[1]}}\r\n                    </div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <div class=\"col-sm-5 col-md-5\">\r\n                        <p>{{langJson.Role[1]}}<br>{{langJson.Authorized[1]}}\r\n                          <select multiple class=\"form-control\" id=\"contribute_role_able\" [(ngModel)]=\"roleModel.contribute_role_able\">\r\n                            <option *ngFor=\"let contribute_role_able of detailData.contribute_role.allow;let i = index\" [value]=\"i\">{{contribute_role_able.name}}</option>\r\n                          </select>\r\n                          <p></p>\r\n                      </div>\r\n                      <div class=\"col-sm-2 col-md-2\">\r\n                        &nbsp;&nbsp;\r\n                        <p><br>\r\n                        <button type=\"button\" class=\"btn btn-default\" (click)=\"setContributeAllowToDeny(roleModel.contribute_role_able)\">\r\n                          <span class=\"glyphicon glyphicon-arrow-right\"></span>\r\n                        </button>\r\n                        <p></p>\r\n                        <button type=\"button\" class=\"btn btn-default\" (click)=\"setContributeDenyToAllow(roleModel.contribute_role_unable)\">\r\n                          <span class=\"glyphicon glyphicon-arrow-left\"></span>\r\n                        </button>\r\n                      </div>\r\n                      <div class=\"col-sm-5 col-md-5\">\r\n                        <p><br>{{langJson.Unauthorized[1]}}\r\n                          <select multiple class=\"form-control\" id=\"contribute_role_unable\" [(ngModel)]=\"roleModel.contribute_role_unable\">\r\n                            <option *ngFor=\"let contribute_role_unable of detailData.contribute_role.deny;let i = index\" [value]=\"i\">{{contribute_role_unable.name}}</option>\r\n                          </select>\r\n                      </div>\r\n                    </div>\r\n                  </div>\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\"></div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      &nbsp;&nbsp;&nbsp;\r\n                      <input type=\"checkbox\" id=\"rss_display\" [(ngModel)]=\"detailData.recursive_contribute_role\">{{langJson.Set_Role_Recursively[1]}}\r\n                    </div>\r\n                  </div>\r\n                  <!-- 20180925 add start -->\r\n                  <!-- Write Permission by Group -->\r\n                  <div class=\"row\">&nbsp;</div>\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\"></div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      <div class=\"col-sm-5 col-md-5\">\r\n                        <p>{{langJson.Group[1]}}<br>{{langJson.Authorized[1]}}\r\n                          <select multiple class=\"form-control\" id=\"contribute_group_able\" [(ngModel)]=\"groupModel.contribute_group_able\">\r\n                            <option *ngFor=\"let contribute_group_able of detailData.contribute_group.allow;let i = index\" [value]=\"i\">{{contribute_group_able.name}}</option>\r\n                          </select>\r\n                          <p></p>\r\n                      </div>\r\n                      <div class=\"col-sm-2 col-md-2\">\r\n                        &nbsp;&nbsp;\r\n                        <p><br>\r\n                        <button type=\"button\" class=\"btn btn-default\" (click)=\"setContributeGroupAllowToDeny(groupModel.contribute_group_able)\">\r\n                          <span class=\"glyphicon glyphicon-arrow-right\"></span>\r\n                        </button>\r\n                        <p></p>\r\n                        <button type=\"button\" class=\"btn btn-default\" (click)=\"setContributeGroupDenyToAllow(groupModel.contribute_group_unable)\">\r\n                          <span class=\"glyphicon glyphicon-arrow-left\"></span>\r\n                        </button>\r\n                      </div>\r\n                      <div class=\"col-sm-5 col-md-5\">\r\n                        <p><br>{{langJson.Unauthorized[1]}}\r\n                          <select multiple class=\"form-control\" id=\"contribute_group_unable\" [(ngModel)]=\"groupModel.contribute_group_unable\">\r\n                            <option *ngFor=\"let contribute_group_unable of detailData.contribute_group.deny;let i = index\" [value]=\"i\">{{contribute_group_unable.name}}</option>\r\n                          </select>\r\n                      </div>\r\n                    </div>\r\n                  </div>\r\n                  <div class=\"row\">\r\n                    <div class=\"col-sm-2 col-md-2\"></div>\r\n                    <div class=\"col-sm-10 col-md-10\">\r\n                      &nbsp;&nbsp;&nbsp;\r\n                      <input type=\"checkbox\" id=\"rss_display\" [(ngModel)]=\"detailData.recursive_contribute_group\">{{langJson.Set_Group_Recursively[1]}}\r\n                    </div>\r\n                  </div>\r\n                  <!-- 20180925 add end -->\r\n                </div>\r\n              </div>\r\n              <!-- 0611 add end -->\r\n              <!-- 0709 add start -->\r\n              <div class=\"panel panel-default\">\r\n                  <div class=\"panel-body\">\r\n                    <div class=\"row\">\r\n                      <div class=\"col-sm-2 col-md-2\">\r\n                        <!-- Display range -->\r\n                        {{langJson.Display_Format[1]}}<br>({{langJson.Search_Results[1]}})\r\n                      </div>\r\n                      <div class=\"col-sm-10 col-md-10\">\r\n                        <div class=\"checkbox\">\r\n                          <label>\r\n                            <input type=\"radio\" [ngModel]=\"detailData.display_format\" [checked]=\"detailData.display_format =='1'\" (click)=\"detailData.display_format = '1'\"\r\n                            name=\"display_format\" value=\"1\">&nbsp;{{langJson.List[1]}}&nbsp;&nbsp;\r\n                          </label>\r\n                          <label>\r\n                            <input type=\"radio\" [ngModel]=\"detailData.display_format\" [checked]=\"detailData.display_format == '2'\" (click)=\"detailData.display_format = '2'\"\r\n                              name=\"display_format\" value=\"2\">&nbsp;{{langJson.Contents_Table[1]}}\r\n                          </label>\r\n                        </div>\r\n                      </div>\r\n                    </div>\r\n                  </div>\r\n                </div>\r\n              <div class=\"panel panel-default\">\r\n                <div class=\"panel-body\">\r\n                    <div class=\"row\">\r\n                      <div class=\"col-sm-10 col-md-10\">\r\n                        {{langJson.File_Size[1]}} : 2MB<br>\r\n                        {{langJson.Image_Size[1]}} : 1024px × 1280px <br>\r\n                        {{langJson.File_Type[1]}} : gif, jpg, jpe, jpeg, png, bmp, tiff, tif\r\n                      </div>\r\n                    </div>\r\n                    <p>\r\n                    <div class=\"row\">\r\n                        <div class=\"col-sm-10 col-md-10\">\r\n                            <input type=\"file\" (change)=\"fileChange($event)\" placeholder=\"Upload file\" name=\"uploadFile\" accept=\".gif,.jpg,.jpe,.jpeg,.png,.bmp,.tiff,.tif\">\r\n                        </div>\r\n                    </div>\r\n                    <div class=\"row\">\r\n                        <p>\r\n                        <div *ngIf=\"privousUploadFlg\">\r\n                            <img [src]=\"imgSrc\" class=\"img-thumbnail\">\r\n                        </div>\r\n                    </div>\r\n                </div>\r\n              </div>\r\n              <!-- 0709 add end -->\r\n            </div>\r\n          </div>\r\n          <div class=\"panel-footer\">\r\n            <button id=\"index-detail-submit\" class=\"btn btn-info\" (click)=\"sendingdetail()\">{{langJson.Send[1]}}</button>\r\n          </div>\r\n        </div>\r\n      </fieldset>\r\n    </div>\r\n    <div *ngIf=\"journalFlg=='1'\" class=\"col-sm-8 col-md-8 col-lg-8\" id=\"journalHtml\">\r\n      <iframe id=\"step_item_login\" name=\"step_item_login\" frameborder=\"0\" width=\"100%\" height=\"700px\" src=\"/indextree/journal/right-content\"></iframe>\r\n      <input type=\"hidden\" id=\"cur_index_id\" [value]=\"selNodeId\"/>\r\n      <!--The content below is only a placeholder and can be replaced.-->\r\n      <span>Welcome to Register Journal Information</span>\r\n    </div>\r\n    <app-cofirm-modal [modalAberto]=\"modalStatus\" [parentIsRoot]=\"parentIsRoot\" (buttonClickEvent)=\"deleteNode($event)\"></app-cofirm-modal>\r\n  </div>\r\n"

/***/ }),

/***/ "../../../../../src/app/tree-list2/tree-list2.component.ts":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "a", function() { return TreeList2Component; });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__angular_core__ = __webpack_require__("../../../core/esm5/core.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__tree_list2_service__ = __webpack_require__("../../../../../src/app/tree-list2.service.ts");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_jquery__ = __webpack_require__("../../../../jquery/dist/jquery.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2_jquery___default = __webpack_require__.n(__WEBPACK_IMPORTED_MODULE_2_jquery__);
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};



var TreeList2Component = /** @class */ (function () {
    function TreeList2Component(treeList2Service) {
        this.treeList2Service = treeList2Service;
        //表示様式フラグ　0:チェックボークスなし　1:チェックボークスあり
        this.templflg = "0";
        // display journal Flag: 0-Index Edit (not journal), 1- Journal
        this.journalFlg = "0";
        //選択したnodeIｄ
        this.selNodeId = "";
        //settings templite
        this.setting = {};
        //treeの設定
        this.checkboxSettings = {};
        this.hiddenNodeId = "hidden";
        //Tree　json
        this.treeH = {
            value: "Root Index",
            id: "0",
            children: [{ value: '', id: this.hiddenNodeId }],
            settings: {
                'static': false,
                'isCollapsedOnInit': false,
                'rightMenu': false,
                'leftMenu': false,
                'cssClasses': {
                    'leaf': 'weko-node-leaf',
                    'empty': 'weko-node-empty'
                }
            }
        };
        //ツリー詳細
        this.detailData = {
            id: "", index_name: null, index_name_english: null, comment: "",
            public_state: false, public_date: null, recursive_public_state: false,
            more_check: false, display_no: null, have_children: false,
            browsing_role: {
                deny: [{ id: "", name: "" }],
                allow: [{ id: "", name: "" }]
            },
            contribute_role: {
                deny: [{ id: "", name: "" }],
                allow: [{ id: "", name: "" }]
            },
            browsing_group: {
                deny: [{ id: "", name: "" }],
                allow: [{ id: "", name: "" }]
            },
            contribute_group: {
                deny: [{ id: "", name: "" }],
                allow: [{ id: "", name: "" }]
            },
            recursive_browsing_role: false,
            recursive_contribute_role: false,
            recursive_browsing_group: false,
            recursive_contribute_group: false,
            harvest_public_state: true,
            display_format: "1",
            image_name: ""
        };
        this.roleModel = {
            browsing_role_able: [],
            browsing_role_unable: [],
            contribute_role_able: [],
            contribute_role_unable: []
        };
        this.groupModel = {
            browsing_group_able: [],
            browsing_group_unable: [],
            contribute_group_able: [],
            contribute_group_unable: []
        };
        //詳細画面入力フラグ
        this.inputFlg = false;
        //modalの表示用
        this.modalStatus = { 'status': 'none' };
        //返す結果状態
        this.res = { code: 400, msg: "", data: { count: 0 } };
        //parentNode を判断する
        this.parentIsRoot = false;
        //i18n 
        this.langJson = {
            Add: [],
            Delete: [],
            Index_Edit: [],
            Index_Link: [],
            Index: [],
            Janpanese: [],
            English: [],
            Comment: [],
            More_Function: [],
            More_Check: [],
            More_No: [],
            Publish: [],
            Open_To_Public: [],
            Date: [],
            Set_Publish_Date_Recursively: [],
            Harvest_Publish: [],
            Harvest_Message: [],
            Browsing_Privilege: [],
            Role: [],
            Set_Role_Recursively: [],
            Authorized: [],
            Unauthorized: [],
            Group: [],
            Set_Group_Recursively: [],
            Deposit_Privilege: [],
            Display_Format: [],
            Search_Results: [],
            List: [],
            Contents_Table: [],
            File_Size: [],
            Image_Size: [],
            File_Type: [],
            Send: []
        };
        this.formData = new FormData();
        this.imgSrc = "";
        this.uploadFlg = false;
        this.privousUploadFlg = false;
        this.checkFlg = false;
    }
    TreeList2Component.prototype.ngOnInit = function () {
        this.setI18n();
        //チェックボックスあるかを設定する
        if (this.templflg == '0') {
            this.checkboxSettings = {
                rootIsVisible: true,
                showCheckboxes: false
            };
        }
        else {
            this.checkboxSettings = {
                rootIsVisible: false,
                showCheckboxes: true
            };
        }
        ;
        this.setIndexTree();
    };
    /**
     * 画面をロードした後に処理を行う
     */
    TreeList2Component.prototype.ngAfterViewInit = function () { };
    /**
     *
     * setIndexTree
     */
    TreeList2Component.prototype.setIndexTree = function () {
        var _this = this;
        //画面初期treeを取得
        var getTreeJsonUrl = document.getElementById('get_tree_json').innerText;
        this.treeList2Service.getTreeInfo(getTreeJsonUrl).then(function (arr) {
            var oopNodeController = _this.treeList.getControllerByNodeId("0");
            if (Array.isArray(arr) && arr.length > 0) {
                oopNodeController.setChildren(arr);
            }
        });
    };
    /**
     * i18n
     */
    TreeList2Component.prototype.setI18n = function () {
        var _this = this;
        var lang = __WEBPACK_IMPORTED_MODULE_2_jquery__("#lang-code").val();
        var js = document.scripts;
        var jsUrl = js[js.length - 1].src;
        var strUrl = jsUrl.substring(0, jsUrl.lastIndexOf('static'));
        var jsonUrl = strUrl + "static/json/weko_index_tree/translations/" + lang + "/messages.json";
        this.treeList2Service.getLnagJson(jsonUrl).then(function (res) {
            _this.langJson = res;
        }).catch();
    };
    /**
     * Nodeを削除する
     */
    TreeList2Component.prototype.deleNode = function () {
        //nodeは選択されない場合
        if (this.selNodeId == null || this.selNodeId == "0") {
            return;
        }
        //選択したインデックスに子インデックスを判断する
        var oopNodeController = this.treeList.getControllerByNodeId(this.selNodeId);
        var parentNodeID = oopNodeController.tree.parent.id;
        //モデル画面を表示する
        if (parentNodeID == "0") {
            this.parentIsRoot = true;
        }
        else {
            this.parentIsRoot = false;
        }
        this.openModule(null);
    };
    /**
     * Nodeを削除する
     */
    TreeList2Component.prototype.deleteNode = function (e) {
        var _this = this;
        //キャンセル
        if (String(e) == "delCancle") {
            return;
            //削除を確定する場合
        }
        else {
            if (String(e) == "delAndMove") {
                this.treeList2Service.delOrMoveNodeInfo(this.selNodeId, "move").then(function (res) {
                    _this.setIndexTree();
                    _this.setRootDetailInit();
                });
            }
            else {
                //削除サービスを呼び出し
                this.treeList2Service.delOrMoveNodeInfo(this.selNodeId, "all").then(function (res) {
                    _this.setIndexTree();
                    _this.setRootDetailInit();
                });
            }
        }
    };
    /**
     * nodeを追加する
     */
    TreeList2Component.prototype.addNode = function () {
        var treeMdlel = this.treeList.tree.toTreeModel().children;
        // Remove hidden node of the root
        if (this.selNodeId == "0") {
            var hiddenNodeController = this.treeList.getControllerByNodeId(this.hiddenNodeId);
            if (hiddenNodeController != null) {
                hiddenNodeController.remove();
            }
        }
        //node 追加
        var oopNodeController = this.treeList.getControllerByNodeId(this.selNodeId);
        var newNodeId = this.setNodeID();
        var newNode = {
            value: 'New Index',
            id: newNodeId,
            children: [],
            settings: {
                'static': false,
                'rightMenu': false,
                'leftMenu': false,
                'isCollapsedOnInit': false,
                'cssClasses': {
                    'leaf': 'weko-node-leaf',
                    'empty': 'weko-node-empty'
                }
            }
        };
        oopNodeController.addChild(newNode);
        // node info
        var nodeJson = {
            'id': newNodeId,
            'value': newNode.value
        };
        //サービスを呼び出し
        this.updateTreeToApi(oopNodeController.tree.node.id, nodeJson);
    };
    /**
   * Nodeを選択する
   */
    TreeList2Component.prototype.seleNode = function (e) {
        var _this = this;
        //選択したNodeIdを格納する
        this.selNodeId = e.node.id;
        if (this.journalFlg == "0") {
            this.uploadFlg = false;
            this.checkFlg = false;
            if (this.selNodeId != "0") {
                this.inputFlg = true;
                var modTreeDetailUrl = document.getElementById('mod_tree_detail').innerText + this.selNodeId;
                this.treeList2Service.getNodeInfo(modTreeDetailUrl).then(function (res) {
                    _this.detailData = res;
                    if (_this.detailData.image_name != "") {
                        var urlArr = window.location.href.split('/');
                        _this.imgSrc = urlArr[0] + "//" + urlArr[2] + _this.detailData.image_name;
                        _this.privousUploadFlg = true;
                    }
                    else {
                        _this.privousUploadFlg = false;
                    }
                });
            }
            else {
                this.setRootDetailInit();
            }
        }
    };
    /**
     * root index detail
     */
    TreeList2Component.prototype.setRootDetailInit = function () {
        this.inputFlg = false;
        this.detailData.index_name = "Root Index";
        this.detailData.index_name_english = "Root Index";
        this.detailData.comment = "";
    };
    /**
     * 日付でNodeIDを設定する
     */
    TreeList2Component.prototype.setNodeID = function () {
        var timestamp = new Date().getTime().toString();
        return timestamp;
    };
    /**
     * サービスインデックス編集画面の送信ボタン
     */
    TreeList2Component.prototype.sendingdetail = function () {
        var _this = this;
        //ツリー詳細を編集＞サービスを呼び出す
        this.checkFlg = this.inputCheck();
        if (this.checkFlg) {
            alert("必須入力項目を入力してください");
            return;
        }
        if (!this.moreCheck()) {
            alert("Invalid display number of index.");
            return;
        }
        this.detailData.index_name = this.detailData.index_name.replace(/(^\s*)|(\s*$)/g, "");
        if (this.detailData.index_name == "") {
            this.detailData.index_name = null;
        }
        if (this.uploadFlg) {
            this.treeList2Service.upload(this.formData, this.selNodeId).then(function (res) {
                _this.detailData.image_name = res.data.path;
                var urlArr = window.location.href.split('/');
                _this.imgSrc = urlArr[0] + "//" + urlArr[2] + res.data.path;
                _this.privousUploadFlg = true;
                _this.treeList2Service.setNodeInfo(_this.selNodeId, _this.detailData).then(function (res) {
                    console.log(JSON.stringify(res));
                    alert(res.message);
                    _this.setIndexTree();
                });
            }).catch();
        }
        else {
            this.treeList2Service.setNodeInfo(this.selNodeId, this.detailData).then(function (res) {
                console.log(JSON.stringify(res));
                alert(res.message);
                _this.setIndexTree();
            });
        }
    };
    /**
     *最新なのindexTreeをAPIへ送る
     @param val:更新フラグ　0:追加 1:削除
     */
    TreeList2Component.prototype.updateTreeToApi = function (parentId, treeJson) {
        var _this = this;
        //サービスを呼び出し
        this.treeList2Service.setTreeInfo(parentId, treeJson).then(function (res) {
            _this.setIndexTree();
        }).catch(function (res) {
            alert(res.message);
        });
    };
    /**
     * modal画面を表示する
     * @param event
     */
    TreeList2Component.prototype.openModule = function (event) {
        this.modalStatus.status = 'table-cell';
    };
    /**
     * set Browsing role allow
     */
    TreeList2Component.prototype.setBrowsingDenyToAllow = function (val) {
        var roleArr = val;
        for (var _i = 0, roleArr_1 = roleArr; _i < roleArr_1.length; _i++) {
            var obj = roleArr_1[_i];
            var sub = { id: "", name: "" };
            sub.id = this.detailData.browsing_role.deny[obj].id;
            sub.name = this.detailData.browsing_role.deny[obj].name;
            this.detailData.browsing_role.allow.push(sub);
        }
        for (var i = roleArr.length - 1; i >= 0; i--) {
            this.detailData.browsing_role.deny.splice(roleArr[i], 1);
        }
        this.roleModel.browsing_role_unable = [];
    };
    /**
     * set Browsing role deny
     */
    TreeList2Component.prototype.setBrowsingAllowToDeny = function (val) {
        var roleArr = val;
        for (var _i = 0, roleArr_2 = roleArr; _i < roleArr_2.length; _i++) {
            var obj = roleArr_2[_i];
            var sub = { id: "", name: "" };
            sub.id = this.detailData.browsing_role.allow[obj].id;
            sub.name = this.detailData.browsing_role.allow[obj].name;
            this.detailData.browsing_role.deny.push(sub);
        }
        for (var i = roleArr.length - 1; i >= 0; i--) {
            this.detailData.browsing_role.allow.splice(roleArr[i], 1);
        }
        this.roleModel.browsing_role_able = [];
    };
    /**
     * set Contribute role deny
     */
    TreeList2Component.prototype.setContributeAllowToDeny = function (val) {
        var roleArr = val;
        for (var _i = 0, roleArr_3 = roleArr; _i < roleArr_3.length; _i++) {
            var obj = roleArr_3[_i];
            var sub = { id: "", name: "" };
            sub.id = this.detailData.contribute_role.allow[obj].id;
            sub.name = this.detailData.contribute_role.allow[obj].name;
            this.detailData.contribute_role.deny.push(sub);
        }
        for (var i = roleArr.length - 1; i >= 0; i--) {
            this.detailData.contribute_role.allow.splice(roleArr[i], 1);
        }
        this.roleModel.contribute_role_able = [];
    };
    /**
     * set Contribute role allow
     */
    TreeList2Component.prototype.setContributeDenyToAllow = function (val) {
        var roleArr = val;
        for (var _i = 0, roleArr_4 = roleArr; _i < roleArr_4.length; _i++) {
            var obj = roleArr_4[_i];
            var sub = { id: "", name: "" };
            sub.id = this.detailData.contribute_role.deny[obj].id;
            sub.name = this.detailData.contribute_role.deny[obj].name;
            this.detailData.contribute_role.allow.push(sub);
        }
        for (var i = roleArr.length - 1; i >= 0; i--) {
            this.detailData.contribute_role.deny.splice(roleArr[i], 1);
        }
        this.roleModel.contribute_role_unable = [];
    };
    // 20180925 add start
    /**
   * set Browsing group allow
   */
    TreeList2Component.prototype.setBrowsingGroupDenyToAllow = function (val) {
        var groupArr = val;
        for (var _i = 0, groupArr_1 = groupArr; _i < groupArr_1.length; _i++) {
            var obj = groupArr_1[_i];
            var sub = { id: "", name: "" };
            sub.id = this.detailData.browsing_group.deny[obj].id;
            sub.name = this.detailData.browsing_group.deny[obj].name;
            this.detailData.browsing_group.allow.push(sub);
        }
        for (var i = groupArr.length - 1; i >= 0; i--) {
            this.detailData.browsing_group.deny.splice(groupArr[i], 1);
        }
        this.groupModel.browsing_group_unable = [];
    };
    /**
     * set Browsing group deny
     */
    TreeList2Component.prototype.setBrowsingGroupAllowToDeny = function (val) {
        var groupArr = val;
        for (var _i = 0, groupArr_2 = groupArr; _i < groupArr_2.length; _i++) {
            var obj = groupArr_2[_i];
            var sub = { id: "", name: "" };
            sub.id = this.detailData.browsing_group.allow[obj].id;
            sub.name = this.detailData.browsing_group.allow[obj].name;
            this.detailData.browsing_group.deny.push(sub);
        }
        for (var i = groupArr.length - 1; i >= 0; i--) {
            this.detailData.browsing_group.allow.splice(groupArr[i], 1);
        }
        this.groupModel.browsing_group_able = [];
    };
    /**
     * set Contribute group deny
     */
    TreeList2Component.prototype.setContributeGroupAllowToDeny = function (val) {
        var groupArr = val;
        for (var _i = 0, groupArr_3 = groupArr; _i < groupArr_3.length; _i++) {
            var obj = groupArr_3[_i];
            var sub = { id: "", name: "" };
            sub.id = this.detailData.contribute_group.allow[obj].id;
            sub.name = this.detailData.contribute_group.allow[obj].name;
            this.detailData.contribute_group.deny.push(sub);
        }
        for (var i = groupArr.length - 1; i >= 0; i--) {
            this.detailData.contribute_group.allow.splice(groupArr[i], 1);
        }
        this.groupModel.contribute_group_able = [];
    };
    /**
     * set Contribute group allow
     */
    TreeList2Component.prototype.setContributeGroupDenyToAllow = function (val) {
        var groupArr = val;
        for (var _i = 0, groupArr_4 = groupArr; _i < groupArr_4.length; _i++) {
            var obj = groupArr_4[_i];
            var sub = { id: "", name: "" };
            sub.id = this.detailData.contribute_group.deny[obj].id;
            sub.name = this.detailData.contribute_group.deny[obj].name;
            this.detailData.contribute_group.allow.push(sub);
        }
        for (var i = groupArr.length - 1; i >= 0; i--) {
            this.detailData.contribute_group.deny.splice(groupArr[i], 1);
        }
        this.groupModel.contribute_group_unable = [];
    };
    // 20180925 add end
    /**
     * node
     */
    TreeList2Component.prototype.handleMoved = function (e) {
        var _this = this;
        // moved Node id
        var nodeId = e.node.id;
        // moved parent Node id
        var parentId = e.node.parent.id;
        var pre_parentId = e.previousParent.id;
        // new position
        var position = e.node.positionInParent;
        // moved info
        var infoJson = {
            pre_parent: pre_parentId,
            parent: parentId,
            position: position
        };
        this.treeList2Service.setNodeMoved(nodeId, infoJson).then(function (res) {
            _this.setIndexTree();
        }).catch(function (res) {
        });
    };
    TreeList2Component.prototype.fileChange = function (event) {
        // this.detailData.image_name = "";
        var fileList = event.target.files;
        if (fileList.length > 0) {
            var file = fileList[0];
            this.formData = new FormData();
            this.detailData.image_name = file.name;
            var str = this.selNodeId + file.name;
            this.formData.append('uploadFile', file, str);
            this.uploadFlg = true;
            this.privousUploadFlg = false;
        }
        else {
            this.detailData.image_name = "";
            this.uploadFlg = false;
        }
    };
    /**
     * 入力チェック
     */
    TreeList2Component.prototype.inputCheck = function () {
        var str = this.detailData.index_name_english;
        str = str.replace(/(^\s*)|(\s*$)/g, "");
        if (str == "") {
            return true;
        }
        else {
            return false;
        }
    };
    /**
     * Display Number Check
     */
    TreeList2Component.prototype.moreCheck = function () {
        if (this.detailData.more_check) {
            if (this.detailData.display_no == null ||
                isNaN(this.detailData.display_no) ||
                this.detailData.display_no <= 0) {
                return false;
            }
        }
        return true;
    };
    __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["ViewChild"])('treeList'),
        __metadata("design:type", Object)
    ], TreeList2Component.prototype, "treeList", void 0);
    __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Input"])(),
        __metadata("design:type", String)
    ], TreeList2Component.prototype, "templflg", void 0);
    __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Input"])(),
        __metadata("design:type", String)
    ], TreeList2Component.prototype, "journalFlg", void 0);
    TreeList2Component = __decorate([
        Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["Component"])({
            selector: 'app-tree-list2',
            template: __webpack_require__("../../../../../src/app/tree-list2/tree-list2.component.html"),
            styles: [__webpack_require__("../../../../../src/app/tree-list2/tree-list2.component.css")],
            providers: [__WEBPACK_IMPORTED_MODULE_1__tree_list2_service__["a" /* TreeList2Service */]]
        }),
        __metadata("design:paramtypes", [__WEBPACK_IMPORTED_MODULE_1__tree_list2_service__["a" /* TreeList2Service */]])
    ], TreeList2Component);
    return TreeList2Component;
}());



/***/ }),

/***/ "../../../../../src/environments/environment.ts":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
/* harmony export (binding) */ __webpack_require__.d(__webpack_exports__, "a", function() { return environment; });
// The file contents for the current environment will overwrite these during build.
// The build system defaults to the dev environment which uses `environment.ts`, but if you do
// `ng build --env=prod` then `environment.prod.ts` will be used instead.
// The list of which env maps to which file can be found in `.angular-cli.json`.
var environment = {
    production: false
};


/***/ }),

/***/ "../../../../../src/main.ts":
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
Object.defineProperty(__webpack_exports__, "__esModule", { value: true });
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_0__angular_core__ = __webpack_require__("../../../core/esm5/core.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_1__angular_platform_browser_dynamic__ = __webpack_require__("../../../platform-browser-dynamic/esm5/platform-browser-dynamic.js");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_2__app_app_module__ = __webpack_require__("../../../../../src/app/app.module.ts");
/* harmony import */ var __WEBPACK_IMPORTED_MODULE_3__environments_environment__ = __webpack_require__("../../../../../src/environments/environment.ts");




if (__WEBPACK_IMPORTED_MODULE_3__environments_environment__["a" /* environment */].production) {
    Object(__WEBPACK_IMPORTED_MODULE_0__angular_core__["enableProdMode"])();
}
Object(__WEBPACK_IMPORTED_MODULE_1__angular_platform_browser_dynamic__["a" /* platformBrowserDynamic */])().bootstrapModule(__WEBPACK_IMPORTED_MODULE_2__app_app_module__["a" /* AppModule */])
    .catch(function (err) { return console.log(err); });


/***/ }),

/***/ 0:
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__("../../../../../src/main.ts");


/***/ })

},[0]);
//# sourceMappingURL=main.bundle.js.map