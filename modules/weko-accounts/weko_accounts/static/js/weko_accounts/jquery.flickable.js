/*
 * jQuery.flickable v1.0b3
 *
 * Copyright (c) 2010 lagos
 * Dual licensed under the MIT and GPL licenses.
 *
 * http://lagoscript.org
 */
(function(h, r, j, q) {
    function t(a) {
        return h("script", a).map(function(d, b) {
            var c = h(b).attr("type");
            return !c || c.toLowerCase() === "text/javascript" ? b : null
        })
    }
    var s, u = r.document, y = /iphone|ipod|ipad|android|blackberry/, z = /android/.test(navigator.userAgent.toLowerCase()), v = /^(input|textarea|select|option|button|embed|object)$/, A = RegExp("^(input|textarea|select|option|button|embed|object|a" + (z ? "" : "|img") + ")$");
    h.fn.flickable = s = function(a) {
        if (typeof a === "string") {
            var d = Array.prototype.slice.call(arguments, 1)
              , b = this;
            this.each(function() {
                var c = h.data(this, "flickable")
                  , e = c && h.isFunction(c[a]) ? c[a].apply(c, d) : c;
                if (e !== c && e !== q) {
                    b = e;
                    return false
                }
            });
            return b
        } else
            return this.each(function() {
                var c = h.data(this, "flickable");
                if (c) {
                    h.extend(true, c.options, a);
                    c.init()
                } else
                    h.data(this, "flickable", new s.prototype.create(a,this))
            })
    }
    ;
    s.prototype = {
        options: {
            cancel: null,
            disabled: false,
            elasticConstant: 0.16,
            friction: 0.96,
            section: null
        },
        canceled: false,
        noPadding: false,
        layoutStyles: ["background-color", "background-repeat", "background-attachment", "background-position", "background-image", "padding-top", "padding-right", "padding-bottom", "padding-left"],
        create: function(a, d) {
            var b = this
              , c = h(d);
            this.originalElement = c;
            this.options = h.extend(true, {}, this.options, a);
            this.layoutStyles = h.extend([], this.layoutStyles);
            this.client = {
                x: 0,
                y: 0
            };
            this.inertialVelocity = {
                x: 0,
                y: 0
            };
            this.remainder = {
                x: 0,
                y: 0
            };
            this.hasScroll = {
                x: false,
                y: false
            };
            this.padding = {};
            this.stretchPosition = {};
            this.sectionPostions = [];
            this.preventDefaultClick = false;
            if (d == r || d == u || /^(html|body)$/i.test(d.nodeName)) {
                if (y.test(navigator.userAgent.toLowerCase()))
                    return;
                this.box = h(r);
                this.elementWrapper = h("html");
                this.element = h("body");
                this.position = this.positionWindow;
                this.scroll = this.scrollWindow;
                this.layoutStyles.push("width");
                h.each(["top", "right", "bottom", "left"], function(e, g) {
                    b.layoutStyles.push(["margin", g].join("-"));
                    h.each(["color", "width", "style"], function(f, i) {
                        b.layoutStyles.push(["border", g, i].join("-"))
                    })
                })
            } else
                this.box = this.elementWrapper = this.element = c;
            this.init()
        },
        init: function() {
            var a = this, d, b = this.element;
            if (!this.container) {
                d = t(b).attr("type", "text/plain");
                b.addClass("ui-flickable").append('<div style="clear:both;"/>').wrapInner('<div class="ui-flickable-container"><div class="ui-flickable-wrapper" style="padding:1px;"><div class="ui-flickable-content" style="position:relative;"/></div></div>');
                d.attr("type", "text/javascript");
                this.container = b.children().bind("touchstart.flickable mousedown.flickable", function(c) {
                    return a.dragStart(c)
                }).bind("click.flickable", function(c) {
                    return a.clickHandler(c)
                });
                this.wrapper = this.container.children();
                this.content = this.wrapper.children();
                this.elementWrapper.bind("touchstart.flickable mousedown.flickable keydown.flickable", function() {
                    a.deactivate()
                }).bind("touchend.flickable mouseup.flickable mouseleave.flickable keyup.flickable", function() {
                    a.activate()
                });
                b.data("style.flickable", b.attr("style"));
                h.each(this.layoutStyles, function(c, e) {
                    var g = b.css(e);
                    a.content.css(e, g);
                    if (e === "background-color")
                        a.wrapper.css(e, h.inArray(g, ["transparent", "rgba(0, 0, 0, 0)"]) >= 0 ? "#FFF" : g);
                    else if (e === "width")
                        b.css(e, "auto");
                    else if (/^(padding-\w+|margin-\w+|border-\w+-width)$/.test(e))
                        b.css(e, 0);
                    else
                        /^(background-image|border-\w+-style)$/.test(e) && b.css(e, "none")
                });
                if (h.nodeName(b[0], "body"))
                    this.box.bind("resize.flickable", function() {
                        setTimeout(function() {
                            !a.options.disabled && a.refresh()
                        }, 0)
                    });
                else
                    b.css("position") === "static" && b.css("position", "relative");
                h(r).bind("unload.flickable", function() {
                    a.disable()
                })
            }
            this.option(this.options);
            this.activate()
        },
        option: function(a, d) {
            var b = this
              , c = a;
            if (arguments.length === 0)
                return h.extend({}, this.options);
            if (typeof a === "string") {
                if (d === q)
                    return this.options[a];
                c = {};
                c[a] = d
            }
            h.each(c, function(e, g) {
                b.setOption(e, g)
            });
            return this
        },
        setOption: function(a, d) {
            var b = this
              , c = false;
            this.options[a] = d;
            switch (a) {
            case "cancel":
                this.cancel && this.cancel.removeClass("ui-flickable-canceled").unbind(".flickable");
                this.cancel = h("div", this.content).map(function(e, g) {
                    var f;
                    f = g;
                    f = h(f);
                    f = h.inArray(f.css("overflow"), ["scroll", "auto"]) >= 0 ? f.attr("scrollWidth") > f.attr("clientWidth") || f.attr("scrollHeight") > f.attr("clientHeight") : false;
                    return f ? g : null
                }).add(h("iframe,textarea,select", this.content));
                if (d)
                    this.cancel = this.cancel.add(h(d, this.content));
                this.cancel.addClass("ui-flickable-canceled").bind("touchstart.flickable mouseenter.flickable", function() {
                    b.canceled = true
                }).bind("touchend.flickable mouseleave.flickable", function() {
                    b.canceled = false
                });
                break;
            case "disabled":
                this.element[d ? "addClass" : "removeClass"]("ui-flickable-disabled");
                if (!d)
                    this.selected = q;
                c = true;
                this.noPadding = d;
                break;
            case "section":
                this.sections = null;
                if (d) {
                    this.sections = h(d, this.content);
                    c = true
                }
                break
            }
            c && this.refresh();
            return this
        },
        destroy: function() {
            var a;
            this.noPadding = true;
            this.refresh();
            this.element.attr("style", this.element.data("style.flickable") || null).removeClass("ui-flickable ui-flickable-disabled").removeData("style.flickable");
            this.elementWrapper.unbind(".flickable");
            this.box.unbind(".flickable");
            this.cancel.unbind(".flickable").removeClass("ui-flickable-canceled");
            h(r).unbind(".flickable");
            a = t(this.content).attr("type", "text/plain");
            this.content.add(this.wrapper).add(this.container).replaceWith(this.content.children());
            a.attr("type", "text/javascript");
            this.container = this.content = this.wrapper = this.cancel = this.selected = q;
            return this
        },
        enable: function() {
            return this.setOption("disabled", false)
        },
        disable: function() {
            return this.setOption("disabled", true)
        },
        trigger: function(a, d, b) {
            var c = this.options[a];
            d = h.Event(d);
            d.type = (a === "flick" ? a : "flick" + a).toLowerCase();
            b = b || {};
            if (d.originalEvent) {
                a = h.event.props.length;
                for (var e; a; ) {
                    e = h.event.props[--a];
                    d[e] = d.originalEvent[e]
                }
            }
            this.originalElement.trigger(d, b);
            return !(c && c.call(this.element[0], d, b) === false || d.isDefaultPrevented())
        },
        refresh: function() {
            var a = this, d = {
                x: 0,
                y: 0
            }, b, c, e, g = this.content, f = this.padding, i = h.extend({}, f), k = u.compatMode === "CSS1Compat" ? this.elementWrapper : this.element, l = {};
            b = g.width();
            g.width("auto");
            e = this.elementWrapper.attr("scrollHeight") - (i.height || 0) * 2;
            c = this.elementWrapper.attr("scrollWidth") - (i.width || 0) * 2;
            if (b > c) {
                g.width(b);
                c = g.outerWidth() + parseInt(g.css("margin-left")) + parseInt(g.css("margin-right"))
            }
            h.each({
                Height: e,
                Width: c
            }, function(m, n) {
                var o = m.toLowerCase();
                l[o] = a.box[o]();
                f[o] = n > k.attr("client" + m) && !a.noPadding ? j.round(l[o] / 2) : 0
            });
            this.container.width(l.width >= c ? "auto" : c).css({
                "padding-top": f.height,
                "padding-bottom": f.height,
                "padding-left": f.width,
                "padding-right": f.width
            });
            c = l.width > c ? l.width : c;
            this.hasScroll.x = this.elementWrapper.attr("scrollWidth") > k.attr("clientWidth");
            this.hasScroll.y = this.elementWrapper.attr("scrollHeight") > k.attr("clientHeight");
            b = this.position(this.wrapper);
            this.stretchPosition = {
                top: b.top,
                bottom: b.top + e - k.attr("clientHeight"),
                left: b.left,
                right: b.left + c - k.attr("clientWidth")
            };
            this.sectionPostions = this.sections ? this.sections.map(function() {
                return a.position(this)
            }).get() : [];
            h.each({
                x: "width",
                y: "height"
            }, function(m, n) {
                d[m] = f[n] - (i[n] || 0)
            });
            this.scroll(d.x, d.y);
            return this
        },
        scroll: function(a, d) {
            var b = this.box;
            a && b.scrollLeft(b.scrollLeft() + a);
            d && b.scrollTop(b.scrollTop() + d);
            return this
        },
        scrollWindow: function(a, d) {
            this.box[0].scrollBy(parseInt(a), parseInt(d));
            return this
        },
        position: function(a) {
            a = h(a).offset();
            var d = this.element.offset();
            return {
                top: j.floor(a.top - d.top + this.box.scrollTop()),
                left: j.floor(a.left - d.left + this.box.scrollLeft())
            }
        },
        positionWindow: function(a) {
            a = h(a).offset();
            return {
                top: j.floor(a.top),
                left: j.floor(a.left)
            }
        },
        activate: function() {
            this.scrollBack();
            return this
        },
        deactivate: function() {
            if (this.isScrolling())
                this.preventDefaultClick = true;
            this.remainder.x = 0;
            this.remainder.y = 0;
            this.inertialVelocity.x = 0;
            this.inertialVelocity.y = 0;
            clearInterval(this.inertia);
            clearInterval(this.back);
            return this
        },
        clickHandler: function(a) {
            if (this.preventDefaultClick) {
                a.preventDefault();
                this.preventDefaultClick = false
            }
        },
        dragStart: function(a) {
            var d = this
              , b = a.type === "touchstart" ? a.originalEvent.touches[0] : a;
            if (!(a.type === "touchstart" && a.originalEvent.touches.length > 1))
                if (!this.canceled && !this.options.disabled) {
                    this.timeStamp = a.timeStamp;
                    h.each(["x", "y"], function(c, e) {
                        d.client[e] = b["client" + e.toUpperCase()];
                        d.inertialVelocity[e] = 0
                    });
                    if (this.trigger("dragStart", a) === false)
                        return false;
                    this.container.unbind("touchstart.flickable mousedown.flickable").bind("touchmove.flickable mousemove.flickable", function(c) {
                        return d.drag(c)
                    }).bind("touchend.flickable mouseup.flickable mouseleave.flickable", function(c) {
                        return d.dragStop(c)
                    });
                    (a.type === "touchstart" ? A : v).test(a.target.nodeName.toLowerCase()) || a.preventDefault()
                }
        },
        drag: function(a) {
            var d = this
              , b = {}
              , c = a.timeStamp - this.timeStamp
              , e = a.type === "touchmove" ? a.originalEvent.touches[0] : a;
            if (!(a.type === "touchmove" && a.originalEvent.touches.length > 1)) {
                if (this.trigger("drag", a) === false)
                    return false;
                h.each(["x", "y"], function(g, f) {
                    var i = e["client" + f.toUpperCase()];
                    b[f] = d.hasScroll[f] && (!d.draggableAxis || d.draggableAxis === f) ? d.client[f] - i : 0;
                    d.client[f] = i;
                    if (c)
                        d.inertialVelocity[f] = b[f] / c
                });
                if (this.sections && !this.draggableAxis) {
                    this.draggableAxis = j.abs(b.x) > j.abs(b.y) ? "x" : "y";
                    b[this.draggableAxis === "x" ? "y" : "x"] = 0
                }
                this.timeStamp = a.timeStamp;
                b = this.velocity(b);
                this.scroll(b.x, b.y);
                v.test(a.target.nodeName.toLowerCase()) || a.preventDefault();
                this.preventDefaultClick = true
            }
        },
        dragStop: function(a) {
            var d = this;
            if (!(a.type === "touchend" && a.originalEvent.touches.length > 1)) {
                if (this.trigger("dragStop", a) === false)
                    return false;
                this.container.unbind(".flickable").bind("touchstart.flickable mousedown.flickable", function(b) {
                    return d.dragStart(b)
                }).bind("click.flickable", function(b) {
                    return d.clickHandler(b)
                });
                this.flick()
            }
        },
        flick: function() {
            var a = this
              , d = this.options
              , b = this.box
              , c = this.inertialVelocity
              , e = d.friction;
            clearInterval(this.inertia);
            h.each(c, function(p, B) {
                if (j.abs(B) < 0.1)
                    c[p] = 0
            });
            if (this.sections) {
                var g, f, i;
                if (this.isScrolling()) {
                    var k, l, m, n, o, w = b.scrollTop(), x = b.scrollLeft();
                    if (j.abs(c.x) > j.abs(c.y)) {
                        i = "x";
                        n = "left";
                        o = "scrollLeft";
                        m = x;
                        c.y = 0
                    } else {
                        i = "y";
                        n = "top";
                        o = "scrollTop";
                        m = w;
                        c.x = 0
                    }
                    k = h.map(this.sectionPostions, function(p) {
                        if (c[i] > 0 && p[n] > m || c[i] < 0 && p[n] < m)
                            return j.abs(p.top - w) + j.abs(p.left - x);
                        return Infinity
                    });
                    l = j.min.apply(j, k);
                    if (l !== Infinity) {
                        g = this.sectionPostions[h.inArray(l, k)][n];
                        f = g - m;
                        e = false
                    }
                }
            }
            c.x *= 13;
            c.y *= 13;
            this.inertia = setInterval(function() {
                if (d.disabled || !a.isScrolling() || a.trigger("flick") === false) {
                    c.x = 0;
                    c.y = 0;
                    clearInterval(a.inertia);
                    a.scrollBack()
                } else {
                    if (g !== q) {
                        var p = b[o]();
                        c[i] = f > 0 && p > g || f < 0 && p < g ? 0 : d.elasticConstant / 4 * f
                    }
                    h.extend(c, a.velocity(c, e));
                    a.scroll(c.x, c.y)
                }
            }, 13);
            return this
        },
        scrollBack: function() {
            var a = this
              , d = this.options
              , b = this.inertialVelocity
              , c = false;
            clearInterval(this.back);
            this.back = setInterval(function() {
                if (!(d.disabled || b.x && b.y)) {
                    var e = {}
                      , g = {};
                    if (a.sections) {
                        var f, i, k, l = a.box.scrollTop(), m = a.box.scrollLeft();
                        f = h.map(a.sectionPostions, function(n) {
                            return j.abs(n.top - l) + j.abs(n.left - m)
                        });
                        i = h.inArray(j.min.apply(j, f), f);
                        f = a.sectionPostions[i];
                        g = {
                            x: a.hasScroll.x ? m - f.left : 0,
                            y: a.hasScroll.y ? l - f.top : 0
                        };
                        if (!g.x && !g.y && !a.isScrolling())
                            k = a.sections.eq(i)
                    } else
                        g = a.stretch();
                    h.each(b, function(n, o) {
                        e[n] = o ? 0 : -1 * d.elasticConstant * g[n]
                    });
                    e = a.velocity(e, false);
                    if (e.x || e.y)
                        c = a.trigger("scrollBack") === false;
                    if (!g.x && !g.y || c) {
                        if (k) {
                            a.draggableAxis = q;
                            if (!a.selected || a.selected[0] != k[0]) {
                                f = {
                                    newSection: k,
                                    oldSection: a.selected
                                };
                                a.selected = h(k[0]);
                                a.trigger("change", null, f)
                            }
                        }
                        clearInterval(a.back)
                    } else
                        a.scroll(e.x, e.y)
                }
            }, 13);
            return this
        },
        select: function(a) {
            var d = this, b = this.box, c = b.scrollLeft(), e = b.scrollTop(), g = this.inertialVelocity, f, i;
            clearInterval(this.back);
            clearInterval(this.inertia);
            f = this.sectionPostions[a];
            i = {
                x: f.left - c,
                y: f.top - e
            };
            this.inertia = setInterval(function() {
                h.each({
                    x: "Left",
                    y: "Top"
                }, function(k, l) {
                    var m = b["scroll" + l]();
                    l = l.toLowerCase();
                    g[k] = i[k] > 0 && m > f[l] || i[k] < 0 && m < f[l] ? 0 : d.options.elasticConstant / 4 * i[k]
                });
                if (d.options.disabled || !d.isScrolling()) {
                    clearInterval(d.inertia);
                    d.scrollBack()
                } else {
                    h.extend(g, d.velocity(g, false));
                    d.scroll(g.x, g.y)
                }
            }, 13);
            return this
        },
        stretch: function() {
            var a = this
              , d = {
                x: 0,
                y: 0
            }
              , b = this.stretchPosition;
            h.each({
                x: ["left", "right", "Left"],
                y: ["top", "bottom", "Top"]
            }, function(c, e) {
                var g;
                if (a.hasScroll[c]) {
                    g = a.box["scroll" + e[2]]();
                    if (g < b[e[0]])
                        d[c] = g - b[e[0]];
                    else if (g > b[e[1]])
                        d[c] = g - b[e[1]]
                }
            });
            return d
        },
        velocity: function(a, d) {
            var b = this
              , c = {}
              , e = {};
            if (d !== false)
                c = this.friction(d);
            h.each(a, function(g, f) {
                f += b.remainder[g] || 0;
                if (c[g] !== q)
                    f *= c[g];
                e[g] = j.round(f);
                b.remainder[g] = f - e[g]
            });
            return e
        },
        friction: function(a) {
            var d = this
              , b = {}
              , c = this.stretch();
            if (a === q)
                a = 1;
            h.each({
                x: "width",
                y: "height"
            }, function(e, g) {
                b[e] = a;
                if (c[e]) {
                    var f = d.padding[g];
                    b[e] *= (f - j.abs(c[e])) / f
                }
            });
            return b
        },
        isScrolling: function() {
            return this.inertialVelocity.x || this.inertialVelocity.y
        }
    };
    s.prototype.create.prototype = s.prototype
}
)(jQuery, window, Math);
