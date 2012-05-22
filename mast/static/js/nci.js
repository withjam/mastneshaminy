(function() {
    /**
     * Adds the lat and long, if available, to a form
    **/
    var geopos = 0;
    var jwin = $(window);
    var jdoc = $(document);
    
    var useCurrentPosition = function(success,error) {
        // if we have geopos just use that
        if (geopos) {
            success(geopos);
            return;
        }
        // otherwise try to get it
        var func = function(pos) {
            // store the returned pos so we don't have to check every call
            geopos = pos;
            // call the given function
            success(pos);
        };
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(success,error);
        } else {
            error();
        }
    };
    
    var modalMask = 0;
    var modalWin = 0;
    var windowH = jwin.height();
    var windowW = jwin.width();
    /**
     * Just creates and returns the modal mask, it's up to the caller to provide
     * the contents and controls
    **/
    var showMask = function() {
        if(!modalMask) {
            modalMask = jQuery('<div id="modalmask"></div>');
            modalMask.css({'z-index':5000,'background-color':'#000','opacity':0.75,'height':'100%','width':windowW,'top':-windowH,'left':0,'position':'fixed'});
            modalMask.appendTo('body');
        }
        modalMask.animate({'top':0});
        return modalMask;
    };
    var hideModal = function(skipAnimation) {
        if(modalMask) {
            if (skipAnimation) {
                modalMask.css({'top':-windowH});
            } else {
                modalMask.animate({'top':-windowH});
            }
        }
        if (skipAnimation) {
            modalWin.remove();
        } else {
            modalWin.animate({'top':-windowH},function() { modalWin.remove(); });
        }
    };
    /**
     *  Make the provided element a modal window
     **/
    var makeModal = function(jele) {
        modalWin = jQuery('<div class="modalwin"></div>').append(jele);
        modalWin.css({'z-index':5001,'position':'fixed','top':-windowH,'left':0}).appendTo('body');
        var w = modalWin.width();
        var h = modalWin.height();
        var l = (windowW - w)/2;
        var t = (windowH - h)/2;
        showMask();
        modalWin.css({'left':l}).animate({'top':t});
    };
    
    /**
     *  Fills in values for lat and lon if navigator supports geolocation
     **/
    var addGeo = function(frm) {
        var lat = frm.find('input:hidden[name="lat"]');
        var lon = frm.find('input:hidden[name="lon"]');
        var setCoords = function(pos) {
            lat.val(pos.coords.latitude);
            lon.val(pos.coords.longitude);
        };
        useCurrentPosition(setCoords,function(){});
    };
    
    /**
     *  Add/remove item functionality in any grid in the form
     **/
    var addFormGrids = function(frm) {
        var grids = frm.find('.inputgrid');
        jQuery.each(grids, function() {
            var grid = $(this);
            var tpl = grid.find('.template:first').remove();
            var adder = grid.find('.icon.add').click(function() { addGridItem(tpl,grid); });
        });
        frm.bind('submit',function() { prepGrids(grids); });
    };
    var prepGrids = function(grids) {
        jQuery.each(grids, function() {
            var g = $(this);
            var rows = g.find('.gridrow');
            var i = 1;
            jQuery.each(rows,function() {
                $(this).find(':visible[name]').dynaAttr('name',i);
                i++;
            });
        });
    };
    /**
     *  Function add a grid item to a grid based on the template
     **/
    var addGridItem = function(tpl,grid) {
        var rows = grid.find('.gridrow').length;
        var n = rows + 1;
        var item = tpl.clone();
        var cnt = grid.find(':hidden.gridcount');
        cnt.val(n);
        item.removeClass('template').addClass('gridrow gridrow'+n);
        item.find('.del').click(function() { item.remove(); cnt.val(rows-1);});
        item.find('input[hint]').hinted();
        grid.append(item);
    
    };
    
    var isBlank = function(str) {
        return (!str || $.trim(str) === '');
    };
    
    var hideHint = function(event) {
        var t = $(event.target);
        var h = t.attr('hint') || '';
        if (h === t.val()) {
            t.val('').removeClass('hinted');
        }
    };
    var showHint = function(event) {
        var t = $(event.target);
        var h = t.attr('hint') || '';
        if (isBlank(t.val())) {
            t.val(h).addClass('hinted');
        }
    };
    
    /**
     *  Share via email
     **/
    var share = function() {
    
    };
    
    /**
     *  capture email
     **/
    var capture = function() {
        var box = $('<section class="mbox"></section>');
        box.append('<p class="heading">Subscribe to our Mailing List</p>');
        box.append('<p class="instruct">If you would like to stay informed of our progress or recieve news and updates, please join our mailing list by completing the following form.</p>');
        var frm = $('<form name="subscribe" action="http://neshaminycharter.us4.list-manage.com/subscribe/post?u=63cf6b214e924df5a7259237c&amp;id=7da605f9b1" method="POST" target="hidframe"></form>');
        frm.appendTo(box);
        var fld = $('<div class="field"></div>').appendTo(frm);
        fld.append('<label>Email Address</label>');
        var inp = $('<div class="input"></div>').appendTo(frm);
        inp.append('<input type="email" required="true" name="EMAIL"/>');
        var btns = $('<div class="buttons"></div>').appendTo(box);
        btns.click(function(event) {
            var t = $(event.target);
            if (t.hasClass('cancel')) {
                hideModal();
                return false;
            }
            if (t.hasClass('submit')) {
                frm.submit();
                hideModal(true);
                return;
            }
        });
        btns.append('<button class="submit">Submit</button>');
        btns.append('<button class="cancel">Cancel</button>');
        makeModal(box);
    };
    
    // fn extensions
    jQuery.fn.extend({
        'hinted': function() {
            return this.each(function() {
                var that = $(this);
                showHint({'target':that});
                that.bind('focus',hideHint).bind('blur',showHint);
            });
        },
        'dynaAttr': function(attr,i) {
            return this.each(function() {
                var that = $(this);
                var dyna = that.attr(attr);
                if (dyna) {
                    dyna = dyna.replace("{#}",i);
                    that.attr(attr,dyna);
                }
            });
        }
    });
    
    // global object
    var nci = {
        'addGeo': addGeo,
        'addFormGrids': addFormGrids,
        'capture': capture,
        'isBlank': isBlank,
        'share': share
    };
    window.nci = nci;
})();

