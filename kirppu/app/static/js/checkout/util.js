// Generated by CoffeeScript 1.7.1
(function() {
  this.displayPrice = function(price, rounded) {
    var price_str, rounded_str;
    if (rounded == null) {
      rounded = false;
    }
    if (price != null) {
      if (Number.isInteger(price)) {
        price_str = price.formatCents() + " €";
      } else {
        price_str = price;
        rounded = false;
      }
    } else {
      price_str = "";
      rounded = false;
    }
    if (rounded && price.round5() !== price) {
      rounded_str = price.round5().formatCents() + " €";
      price_str = "" + rounded_str + " (" + price_str + ")";
    }
    return price_str;
  };

  this.displayState = function(state) {
    return {
      SO: 'sold',
      BR: 'on display',
      ST: 'about to be sold',
      MI: 'missing',
      RE: 'returned to the vendor',
      CO: 'sold and compensated to the vendor',
      AD: 'not brought to the event'
    }[state];
  };

  Number.prototype.round5 = function() {
    var modulo;
    modulo = this % 5;
    if (modulo >= 2.5) {
      return this + (5 - modulo);
    } else {
      return this - modulo;
    }
  };

}).call(this);
