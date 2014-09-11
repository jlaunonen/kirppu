// Generated by CoffeeScript 1.7.1
(function() {
  var __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  this.VendorCheckoutMode = (function(_super) {
    __extends(VendorCheckoutMode, _super);

    ModeSwitcher.registerEntryPoint("vendor_check_out", VendorCheckoutMode);

    function VendorCheckoutMode(cfg, switcher, vendor) {
      this.onCheckedOut = __bind(this.onCheckedOut, this);
      this.onItemFound = __bind(this.onItemFound, this);
      this.returnItem = __bind(this.returnItem, this);
      this.onGotItems = __bind(this.onGotItems, this);
      VendorCheckoutMode.__super__.constructor.call(this, cfg, switcher);
      this.vendorId = vendor != null ? vendor.id : null;
      this.receipt = new ItemReceiptTable('Returned items');
      this.lastItem = new ItemReceiptTable();
      this.remainingItems = new ItemReceiptTable('Remaining items');
    }

    VendorCheckoutMode.prototype.enter = function() {
      VendorCheckoutMode.__super__.enter.apply(this, arguments);
      this.cfg.uiRef.body.prepend(this.remainingItems.render());
      this.cfg.uiRef.body.prepend(this.lastItem.render());
      if (this.vendorId != null) {
        return this.addVendorInfo();
      }
    };

    VendorCheckoutMode.prototype.glyph = function() {
      return "export";
    };

    VendorCheckoutMode.prototype.title = function() {
      return "Vendor Check-Out";
    };

    VendorCheckoutMode.prototype.actions = function() {
      return [['', this.returnItem], [this.cfg.settings.logoutPrefix, this.onLogout]];
    };

    VendorCheckoutMode.prototype.addVendorInfo = function() {
      Api.vendor_get({
        id: this.vendorId
      }).done((function(_this) {
        return function(vendor) {
          _this.cfg.uiRef.body.prepend($('<input type="button">').addClass('btn btn-primary').attr('value', 'Open Report').click(function() {
            return _this.switcher.switchTo(VendorReport, vendor);
          }));
          return _this.cfg.uiRef.body.prepend(new VendorInfo(vendor).render());
        };
      })(this));
      return Api.item_list({
        vendor: this.vendorId
      }).done(this.onGotItems);
    };

    VendorCheckoutMode.prototype.onGotItems = function(items) {
      var item, remaining, returned, row, _i, _j, _len, _len1, _results;
      remaining = {
        BR: 0,
        ST: 0,
        MI: 0
      };
      for (_i = 0, _len = items.length; _i < _len; _i++) {
        item = items[_i];
        if (!(remaining[item.state] != null)) {
          continue;
        }
        row = this.createRow("", item.code, item.name, item.price);
        this.remainingItems.body.prepend(row);
      }
      returned = {
        RE: 0,
        CO: 0
      };
      _results = [];
      for (_j = 0, _len1 = items.length; _j < _len1; _j++) {
        item = items[_j];
        if (!(returned[item.state] != null)) {
          continue;
        }
        row = this.createRow("", item.code, item.name, item.price);
        _results.push(this.receipt.body.prepend(row));
      }
      return _results;
    };

    VendorCheckoutMode.prototype.returnItem = function(code) {
      return Api.item_find({
        code: code
      }).done(this.onItemFound);
    };

    VendorCheckoutMode.prototype.onItemFound = function(item) {
      if (this.vendorId == null) {
        this.vendorId = item.vendor;
        this.addVendorInfo();
      } else if (this.vendorId !== item.vendor) {
        alert('Someone else\'s item!');
        return;
      }
      return Api.item_checkout({
        code: item.code
      }).done(this.onCheckedOut);
    };

    VendorCheckoutMode.prototype.onCheckedOut = function(item) {
      this.receipt.body.prepend($('tr', this.lastItem.body));
      return this.lastItem.body.prepend($('#' + item.code, this.remainingItems.body));
    };

    return VendorCheckoutMode;

  })(ItemCheckoutMode);

}).call(this);
