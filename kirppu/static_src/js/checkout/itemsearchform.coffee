class @ItemSearchForm

  constructor: (action) ->
    @action = action

    @searchInput = $('<input type="text" id="item_search_input" class="form-control">')
    @minPriceInput = $('<input type="number" step="any" min="0" id="item_search_min_price" class="form-control">')
    @maxPriceInput = $('<input type="number" step="any" min="0" id="item_search_max_price" class="form-control">')

    @form = $('<form role="form" class="form-horizontal">').append([
      $('<div class="form-group">').append([
        $('<label for="item_search_input" class="control-label col-sm-2">Name</label>')
        $('<div class="input-group col-sm-10">').append(@searchInput)
      ])
      $('<div class="form-group">').append([
        $('<label for="item_search_min_price" class="control-label col-sm-2">Minimum price</label>')
        $('<div class="input-group col-sm-2">').append([
          @minPriceInput
          $('<span class="input-group-addon">').text('€')
        ])
      ])
      $('<div class="form-group">').append([
        $('<label for="item_search_max_price" class="control-label col-sm-2">Maximum price</label>')
        $('<div class="input-group col-sm-2">').append([
          @maxPriceInput
          $('<span class="input-group-addon">').text('€')
        ])
      ])
      $('<div class="col-sm-offset-2">').append(
        $('<button type="submit" class="btn btn-default" class="col-sm-1">')
          .text('Search')
      )
    ])
    @form.off('submit')
    @form.submit(@onSubmit)

  render: -> @form

  onSubmit: (event) =>
    do event.preventDefault
    @action(
      @searchInput.val()
      @minPriceInput.val()
      @maxPriceInput.val()
    )
