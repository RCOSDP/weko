$(document).ready(function () {
  $('#message-modal').modal({ show: false })

  const page_global = {
    url: '/admin/itemtypes/rocrate_mapping/',
    src_mapping_name: $('#item-type-lists').val(),
    dst_mapping_name: $('#item-type-lists').val(),
    hasEdit: false,
    // hasError: false,
    item_properties: null,
    mapping_prop: null,
  }

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
      message += '[' + items[0] + ' && ' + items[1] + ']' + '<br/>';
    })
    $('#errors').append(
      '<div class="alert alert-danger alert-dismissable">' +
      '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>' +
      message +
      '</div>');
  };

  $('#item-type-lists').change((ev) => {
    page_global.dst_mapping_name = $(ev.target).val();
    if (page_global.hasEdit) {
      $('.modal-title').text('Present');
      $('.modal-body').text('Would you like to cancel your changes?');
      $('#btn-submit').addClass('hide');
      $('#btn-confirm').removeClass('hide');
      $('#message-modal').modal('show');
    }
    else {
      window.location.href = page_global.url + page_global.dst_mapping_name;
    }
  });

  $('#message-modal').on('hide.bs.modal', (ev) => {
    $('#item-type-lists').val(page_global.src_mapping_name);
  })

  $('#btn-confirm').on('click', (ev) => {
    window.location.href = page_global.url + page_global.dst_mapping_name;
  });

  $('input[type="text"]').change((ev) => {
    page_global.hasEdit = true;
  });

  $('#layer-num').change((ev) => {
    page_global.hasEdit = true;

    const layer_num = Number($(ev.target).val());
    const layers = $('ul[name="layer-ul"]');
    if (layer_num + 2 < layers.length) {
      // Remove child layer
      layers[layer_num + 2].remove();
    }
    else {
      // Add child layer
      for (let ii = layers.length; ii < layer_num + 2; ii++) {
        const template = $('ul[name="layer-ul"]').first().clone(true);
        $('li[name="layer-li"]').last().append(template);
      }
    }
  });

  $('input[name="select-node"]').change((ev) => {
    // const radio_val = $(ev.target).val();

    const node_text_list = []
    $(ev.target).parents('li').each((index, value) => {
      node_text_list.push($(value).children().eq(1).find('input[type="text"]').val());
    });
    let node_name = '';
    for (let node_text of node_text_list) {
      if (node_name == '') {
        node_name = node_text;
      }
      else {
        node_name = node_text + '/' + node_name;
      }
    }
    $('label#rocrate-property-label').text(node_name);

    const item_type_name = $('#item-type-lists option:selected').text();
    $('label#metadata-property-label').text(item_type_name);
  });

  $('button[type="button"]').on('click', (ev) => {
    page_global.hasEdit = true;
    const target = ev.currentTarget;
    const action = target.dataset.action;
    if (action == 'add-node') {
      const template = $('li[name="node-li"]').first().clone(true);

      // Add event
      template.find('.arrow').get(0).addEventListener('click', toggleArrow);

      // Add node
      $(target).closest('li').before(template);
    }
    else if (action == 'del-node') {
      // Remove node
      $(target).closest('li').remove();
    }
    else if (action == 'add-mapping') {
      const template = $('#template-mapping-row :first').clone(true);

      const template_metadata_column = $('#template-metadata-property-column :first').clone(true);
      template.find('div[name="button-row"]').before(template_metadata_column);

      // Add mapping table row
      $('#mapping-table').append(template);
      $('#mapping-table').append('<hr>');
    }
    else if (action == 'del-mapping') {
      // Remove mapping table row
      const table_row = $(target).closest('[name="mapping-table-row"]');
      table_row.next().remove() // remove hr
      table_row.remove();
    }
    else if (action == 'add-metadata-property') {
      const template = $('#template-metadata-property-column :first').clone(true);

      // Add metadata property
      $(target).closest('div[name="button-row"]').before(template);
    }
    else if (action == 'del-metadata-property') {
      // Remove metadata property
      $(target).closest('[name="metadata-property-column"]').remove();
    }
  });

  $('input[name="check-language"]').on('click', (ev) => {
    const check_value = $(ev.target).is(':checked');
    const column = $(ev.target).parents('[name="metadata-property-column"]');
    const property = column.find('[name="metadata-property"]');
    const property_with_lang = column.find('[name="metadata-property-with-lang"]');
    if (check_value) {
      property.addClass('hide');
      property_with_lang.removeClass('hide');
    }
    else {
      property.removeClass('hide');
      property_with_lang.addClass('hide');
    }
  });

  $('input[name="check-list-index"]').on('click', (ev) => {
    const index_text = $(ev.target).parent().prev();
    index_text.toggleClass('invisible');
  });

  $('select[name="metadata-select"]').change((ev) => {
    page_global.hasEdit = true;

    // Init input area
    const input_area = $(ev.target).closest('[name="metadata-property-item"]');
    input_area.nextAll().remove();
    input_area.find('input[type="number"]').addClass('invisible');
    input_area.find('label').addClass('invisible');
    input_area.find('input[name="check-list-index"]').prop('checked', false);

    if ($(ev.target).val() == '') {
      return;
    }

    // Get selected property
    const selected_prop_key = getSelectedKeys(ev.target);
    const selected_prop = getSelectedProp(selected_prop_key);

    // Show specify index checkbox if selected property is list.
    if (selected_prop['type'] == 'array') {
      input_area.find('label').removeClass('invisible');
    }

    // Add child property select box
    const child_props = getChildProps(selected_prop);
    if (child_props != null) {
      // Create child select box
      const template = $('#template-metadata-property-item :first').clone(true);
      input_area.after(template);

      // Set child property
      const select = template.find('select');
      for (let key in child_props) {
        select.append($('<option>').html(child_props[key]['title']).val(key));
      }
    }
  });

  $('select[name="metadata-value-select"]').change((ev) => {
    page_global.hasEdit = true;

    // Init input area
    const select_list = $(ev.target).closest('[name="metadata-property-with-lang"]').find('select[name="metadata-value-select"]');
    const index = select_list.index(ev.target);
    for (let ii = 0; ii < select_list.length; ii++) {
      if (ii <= index) {
        continue;
      }
      // Init child select box
      const child_select = select_list.eq(ii);
      child_select.children().remove();
      child_select.append($('<option>').html('').val(''));
    }

    // Delete waste area
    removeWasteArea(ev.target);

    if ($(ev.target).val() == '') {
      return;
    }

    const selected_prop_key_value = getSelectedKeys(ev.target, 'metadata-value-select');
    const selected_prop_key_lang = getSelectedKeys(ev.target, 'metadata-lang-select');
    const create_child_select = selected_prop_key_value.length > selected_prop_key_lang.length;

    // Get selected property
    const selected_prop = getSelectedProp(selected_prop_key_value);

    // Add child property select box
    const child_props = getChildProps(selected_prop);
    if (child_props != null) {
      if (create_child_select) {
        const template = $('#template-metadata-property-item-with-lang :first').clone(true);
        const input_area = $(ev.target).closest('[name="metadata-property-item-with-lang"]');
        input_area.after(template);
      }

      // Set child property
      const child_select = $(ev.target)
        .closest('[name="metadata-property-with-lang"]')
        .find('select[name="metadata-value-select"]')
        .eq(selected_prop_key_value.length);
      for (let key in child_props) {
        child_select.append($('<option>').html(child_props[key]['title']).val(key));
      }
      child_select.removeClass('invisible');
    }
  });

  $('select[name="metadata-lang-select"]').change((ev) => {
    page_global.hasEdit = true;

    // Init input area
    const select_list = $(ev.target).closest('[name="metadata-property-with-lang"]').find('select[name="metadata-lang-select"]');
    const index = select_list.index(ev.target);
    for (let ii = 0; ii < select_list.length; ii++) {
      if (ii <= index) {
        continue;
      }
      // Init child select box
      const child_select = select_list.eq(ii);
      child_select.children().remove();
      child_select.append($('<option>').html('').val(''));
    }

    // Delete waste area
    removeWasteArea(ev.target);

    if ($(ev.target).val() == '') {
      return;
    }

    const selected_prop_key_value = getSelectedKeys(ev.target, 'metadata-value-select');
    const selected_prop_key_lang = getSelectedKeys(ev.target, 'metadata-lang-select');
    const create_child_select = selected_prop_key_lang.length > selected_prop_key_value.length;

    // Get selected property
    const selected_prop = getSelectedProp(selected_prop_key_lang);

    // Add child property select box
    const child_props = getChildProps(selected_prop);
    if (child_props != null) {
      if (create_child_select) {
        const template = $('#template-metadata-property-item-with-lang :first').clone(true);
        const input_area = $(ev.target).closest('[name="metadata-property-item-with-lang"]');
        input_area.after(template);
      }

      // Set child property
      const child_select = $(ev.target)
        .closest('[name="metadata-property-with-lang"]')
        .find('select[name="metadata-lang-select"]')
        .eq(selected_prop_key_lang.length);
      for (let key in child_props) {
        child_select.append($('<option>').html(child_props[key]['title']).val(key));
      }
      child_select.removeClass('invisible');
    }
  });

  function getSelectedKeys(select_box, select_name) {
    const keys = [];
    const select_list = (() => {
      if (select_name == null) {
        return $(select_box).closest('[name="metadata-property"]').find('select');
      } else {
        return $(select_box).closest('[name="metadata-property-with-lang"]').find(`select[name="${select_name}"]`);
      }
    })();
    for (const elem of select_list.toArray()) {
      if (elem.value == '') {
        break;
      }
      keys.push(elem.value);
      if ($(select_box).val() == elem.value) {
        break;
      }
    }
    return keys;
  };

  function getSelectedProp(keys) {
    if (page_global.item_properties == null) {
      const item_properties_str = $('#item-properties').text();
      page_global.item_properties = JSON.parse(item_properties_str);
    }
    let selected_prop = page_global.item_properties;
    for (let key of keys) {
      if ('type' in selected_prop) {
        selected_prop = getChildProps(selected_prop);
      }
      selected_prop = selected_prop[key];
    }
    return selected_prop;
  };

  function getChildProps(prop) {
    let childProps = null;
    if (prop['type'] == 'array') {
      childProps = prop['items']['properties'];
    }
    else if (prop['type'] == 'object') {
      childProps = prop['properties'];
    }
    return childProps;
  };

  function removeWasteArea(select_box) {
    let find = false;
    const select_value_list = $(select_box).closest('[name="metadata-property-with-lang"]').find('select[name="metadata-value-select"]');
    let valid_value_num = select_value_list.length;
    for (let ii = 0; ii < select_value_list.length; ii++) {
      const select = select_value_list.eq(ii);
      if (select.find('option').length == 1) {
        if (!find) {
          valid_value_num = ii;
          find = true;
        }
        select.addClass('invisible')
      }
    }

    find = false;
    const select_lang_list = $(select_box).closest('[name="metadata-property-with-lang"]').find('select[name="metadata-lang-select"]');
    let valid_lang_num = select_lang_list.length;
    for (let ii = 0; ii < select_lang_list.length; ii++) {
      const select = select_lang_list.eq(ii);
      if (select.find('option').length == 1) {
        if (!find) {
          valid_lang_num = ii;
          find = true;
        }
        select.addClass('invisible')
      }
    }

    const valid_num = Math.max(valid_value_num, valid_lang_num);
    const input_areas = $(select_box).closest('[name="metadata-property-item-with-lang"]').parent().find('[name="metadata-property-item-with-lang"]');
    input_areas.eq(valid_num - 1).nextAll().remove();
  }

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
        }
        else {
          addAlert(data.msg);
        }
      },
      error: function (textStatus, errorThrown) {
        $('.modal-body').text('Error: ' + JSON.stringify(textStatus));
        $('#message-modal').modal('show');
      }
    });
  }

  $('#mapping-submit').on('click', (ev) => {
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

  function toggleArrow(ev) {
    const nested = ev.target.parentElement.querySelector('.nested');
    if (nested != null) {
      nested.classList.toggle('active');
    }
    ev.target.classList.toggle('arrow-down');
  };

  const toggler = document.getElementsByClassName('arrow');
  for (let ii = 0; ii < toggler.length; ii++) {
    toggler[ii].addEventListener('click', toggleArrow);
  }

});
