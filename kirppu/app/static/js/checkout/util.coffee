@displayPrice = (price, rounded=false) ->
  if price?
    if Number.isInteger(price)
      price_str = price.formatCents() + " €"
    else
      price_str = price
      rounded = false
  else
    price_str = ""
    rounded = false

  if rounded and price.round5() != price
    rounded_str = price.round5().formatCents() + " €"
    price_str = "#{ rounded_str } (#{ price_str })"

  return price_str

@displayState = (state) ->
  {
    SO: 'sold'
    BR: 'on display'
    ST: 'about to be sold'
    MI: 'missing'
    RE: 'returned to the vendor'
    CO: 'sold and compensated to the vendor'
    AD: 'not brought to the event'
  }[state]

# Round the number to closest modulo 5.
#
# @return Integer rounded to closest 5.
Number.prototype.round5 = ->
  modulo = this % 5

  # 2.5 == split-point, i.e. half of 5.
  if modulo >= 2.5
    return this + (5 - modulo)
  else
    return this - modulo
