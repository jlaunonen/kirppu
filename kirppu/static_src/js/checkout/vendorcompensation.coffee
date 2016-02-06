class @VendorCompensation extends CheckoutMode

  constructor: (cfg, switcher, vendor) ->
    super(cfg, switcher)
    @vendor = vendor

  title: -> "Vendor Compensation"

  enter: ->
    super
    @cfg.uiRef.codeForm.hide()
    @switcher.setMenuEnabled(false)
    @cfg.uiRef.body.append(new VendorInfo(@vendor).render())

    @buttonForm = $('<form class="hidden-print">').append(@abortButton())
    @cfg.uiRef.body.append(@buttonForm)

    @itemDiv = $('<div>')
    @cfg.uiRef.body.append(@itemDiv)

    Api.item_list(vendor: @vendor.id, state: "SO", include_box_items: true).done(@onGotItems)

  exit: ->
    @cfg.uiRef.codeForm.show()
    @switcher.setMenuEnabled(true)
    super

  confirmButton: ->
    $('<input type="button" class="btn btn-success">')
      .attr('value', 'Confirm')
      .click(@onConfirm)

  abortButton: ->
    $('<input type="button" class="btn btn-default">')
      .attr('value', 'Cancel')
      .click(@onCancel)

  continueButton: (type="primary", clickHandler=@onCancel) =>
    $('<input type="button" class="btn btn-' + type + '">')
      .attr('value', 'Continue')
      .click(clickHandler)

  retryButton: ->
    $('<input type="button" class="btn btn-primary">')
      .attr('value', 'Retry')
      .click(@onRetryFailed)

  onGotItems: (items) =>
    @compensableItems = items

    if @compensableItems.length > 0
      table = Templates.render("item_report_table",
        caption: "Sold Items"
        items: @compensableItems
        sum: _.reduce(@compensableItems, ((acc, item) -> acc + item.price), 0)
        topSum: true
        extra_col: true
      )
      @itemDiv.empty().append(table)
      @buttonForm.empty().append(@confirmButton(), @abortButton())

    else
      @itemDiv.empty().append($('<em>').text('No compensable items'))
      @buttonForm.empty().append(@continueButton())

  onCancel: => @switcher.switchTo(VendorReport, @vendor)

  onConfirm: =>
    nItems = @compensableItems.length
    if nItems == 0
      console.error("What? Nothing to compensate?")
      return
    @buttonForm.empty()

    # Add table row indices for items (needed to point to the rows at UI).
    for i, index in @compensableItems
      i.row_index = index + 1

    @_loopResult = []
    @_loopBack(@compensableItems)

  # Compensate items by looping over the list of items.
  # Failed items are added to @_loopResult thus it must be set to empty Array before calling this.
  # The failed items can then be tried again with this function. Note, that @_loopResult must be
  # cleared for retry also!
  #
  # @param list [Array] List of Items to compensate.
  # @param index [Integer, optional] Current index. Must be 0 when calling from outside this function.
  _loopBack: (list, index=0) =>
    item = list[index]
    status = $(".table_row_#{item.row_index} > .receipt_extra_col", @itemDiv)
    status.html('<span class="glyphicon glyphicon-repeat spinner text-info"></span>')

    cb = (glyph, color) => () =>
      status.html("<span class=\"glyphicon glyphicon-#{glyph} text-#{color}\"></span>")
      if index + 1 < list.length
        @_loopBack(list, index + 1)
      else
        @_onLoopDone()

    # Compensate an item. When successful, set the item state. If failure, add it to list of failed items.
    Api.item_compensate(code: item.code)
      .done(() => item.state = "CO")
      .done(cb("ok", "success"))
      .fail(() => @_loopResult.push(item))
      .fail(cb("remove", "danger"))

  # Looping done, choose next action.
  _onLoopDone: () =>
    if @_loopResult.length > 0
      # Some items failed. Give options to retry or continue/skip.
      @buttonForm.append(@retryButton(), @continueButton("warning", @onSkipFailed))
    else
      # All success. Continue to compensation view.
      setTimeout((=> @onCompensated()), 1000)

  # Start new compensation loop over failed items.
  onRetryFailed: =>
    nItems = @_loopResult.length
    if nItems == 0
      console.error("What? Nothing to retry?")
      return
    @buttonForm.empty()

    list = @_loopResult
    @_loopResult = []
    @_loopBack(list)

  # Skip failed items and proceed to compensation with only the successful items.
  onSkipFailed: =>
    r = confirm("Failed items will not be compensated. Check report. Are you sure to skip failed items?")
    if r
      @onCompensated()

  onCompensated: ->
    @switcher.setPrintable()

    # Create list of succeeded i.e. compensated items.
    items = []
    for item in @compensableItems
      if item.state == "CO"
        items.push(item)
    @compensableItems = []

    table = Templates.render("item_report_table",
      caption: "Compensated Items"
      items: items
      sum: _.reduce(items, ((acc, item) -> acc + item.price), 0)
      topSum: true
    )
    @itemDiv.empty().append(table)
    @buttonForm.empty().append(@continueButton())
