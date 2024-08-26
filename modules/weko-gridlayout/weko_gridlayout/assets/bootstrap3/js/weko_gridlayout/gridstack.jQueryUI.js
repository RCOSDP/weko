/**
 * gridstack.js 0.2.7-dev
 * http://troolee.github.io/gridstack.js/
 * (c) 2014-2016 Pavel Reznikov, Dylan Weiss
 * gridstack.js may be freely distributed under the MIT license.
 * @preserve
*/
import jQuery from "jquery";
import _ from 'lodash';
import GridStackUI from './gridstack';
import "jquery-ui/ui/data";
import "jquery-ui/ui/disable-selection";
import "jquery-ui/ui/focusable";
import "jquery-ui/ui/keycode";
import "jquery-ui/ui/labels";
import "jquery-ui/ui/plugin";
import "jquery-ui/ui/scroll-parent";
import "jquery-ui/ui/tabbable";
import "jquery-ui/ui/unique-id";
import "jquery-ui/ui/version";
import "jquery-ui/ui/widget";
import "jquery-ui/ui/widgets/mouse";
import "jquery-ui/ui/widgets/draggable";
import "jquery-ui/ui/widgets/droppable";
import "jquery-ui/ui/widgets/resizable";

(function(a, b, c) {
    /**
     * @class JQueryUIGridStackDragDropPlugin
     * jQuery UI implementation of drag'n'drop gridstack plugin.
     */
    function d(a) {
        c.GridStackDragDropPlugin.call(this, a);
    }
    void window;
    return c.GridStackDragDropPlugin.registerPlugin(d),
        d.prototype = Object.create(c.GridStackDragDropPlugin.prototype),
        d.prototype.constructor = d,
        d.prototype.resizable = function(c, d) {
            if (c = a(c), "disable" === d || "enable" === d) {
                c.resizable(d);
            } else if ("option" === d) {
                var e = arguments[2], f = arguments[3];
                c.resizable(d, e, f);
            } else {
                c.resizable(b.extend({}, this.grid.opts.resizable, {
                    start: d.start || function() {},
                    stop: d.stop || function() {},
                    resize: d.resize || function() {}
                }));
            }
            return this;
        },
        d.prototype.draggable = function(c, d) {
            return c = a(c), "disable" === d || "enable" === d ? c.draggable(d) : c.draggable(b.extend({}, this.grid.opts.draggable, {
                containment: this.grid.opts.isNested ? this.grid.container.parent() : null,
                start: d.start || function() {},
                stop: d.stop || function() {},
                drag: d.drag || function() {}
            })), this;
        },
        d.prototype.droppable = function(b, c) {
            return b = a(b), "disable" === c || "enable" === c ? b.droppable(c) : b.droppable({
                accept: c.accept
            }), this;
        },
        d.prototype.isDroppable = function(b, c) {
            return b = a(b), Boolean(b.data("droppable"));
        },
        d.prototype.on = function(b, c, d) {
            return a(b).on(c, d), this;
        },
        d
})(jQuery, _, GridStackUI);
//# sourceMappingURL=gridstack.min.map