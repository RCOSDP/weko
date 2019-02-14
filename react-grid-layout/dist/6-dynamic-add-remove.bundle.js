/******/ (function(modules) { // webpackBootstrap
/******/ 	// install a JSONP callback for chunk loading
/******/ 	function webpackJsonpCallback(data) {
/******/ 		var chunkIds = data[0];
/******/ 		var moreModules = data[1];
/******/ 		var executeModules = data[2];
/******/
/******/ 		// add "moreModules" to the modules object,
/******/ 		// then flag all "chunkIds" as loaded and fire callback
/******/ 		var moduleId, chunkId, i = 0, resolves = [];
/******/ 		for(;i < chunkIds.length; i++) {
/******/ 			chunkId = chunkIds[i];
/******/ 			if(installedChunks[chunkId]) {
/******/ 				resolves.push(installedChunks[chunkId][0]);
/******/ 			}
/******/ 			installedChunks[chunkId] = 0;
/******/ 		}
/******/ 		for(moduleId in moreModules) {
/******/ 			if(Object.prototype.hasOwnProperty.call(moreModules, moduleId)) {
/******/ 				modules[moduleId] = moreModules[moduleId];
/******/ 			}
/******/ 		}
/******/ 		if(parentJsonpFunction) parentJsonpFunction(data);
/******/
/******/ 		while(resolves.length) {
/******/ 			resolves.shift()();
/******/ 		}
/******/
/******/ 		// add entry modules from loaded chunk to deferred list
/******/ 		deferredModules.push.apply(deferredModules, executeModules || []);
/******/
/******/ 		// run deferred modules when all chunks ready
/******/ 		return checkDeferredModules();
/******/ 	};
/******/ 	function checkDeferredModules() {
/******/ 		var result;
/******/ 		for(var i = 0; i < deferredModules.length; i++) {
/******/ 			var deferredModule = deferredModules[i];
/******/ 			var fulfilled = true;
/******/ 			for(var j = 1; j < deferredModule.length; j++) {
/******/ 				var depId = deferredModule[j];
/******/ 				if(installedChunks[depId] !== 0) fulfilled = false;
/******/ 			}
/******/ 			if(fulfilled) {
/******/ 				deferredModules.splice(i--, 1);
/******/ 				result = __webpack_require__(__webpack_require__.s = deferredModule[0]);
/******/ 			}
/******/ 		}
/******/ 		return result;
/******/ 	}
/******/
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// object to store loaded and loading chunks
/******/ 	// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 	// Promise = chunk loading, 0 = chunk loaded
/******/ 	var installedChunks = {
/******/ 		"6-dynamic-add-remove": 0
/******/ 	};
/******/
/******/ 	var deferredModules = [];
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, { enumerable: true, get: getter });
/******/ 		}
/******/ 	};
/******/
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = function(exports) {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 8|1: behave like require
/******/ 	__webpack_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = __webpack_require__(value);
/******/ 		if(mode & 8) return value;
/******/ 		if((mode & 4) && typeof value === 'object' && value && value.__esModule) return value;
/******/ 		var ns = Object.create(null);
/******/ 		__webpack_require__.r(ns);
/******/ 		Object.defineProperty(ns, 'default', { enumerable: true, value: value });
/******/ 		if(mode & 2 && typeof value != 'string') for(var key in value) __webpack_require__.d(ns, key, function(key) { return value[key]; }.bind(null, key));
/******/ 		return ns;
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	var jsonpArray = window["webpackJsonp"] = window["webpackJsonp"] || [];
/******/ 	var oldJsonpFunction = jsonpArray.push.bind(jsonpArray);
/******/ 	jsonpArray.push = webpackJsonpCallback;
/******/ 	jsonpArray = jsonpArray.slice();
/******/ 	for(var i = 0; i < jsonpArray.length; i++) webpackJsonpCallback(jsonpArray[i]);
/******/ 	var parentJsonpFunction = oldJsonpFunction;
/******/
/******/
/******/ 	// add entry module to deferred list
/******/ 	deferredModules.push(["./test/examples/6-dynamic-add-remove.jsx","commons"]);
/******/ 	// run deferred modules when ready
/******/ 	return checkDeferredModules();
/******/ })
/************************************************************************/
/******/ ({

/***/ "./test/examples/6-dynamic-add-remove.jsx":
/*!************************************************!*\
  !*** ./test/examples/6-dynamic-add-remove.jsx ***!
  \************************************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

"use strict";
eval("/* WEBPACK VAR INJECTION */(function(module) {\n\nvar _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; };\n\nvar _jsx = function () { var REACT_ELEMENT_TYPE = typeof Symbol === \"function\" && Symbol.for && Symbol.for(\"react.element\") || 0xeac7; return function createRawReactElement(type, props, key, children) { var defaultProps = type && type.defaultProps; var childrenLength = arguments.length - 3; if (!props && childrenLength !== 0) { props = {}; } if (props && defaultProps) { for (var propName in defaultProps) { if (props[propName] === void 0) { props[propName] = defaultProps[propName]; } } } else if (!props) { props = defaultProps || {}; } if (childrenLength === 1) { props.children = children; } else if (childrenLength > 1) { var childArray = Array(childrenLength); for (var i = 0; i < childrenLength; i++) { childArray[i] = arguments[i + 3]; } props.children = childArray; } return { $$typeof: REACT_ELEMENT_TYPE, type: type, key: key === undefined ? null : '' + key, ref: null, props: props, _owner: null }; }; }();\n\nvar _react = __webpack_require__(/*! react */ \"./node_modules/react/index.js\");\n\nvar _react2 = _interopRequireDefault(_react);\n\nvar _reactGridLayout = __webpack_require__(/*! react-grid-layout */ \"./index-dev.js\");\n\nvar _lodash = __webpack_require__(/*! lodash */ \"./node_modules/lodash/lodash.js\");\n\nvar _lodash2 = _interopRequireDefault(_lodash);\n\nfunction _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }\n\nfunction _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError(\"Cannot call a class as a function\"); } }\n\nfunction _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError(\"this hasn't been initialised - super() hasn't been called\"); } return call && (typeof call === \"object\" || typeof call === \"function\") ? call : self; }\n\nfunction _inherits(subClass, superClass) { if (typeof superClass !== \"function\" && superClass !== null) { throw new TypeError(\"Super expression must either be null or a function, not \" + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }\n\nvar ResponsiveReactGridLayout = (0, _reactGridLayout.WidthProvider)(_reactGridLayout.Responsive);\n\n/**\n * This layout demonstrates how to use a grid with a dynamic number of elements.\n */\n\nvar AddRemoveLayout = function (_React$PureComponent) {\n  _inherits(AddRemoveLayout, _React$PureComponent);\n\n  function AddRemoveLayout(props) {\n    _classCallCheck(this, AddRemoveLayout);\n\n    var _this = _possibleConstructorReturn(this, _React$PureComponent.call(this, props));\n\n    _this.state = {\n      items: [0, 1, 2, 3, 4].map(function (i, key, list) {\n        return {\n          i: i.toString(),\n          x: i * 2,\n          y: 0,\n          w: 2,\n          h: 2,\n          add: i === (list.length - 1).toString()\n        };\n      }),\n      newCounter: 0\n    };\n\n    _this.onAddItem = _this.onAddItem.bind(_this);\n    _this.onBreakpointChange = _this.onBreakpointChange.bind(_this);\n    return _this;\n  }\n\n  AddRemoveLayout.prototype.createElement = function createElement(el) {\n    var removeStyle = {\n      position: \"absolute\",\n      right: \"2px\",\n      top: 0,\n      cursor: \"pointer\"\n    };\n    var i = el.add ? \"+\" : el.i;\n    return _jsx(\"div\", {\n      \"data-grid\": el\n    }, i, el.add ? _jsx(\"span\", {\n      className: \"add text\",\n      onClick: this.onAddItem,\n      title: \"You can add an item by clicking here, too.\"\n    }, void 0, \"Add +\") : _jsx(\"span\", {\n      className: \"text\"\n    }, void 0, i), _jsx(\"span\", {\n      className: \"remove\",\n      style: removeStyle,\n      onClick: this.onRemoveItem.bind(this, i)\n    }, void 0, \"x\"));\n  };\n\n  AddRemoveLayout.prototype.onAddItem = function onAddItem() {\n    /*eslint no-console: 0*/\n    console.log(\"adding\", \"n\" + this.state.newCounter);\n    this.setState({\n      // Add a new item. It must have a unique key!\n      items: this.state.items.concat({\n        i: \"n\" + this.state.newCounter,\n        x: this.state.items.length * 2 % (this.state.cols || 12),\n        y: Infinity, // puts it at the bottom\n        w: 2,\n        h: 2\n      }),\n      // Increment the counter to ensure key is always unique.\n      newCounter: this.state.newCounter + 1\n    });\n  };\n\n  // We're using the cols coming back from this to calculate where to add new items.\n\n\n  AddRemoveLayout.prototype.onBreakpointChange = function onBreakpointChange(breakpoint, cols) {\n    this.setState({\n      breakpoint: breakpoint,\n      cols: cols\n    });\n  };\n\n  AddRemoveLayout.prototype.onLayoutChange = function onLayoutChange(layout) {\n    this.props.onLayoutChange(layout);\n    this.setState({ layout: layout });\n  };\n\n  AddRemoveLayout.prototype.onRemoveItem = function onRemoveItem(i) {\n    console.log(\"removing\", i);\n    this.setState({ items: _lodash2.default.reject(this.state.items, { i: i }) });\n  };\n\n  AddRemoveLayout.prototype.render = function render() {\n    var _this2 = this;\n\n    return _jsx(\"div\", {}, void 0, _jsx(\"button\", {\n      onClick: this.onAddItem\n    }, void 0, \"Add Item\"), _react2.default.createElement(\n      ResponsiveReactGridLayout,\n      _extends({\n        onLayoutChange: this.onLayoutChange,\n        onBreakpointChange: this.onBreakpointChange\n      }, this.props),\n      _lodash2.default.map(this.state.items, function (el) {\n        return _this2.createElement(el);\n      })\n    ));\n  };\n\n  return AddRemoveLayout;\n}(_react2.default.PureComponent);\n\nAddRemoveLayout.defaultProps = {\n  className: \"layout\",\n  cols: { lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 },\n  rowHeight: 100\n};\n\n\nmodule.exports = AddRemoveLayout;\n\nif (__webpack_require__.c[__webpack_require__.s] === module) {\n  __webpack_require__(/*! ../test-hook.jsx */ \"./test/test-hook.jsx\")(module.exports);\n}\n/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(/*! ./../../node_modules/webpack/buildin/module.js */ \"./node_modules/webpack/buildin/module.js\")(module)))\n\n//# sourceURL=webpack:///./test/examples/6-dynamic-add-remove.jsx?");

/***/ })

/******/ });