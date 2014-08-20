// Generated by CoffeeScript 1.7.1
(function() {
  this.CheckoutMode = (function() {
    function CheckoutMode(switcher, config) {
      this.switcher = switcher;
      this.cfg = config ? config : CheckoutConfig;
    }

    CheckoutMode.prototype.title = function() {
      return "[unknown mode]";
    };

    CheckoutMode.prototype.subtitle = function() {
      return null;
    };

    CheckoutMode.prototype.columns = function() {
      return [];
    };

    CheckoutMode.prototype.enter = function() {
      return null;
    };

    CheckoutMode.prototype.exit = function() {
      return null;
    };

    CheckoutMode.prototype.actions = function() {
      return [["", function() {}]];
    };

    return CheckoutMode;

  })();

}).call(this);
