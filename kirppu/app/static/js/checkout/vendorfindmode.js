// Generated by CoffeeScript 1.7.1
(function() {
  var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
    __slice = [].slice;

  this.VendorFindMode = (function(_super) {
    __extends(VendorFindMode, _super);

    ModeSwitcher.registerEntryPoint("vendor_find", VendorFindMode);

    function VendorFindMode() {
      var args, query, _i;
      args = 2 <= arguments.length ? __slice.call(arguments, 0, _i = arguments.length - 1) : (_i = 0, []), query = arguments[_i++];
      this.createRow = __bind(this.createRow, this);
      this.onVendorsFound = __bind(this.onVendorsFound, this);
      VendorFindMode.__super__.constructor.apply(this, arguments);
      this.vendorList = new VendorList();
      this.query = query;
    }

    VendorFindMode.prototype.enter = function() {
      VendorFindMode.__super__.enter.apply(this, arguments);
      this.cfg.uiRef.body.append(this.vendorList.render());
      if (this.query != null) {
        return Api.vendor_find({
          q: this.query
        }).done(this.onVendorsFound);
      }
    };

    VendorFindMode.prototype.glyph = function() {
      return "user";
    };

    VendorFindMode.prototype.title = function() {
      return "Vendor Search";
    };

    VendorFindMode.prototype.inputPlaceholder = function() {
      return "Search";
    };

    VendorFindMode.prototype.actions = function() {
      return [
        [
          "", (function(_this) {
            return function(query) {
              return Api.vendor_find({
                q: query
              }).done(_this.onVendorsFound);
            };
          })(this)
        ]
      ];
    };

    VendorFindMode.prototype.onVendorsFound = function(vendors) {
      var index, vendor, _i, _len, _results;
      this.vendorList.body.empty();
      _results = [];
      for (index = _i = 0, _len = vendors.length; _i < _len; index = ++_i) {
        vendor = vendors[index];
        _results.push(this.vendorList.body.append(this.createRow(index + 1, vendor)));
      }
      return _results;
    };

    VendorFindMode.prototype.createRow = function(index, vendor) {
      var a, row, _i, _len, _ref;
      row = $("<tr>");
      row.append($("<td>").text(index));
      _ref = ['id', 'name', 'email', 'phone'];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        a = _ref[_i];
        row.append.apply(row, $("<td>").text(vendor[a]));
      }
      return row.click((function(_this) {
        return function() {
          return _this.switcher.switchTo(VendorReport, vendor);
        };
      })(this));
    };

    return VendorFindMode;

  })(CheckoutMode);

}).call(this);
