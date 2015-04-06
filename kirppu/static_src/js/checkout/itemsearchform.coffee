class @ItemSearchForm

  constructor: (action) ->
    @action = action

    @searchInput = $('<input type="text" id="item_search_input" class="form-control">')
    @form = $('<form role="form">').append([
      $('<div class="form-group">').append([
        $('<label for="item_search_input">Name</label>')
        @searchInput
      ])
      $('<button type="submit" class="btn btn-default">').text('Search')
    ])
    @form.off('submit')
    @form.submit(@onSubmit)

  render: -> @form

  onSubmit: (event) =>
    do event.preventDefault
    @action(@searchInput.val())
