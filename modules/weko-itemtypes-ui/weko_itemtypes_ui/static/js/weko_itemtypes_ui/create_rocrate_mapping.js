$(document).ready(function () {
  $('#message-modal').modal({ show: false })

  const page_global = {
    url: '/admin/itemtypes/rocrate_mapping/',
    src_mapping_name: '',
    dst_mapping_name: '',
    hasEdit: false,
    hasError: false,
    item_properties: null,
    schema_prop: {},
    mapping_prop: null,
    sub_itemtype_list: [],
    sub_mapping_list: {},
    meta_system: null,
  }
  page_global.src_mapping_name = $('#item-type-lists').val();
  page_global.dst_mapping_name = $('#item-type-lists').val();

  function addAlert(message) {
    $('#alerts').append(
      '<div id="alert-style" class="alert alert-light">' +
      '<button type="button" class="close" data-dismiss="alert">&times;</button>' +
      message +
      '</div>');
  };

  function addError(message, err_items) {
    message += '<br/>'
    err_items.forEach(function (items) {
      message += '[' + items[0] + ' && ' + items[1] + ']' + '<br/>'
    })
    $('#errors').append(
      '<div class="alert alert-danger alert-dismissable">' +
      '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>' +
      message +
      '</div>');
  };

  $('#item-type-lists').change(function (ev) {
    page_global.dst_mapping_name = $(this).val();
    if (page_global.hasEdit) {
      $('.modal-title').text('Present');
      $('.modal-body').text('Would you like to cancel your changes?');
      $('#btn-submit').addClass('hide');
      $('#btn-confirm').removeClass('hide');
      $('#message-modal').modal('show');
    } else {
      window.location.href = page_global.url + page_global.dst_mapping_name;
    }
  });

  $('#message-modal').on('hide.bs.modal', function (e) {
    $('#item-type-lists').val(page_global.src_mapping_name);
  })

  $('#btn-confirm').on('click', function (ev) {
    window.location.href = page_global.url + page_global.dst_mapping_name;
  });

  $('input[type="text"]').change(function (ev) {
    page_global.hasEdit = true;
  });

  $('#layer-num').change(function (ev) {
    page_global.hasEdit = true;

    const layer_num = Number($(this).val());
    const layers = $('ul[name="layer-ul"]');
    if (layer_num + 2 < layers.length) {
      // Remove child layer
      layers[layer_num + 2].remove();
    } else {
      // Add child layer
      for (let ii = layers.length; ii < layer_num + 2; ii++) {
        const template = $('ul[name="layer-ul"]').first().clone(true);
        $('li[name="layer-li"]').last().append(template);
      }
    }
  });

  $('input[name="select-node"]').change(function (ev) {
    const radio_val = $(this).val();
    console.log(radio_val)
  });

  $('button[type="button"]').on('click', function (ev) {
    page_global.hasEdit = true;
    const action = this.dataset.action;
    if ('add_node' == action) {
      const template = $('li[name="node-li"]').first().clone(true);

      // Add event
      template.find('.arrow').get(0).addEventListener('click', toggleArrow);

      // Add node
      $(this).closest('li').before(template);
    }
    if ('del_node' == action) {
      // Remove node
      $(this).closest('li').remove();
    }
  });

  $('input[name="check-language"]').on('click', function (ev) {
    const check_value = $(this).is(':checked');
    const column = $(this).parents('[name="metadata-property-column"]');
    const property = column.find('[name="metadata-property"]');
    const property_with_lang = column.find('[name="metadata-property-with-lang"]');
    if (check_value) {
      property.addClass('hide');
      property_with_lang.removeClass('hide');
    } else {
      property.removeClass('hide');
      property_with_lang.addClass('hide');
    }
  });

  $('input[name="check-list-index"]').on('click', function (ev) {
    const index_text = $(this).parent().prev();
    index_text.toggleClass('invisible');
  });

  $('select[name="metadata-select"]').change(function (ev) {
    page_global.hasEdit = true;
    if (page_global.item_properties == null) {
      const item_properties_str = $('#item-properties').text();
      page_global.item_properties = JSON.parse(item_properties_str);
    }

    // init input area
    const input_area = $(this).closest('[name="metadata-property-item"]');
    input_area.nextAll().remove();
    input_area.find('input[type="number"]').addClass('invisible');
    input_area.find('label').addClass('invisible');
    input_area.find('input[name="check-list-index"]').prop('checked', false);

    const val = $(this).val();
    if (val == undefined) {
      return;
    }

    // Get selected property
    const selected_prop_key = [];
    const select_list = $(this).closest('[name="metadata-property"]').find('select');
    select_list.each((index, element) => {
      selected_prop_key.push(element.value);
    });
    let is_list = false;
    let selected_prop = page_global.item_properties;
    for (let key of selected_prop_key) {
      selected_prop = selected_prop[key];
      if (selected_prop['type'] == 'array') {
        if (val == key) {
          is_list = true;
        }
        selected_prop = selected_prop['items']['properties'];
      } else if (selected_prop['type'] == 'object') {
        selected_prop = selected_prop['properties'];
      }
    }

    // Show specify index checkbox if selected property is list.
    if (is_list) {
      input_area.find('label').removeClass('invisible');
    }

    // Add child property select box
    if (selected_prop != null && selected_prop['type'] != 'string') {
      const template = $('[name="metadata-property-item"]').first().clone(true);
      const select = template.find('select');
      for (let key in selected_prop) {
        select.append($('<option>').html(selected_prop[key]['title']).val(key));
      }

      input_area.after(template);
    }
  });

  $('select[name="metadata-value-select"]').change(function (ev) {
    page_global.hasEdit = true;
    if (page_global.item_properties == null) {
      const item_properties_str = $('#item-properties').text();
      page_global.item_properties = JSON.parse(item_properties_str);
    }

    // init input area
    // FIXME: もう一方が多い場合は削除ではなく非表示で対応
    const input_area = $(this).closest('[name="metadata-property-item-with-lang"]');
    input_area.nextAll().remove();
    input_area.find('input[type="number"]').addClass('invisible');
    input_area.find('label').addClass('invisible');
    input_area.find('input[name="check-list-index"]').prop('checked', false);

    const val = $(this).val();
    if (val == undefined) {
      return;
    }

    // Get selected property
    const selected_prop_key = [];
    const select_list = $(this).closest('[name="metadata-property-with-lang"]').find('select[name="metadata-value-select"]');
    select_list.each((index, element) => {
      selected_prop_key.push(element.value);
    });
    let is_list = false;
    let selected_prop = page_global.item_properties;
    for (let key of selected_prop_key) {
      selected_prop = selected_prop[key];
      if (selected_prop['type'] == 'array') {
        if (val == key) {
          is_list = true;
        }
        selected_prop = selected_prop['items']['properties'];
      } else if (selected_prop['type'] == 'object') {
        selected_prop = selected_prop['properties'];
      }
    }

    // Add child property select box
    if (selected_prop != null && selected_prop['type'] != 'string') {
      const template = $('[name="metadata-property-item-with-lang"]').first().clone(true);
      const select = template.find('select[name="metadata-value-select"]');
      for (let key in selected_prop) {
        select.append($('<option>').html(selected_prop[key]['title']).val(key));
      }

      input_area.after(template);
    }
  });

  function buildMappingData() {
    console.log('buildMappingData')
  };

  function send(url, data) {
    $.ajax({
      method: 'POST',
      url: url,
      async: true,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: function (data, textStatus) {
        page_global.hasEdit = false;
        $('html,body').scrollTop(0);
        if ('duplicate' in data) {
          addError(data.msg, data.err_items);
        } else {
          addAlert(data.msg);
        }
      },
      error: function (textStatus, errorThrown) {
        $('.modal-body').text('Error: ' + JSON.stringify(textStatus));
        $('#message-modal').modal('show');
      }
    });
  }

  $('#mapping-submit').on('click', function () {
    let error_flag = false;
    buildMappingData();
    if (error_flag) {
      return;
    }
    const data = {
      item_type_id: parseInt(page_global.src_mapping_name),
      mapping: page_global.mapping_prop,
    };
    send(page_global.url, data);
  });

  function toggleArrow() {
    const nested = this.parentElement.querySelector('.nested');
    if (nested != null) {
      nested.classList.toggle('active');
    }
    this.classList.toggle('arrow-down');
  };

  const toggler = document.getElementsByClassName('arrow');
  for (let ii = 0; ii < toggler.length; ii++) {
    toggler[ii].addEventListener('click', toggleArrow);
  }

});
