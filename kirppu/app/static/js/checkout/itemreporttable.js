// Generated by CoffeeScript 1.7.1
(function() {
  var __hasProp = {}.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

  this.ItemReportTable = (function(_super) {
    __extends(ItemReportTable, _super);

    function ItemReportTable() {
      var c;
      ItemReportTable.__super__.constructor.apply(this, arguments);
      this.columns = [
        {
          title: gettext('#'),
          render: function(_, index) {
            return index + 1;
          },
          "class": 'receipt_index numeric'
        }, {
          title: gettext('code'),
          render: function(i) {
            return i.code;
          },
          "class": 'receipt_code'
        }, {
          title: gettext('item'),
          render: function(i) {
            return i.name;
          },
          "class": 'receipt_item'
        }, {
          title: gettext('price'),
          render: function(i) {
            return displayPrice(i.price);
          },
          "class": 'receipt_price numeric'
        }, {
          title: gettext('status'),
          render: function(i) {
            return displayState(i.state);
          },
          "class": 'receipt_status'
        }
      ];
      this.head.append((function() {
        var _i, _len, _ref, _results;
        _ref = this.columns;
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          c = _ref[_i];
          _results.push($('<th>').text(c.title).addClass(c["class"]));
        }
        return _results;
      }).call(this));
    }

    ItemReportTable.prototype.update = function(items) {
      var c, index, item, row, sum, _i, _len;
      this.body.empty();
      sum = 0;
      for (index = _i = 0, _len = items.length; _i < _len; index = ++_i) {
        item = items[index];
        sum += item.price;
        row = $('<tr>').append((function() {
          var _j, _len1, _ref, _results;
          _ref = this.columns;
          _results = [];
          for (_j = 0, _len1 = _ref.length; _j < _len1; _j++) {
            c = _ref[_j];
            _results.push($('<td>').text(c.render(item, index)).addClass(c["class"]));
          }
          return _results;
        }).call(this));
        this.body.append(row);
      }
      return this.body.append($('<tr>').append($('<th colspan="3">').text(gettext('Total:')), $('<th class="receipt_price numeric">').text(displayPrice(sum))));
    };

    return ItemReportTable;

  })(ResultTable);

}).call(this);