(function() {
  var iOSCheckbox;
  var __slice = Array.prototype.slice;
  iOSCheckbox = (function() {
    function iOSCheckbox(elem, options) {
      var key, opts, value;
      this.elem = $(elem);
      opts = $.extend({}, iOSCheckbox.defaults, options);
      for (key in opts) {
        value = opts[key];
        this[key] = value;
      }
      this.elem.data(this.dataName, this);
      this.wrapCheckboxWithDivs();
      this.attachEvents();
      this.disableTextSelection();
      if (this.resizeHandle) {
        this.optionallyResize('handle');
      }
      if (this.resizeContainer) {
        this.optionallyResize('container');
      }
      this.initialPosition();
    }
    iOSCheckbox.prototype.isDisabled = function() {
      return this.elem.is(':disabled');
    };
    iOSCheckbox.prototype.wrapCheckboxWithDivs = function() {
      this.elem.wrap("<div class='" + this.containerClass + "' />");
      this.container = this.elem.parent();
      this.offLabel = $("<label class='" + this.labelOffClass + "'>\n  <span>" + this.uncheckedLabel + "</span>\n</label>").appendTo(this.container);
      this.offSpan = this.offLabel.children('span');
      this.onLabel = $("<label class='" + this.labelOnClass + "'>\n  <span>" + this.checkedLabel + "</span>\n</label>").appendTo(this.container);
      this.onSpan = this.onLabel.children('span');
      return this.handle = $("<div class='" + this.handleClass + "'>\n  <div class='" + this.handleRightClass + "'>\n    <div class='" + this.handleCenterClass + "' />\n  </div>\n</div>").appendTo(this.container);
    };
    iOSCheckbox.prototype.disableTextSelection = function() {
      if ($.browser.msie) {
        return $([this.handle, this.offLabel, this.onLabel, this.container]).attr("unselectable", "on");
      }
    };
    iOSCheckbox.prototype._getDimension = function(elem, dimension) {
      if ($.fn.actual != null) {
        return elem.actual(dimension);
      } else {
        return elem[dimension]();
      }
    };
    iOSCheckbox.prototype.optionallyResize = function(mode) {
      var newWidth, offLabelWidth, onLabelWidth;
      onLabelWidth = this._getDimension(this.onLabel, "width");
      offLabelWidth = this._getDimension(this.offLabel, "width");
      if (mode === "container") {
        newWidth = onLabelWidth > offLabelWidth ? onLabelWidth : offLabelWidth;
        newWidth += this._getDimension(this.handle, "width") + this.handleMargin;
        return this.container.css({
          width: newWidth
        });
      } else {
        newWidth = onLabelWidth > offLabelWidth ? onLabelWidth : offLabelWidth;
        return this.handle.css({
          width: newWidth
        });
      }
    };
    iOSCheckbox.prototype.onMouseDown = function(event) {
      var x;
      event.preventDefault();
      if (this.isDisabled()) {
        return;
      }
      x = event.pageX || event.originalEvent.changedTouches[0].pageX;
      iOSCheckbox.currentlyClicking = this.handle;
      iOSCheckbox.dragStartPosition = x;
      return iOSCheckbox.handleLeftOffset = parseInt(this.handle.css('left'), 10) || 0;
    };
    iOSCheckbox.prototype.onDragMove = function(event, x) {
      var newWidth, p;
      if (iOSCheckbox.currentlyClicking !== this.handle) {
        return;
      }
      p = (x + iOSCheckbox.handleLeftOffset - iOSCheckbox.dragStartPosition) / this.rightSide;
      if (p < 0) {
        p = 0;
      }
      if (p > 1) {
        p = 1;
      }
      newWidth = p * this.rightSide;
      this.handle.css({
        left: newWidth
      });
      this.onLabel.css({
        width: newWidth + this.handleRadius
      });
      this.offSpan.css({
        marginRight: -newWidth
      });
      return this.onSpan.css({
        marginLeft: -(1 - p) * this.rightSide
      });
    };
    iOSCheckbox.prototype.onDragEnd = function(event, x) {
      var p;
      if (iOSCheckbox.currentlyClicking !== this.handle) {
        return;
      }
      if (this.isDisabled()) {
        return;
      }
      if (iOSCheckbox.dragging) {
        p = (x - iOSCheckbox.dragStartPosition) / this.rightSide;
        this.elem.prop('checked', p >= 0.5);
      } else {
        this.elem.prop('checked', !this.elem.prop('checked'));
      }
      iOSCheckbox.currentlyClicking = null;
      iOSCheckbox.dragging = null;
      return this.didChange();
    };
    iOSCheckbox.prototype.refresh = function() {
      return this.didChange();
    };
    iOSCheckbox.prototype.didChange = function() {
      var new_left;
      if (typeof this.onChange === "function") {
        this.onChange(this.elem, this.elem.prop('checked'));
      }
      if (this.isDisabled()) {
        this.container.addClass(this.disabledClass);
        return false;
      } else {
        this.container.removeClass(this.disabledClass);
      }
      new_left = this.elem.prop('checked') ? this.rightSide : 0;
      this.handle.animate({
        left: new_left
      }, this.duration);
      this.onLabel.animate({
        width: new_left + this.handleRadius
      }, this.duration);
      this.offSpan.animate({
        marginRight: -new_left
      }, this.duration);
      return this.onSpan.animate({
        marginLeft: new_left - this.rightSide
      }, this.duration);
    };
    iOSCheckbox.prototype.attachEvents = function() {
      var localMouseMove, localMouseUp, self;
      self = this;
      localMouseMove = function(event) {
        return self.onGlobalMove.apply(self, arguments);
      };
      localMouseUp = function(event) {
        self.onGlobalUp.apply(self, arguments);
        $(document).unbind('mousemove touchmove', localMouseMove);
        return $(document).unbind('mouseup touchend', localMouseUp);
      };
      this.elem.change(function() {
        return self.refresh();
      });
      return this.container.bind('mousedown touchstart', function(event) {
        self.onMouseDown.apply(self, arguments);
        $(document).bind('mousemove touchmove', localMouseMove);
        return $(document).bind('mouseup touchend', localMouseUp);
      });
    };
    iOSCheckbox.prototype.initialPosition = function() {
      var containerWidth, offset;
      containerWidth = this._getDimension(this.container, "width");
      this.offLabel.css({
        width: containerWidth - this.containerRadius
      });
      offset = this.containerRadius + 1;
      if ($.browser.msie && $.browser.version < 7) {
        offset -= 3;
      }
      this.rightSide = containerWidth - this._getDimension(this.handle, "width") - offset;
      if (this.elem.is(':checked')) {
        this.handle.css({
          left: this.rightSide
        });
        this.onLabel.css({
          width: this.rightSide + this.handleRadius
        });
        this.offSpan.css({
          marginRight: -this.rightSide
        });
      } else {
        this.onLabel.css({
          width: 0
        });
        this.onSpan.css({
          marginLeft: -this.rightSide
        });
      }
      if (this.isDisabled()) {
        return this.container.addClass(this.disabledClass);
      }
    };
    iOSCheckbox.prototype.onGlobalMove = function(event) {
      var x;
      if (!(!this.isDisabled() && iOSCheckbox.currentlyClicking)) {
        return;
      }
      event.preventDefault();
      x = event.pageX || event.originalEvent.changedTouches[0].pageX;
      if (!iOSCheckbox.dragging && (Math.abs(iOSCheckbox.dragStartPosition - x) > this.dragThreshold)) {
        iOSCheckbox.dragging = true;
      }
      return this.onDragMove(event, x);
    };
    iOSCheckbox.prototype.onGlobalUp = function(event) {
      var x;
      if (!iOSCheckbox.currentlyClicking) {
        return;
      }
      event.preventDefault();
      x = event.pageX || event.originalEvent.changedTouches[0].pageX;
      this.onDragEnd(event, x);
      return false;
    };
    iOSCheckbox.defaults = {
      duration: 200,
      checkedLabel: 'ON',
      uncheckedLabel: 'OFF',
      resizeHandle: true,
      resizeContainer: true,
      disabledClass: 'iPhoneCheckDisabled',
      containerClass: 'iPhoneCheckContainer',
      labelOnClass: 'iPhoneCheckLabelOn',
      labelOffClass: 'iPhoneCheckLabelOff',
      handleClass: 'iPhoneCheckHandle',
      handleCenterClass: 'iPhoneCheckHandleCenter',
      handleRightClass: 'iPhoneCheckHandleRight',
      dragThreshold: 5,
      handleMargin: 15,
      handleRadius: 4,
      containerRadius: 5,
      dataName: "iphoneStyle",
      onChange: function() {}
    };
    return iOSCheckbox;
  })();
  $.iphoneStyle = this.iOSCheckbox = iOSCheckbox;
  $.fn.iphoneStyle = function() {
    var args, checkbox, dataName, existingControl, method, params, _i, _len, _ref, _ref2, _ref3, _ref4;
    args = 1 <= arguments.length ? __slice.call(arguments, 0) : [];
    dataName = (_ref = (_ref2 = args[0]) != null ? _ref2.dataName : void 0) != null ? _ref : iOSCheckbox.defaults.dataName;
    _ref3 = this.filter(':checkbox');
    for (_i = 0, _len = _ref3.length; _i < _len; _i++) {
      checkbox = _ref3[_i];
      existingControl = $(checkbox).data(dataName);
      if (existingControl != null) {
        method = args[0], params = 2 <= args.length ? __slice.call(args, 1) : [];
        if ((_ref4 = existingControl[method]) != null) {
          _ref4.apply(existingControl, params);
        }
      } else {
        new iOSCheckbox(checkbox, args[0]);
      }
    }
    return this;
  };
  $.fn.iOSCheckbox = function(options) {
    var opts;
    if (options == null) {
      options = {};
    }
    opts = $.extend({}, options, {
      resizeHandle: false,
      disabledClass: 'iOSCheckDisabled',
      containerClass: 'iOSCheckContainer',
      labelOnClass: 'iOSCheckLabelOn',
      labelOffClass: 'iOSCheckLabelOff',
      handleClass: 'iOSCheckHandle',
      handleCenterClass: 'iOSCheckHandleCenter',
      handleRightClass: 'iOSCheckHandleRight',
      dataName: 'iOSCheckbox'
    });
    return this.iphoneStyle(opts);
  };
}).call(this);