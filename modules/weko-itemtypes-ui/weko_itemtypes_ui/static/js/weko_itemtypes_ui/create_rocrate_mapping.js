$(() => {
  $('#message-modal').modal({ show: false })

  const page_global = {
    url: '/admin/itemtypes/rocrate_mapping',
    src_mapping_name: $('#select-item-type').val(),
    dst_mapping_name: $('#select-item-type').val(),
    hasEdit: false,
    item_properties: null,
    rocrate_mapping: null,
    node_mapping: {},
    node_index_counter: 0,
  }
  const item_properties_str = $('#item-properties').text();
  page_global.item_properties = JSON.parse(item_properties_str);
  const rocrate_mapping_str = $('#rocrate-mapping').text();
  if (rocrate_mapping_str != '') {
    page_global.rocrate_mapping = JSON.parse(rocrate_mapping_str);
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
    err_items.forEach((items) => {
      message += '[' + items[0] + ' && ' + items[1] + ']' + '<br/>';
    })
    $('#errors').append(
      '<div class="alert alert-danger alert-dismissable">' +
      '<button type="button" class="close" data-dismiss="alert" aria-hidden="true">&times;</button>' +
      message +
      '</div>');
  };

  $('#select-item-type').change((ev) => {
    page_global.dst_mapping_name = $(ev.target).val();
    if (page_global.hasEdit) {
      $('.modal-title').text('Present');
      $('.modal-body').text('Would you like to cancel your changes?');
      $('#btn-submit').addClass('hide');
      $('#btn-confirm').removeClass('hide');
      $('#message-modal').modal('show');
    }
    else {
      window.location.href = page_global.url + '/' + page_global.dst_mapping_name;
    }
  });

  $('#message-modal').on('hide.bs.modal', (ev) => {
    $('#select-item-type').val(page_global.src_mapping_name);
  })

  $('#btn-confirm').on('click', (ev) => {
    window.location.href = page_global.url + '/' + page_global.dst_mapping_name;
  });

  $('input[type="text"]').change((ev) => {
    page_global.hasEdit = true;
  });

  $('#layer-num').change((ev) => {
    page_global.hasEdit = true;

    const layer_num = Number($(ev.target).val());
    const layers = $('#layer-base').find('ul[name="layer-ul"]');
    if (layer_num < layers.length) {
      // Remove child layer
      layers[layer_num].remove();
    }
    else {
      // Add child layer
      for (let ii = layers.length; ii < layer_num; ii++) {
        addLayer();
      }
    }
  });

  function addLayer() {
    const template = $('#template-layer-name :first').clone(true);
    $('li[name="layer-li"]').last().append(template);
  }

  $('.arrow').on('click', (ev) => {
    $(ev.target).nextAll('.nested').toggleClass('active');
    $(ev.target).toggleClass('arrow-down');
  });

  $('input[name="select-node"]').change((ev) => {
    // Save mapping
    saveCurrentMapping();
    initCurrentMapping();

    // Get node name
    let node_name = '';
    $(ev.target).parents('li').each((_, elem) => {
      const node_text = $(elem).children().eq(1).find('input[type="text"]').val();
      node_name = node_text + '/' + node_name;
    });
    node_name = node_name.slice(0, -1);
    $('label#rocrate-property-label').text(node_name);

    // Get item type name
    const item_type_name = $('#select-item-type option:selected').text();
    $('label#metadata-property-label').text(item_type_name);

    // Set editing node
    const node_id = $(ev.target).parents('li').get(0).dataset.id;
    $('#editing-node').val(node_id);
    if (node_id != '') {
      $('button[data-action="add-mapping"]').prop('disabled', false);
    }
    else {
      $('button[data-action="add-mapping"]').prop('disabled', true);
    }

    // Set mapping
    setCurrentMapping(node_id);
  });

  function saveCurrentMapping() {
    const editing_node = $('#editing-node').val();
    if (editing_node == '') {
      return;
    }

    const mapping = {};
    const table_rows = $('#mapping-table').find('div[name="mapping-row"]');
    table_rows.each((_, table_row) => {
      // rocrate property
      const rocrate_property_select = $(table_row).find('select[name="select-rocrate-property"]');
      const rocrate_property = rocrate_property_select.val();

      // metadata property
      let metadata_property = null;
      const metadata_property_row = $(table_row).find('div[name="metadata-property-row"]');
      if (metadata_property_row.length == 1) {
        metadata_property = getMetadataProperty(metadata_property_row);
      }
      else if (metadata_property_row.length > 1) {
        metadata_property = [];
        metadata_property_row.each((_, elem) => {
          metadata_property.push(getMetadataProperty($(elem)));
        });
      }
      mapping[rocrate_property] = metadata_property;
    });

    page_global.node_mapping[editing_node] = mapping;
  };

  function getMetadataProperty(metadata_property_column) {
    const editing_node = $('#editing-node').val();
    if (editing_node == 'file') {
      let metadata_property = '';
      const items = metadata_property_column.find('div[name="metadata-file-property-item"]');
      items.each((_, item) => {
        const item_key = $(item).find('select').val();
        metadata_property = metadata_property + '.' + item_key;
      });
      if (metadata_property != '') {
        metadata_property = metadata_property.slice(1);
      }
      return metadata_property;
    }

    const lang_check = metadata_property_column.find('input[name="check-language"]');
    if (!lang_check.is(':checked')) {
      let metadata_property = '';
      const items = metadata_property_column.find('div[name="metadata-property-item"]');
      items.each((_, item) => {
        let item_key = $(item).find('select').val();
        const index_check = $(item).find('input[name="check-list-index"]');
        if (index_check.is(':checked')) {
          item_key = item_key + '[' + $(item).find('input[type=number]').val() + ']';
        }
        metadata_property = metadata_property + '.' + item_key;
      });
      if (metadata_property != '') {
        metadata_property = metadata_property.slice(1);
      }
      return metadata_property;
    }
    else {
      let metadata_property_value = '';
      let metadata_property_lang = '';
      const items = metadata_property_column.find('div[name="metadata-property-item-with-lang"]');
      items.each((_, item) => {
        const item_value_key = $(item).find('select[name="select-metadata-property-value"]').val();
        if (item_value_key != '') {
          metadata_property_value = metadata_property_value + '.' + item_value_key;
        }
        const item_lang_key = $(item).find('select[name="select-metadata-property-lang"]').val();
        if (item_lang_key != '') {
          metadata_property_lang = metadata_property_lang + '.' + item_lang_key;
        }
      });
      if (metadata_property_value != '') {
        metadata_property_value = metadata_property_value.slice(1);
      }
      if (metadata_property_lang != '') {
        metadata_property_lang = metadata_property_lang.slice(1);
      }
      return {
        value: metadata_property_value,
        lang: metadata_property_lang,
      };
    }
  };

  function initCurrentMapping() {
    $('#mapping-table').empty();
  };

  function setCurrentMapping(node_id) {
    if (!(node_id in page_global.node_mapping)) {
      return;
    }
    const node_mapping = page_global.node_mapping[node_id];
    if (Object.keys(node_mapping).length == 0) {
      return;
    }

    for (let [key, value] of Object.entries(node_mapping)) {
      // Add table row
      const added_row = addMapping();

      // Set RO-Crate property
      const rocrate_property_select = added_row.find('select[name="select-rocrate-property"]');
      rocrate_property_select.val(key);

      // Set Metadata property
      const metadata_property_column = added_row.find('div[name="metadata-property-column"]');
      if (value instanceof Array) {
        value.forEach((elem) => {
          setMetadataProperty(metadata_property_column, elem);
        });
      }
      else {
        setMetadataProperty(metadata_property_column, value);
      }
    }
  };

  function setMetadataProperty(metadata_property_column, property_key) {
    // Add metadata property input area
    const add_button = metadata_property_column.find('button[data-action="add-metadata-property"]');
    const added_property = addMetadataProperty(add_button);

    const editing_node = $('#editing-node').val();
    if (editing_node == 'file') {
      const keys = splitPropertyKey(property_key);
      const length = keys.length;
      let item_properties = page_global.item_properties;
      for (let ii = 0; ii < length; ii++) {
        let input_area = null;
        if (ii == 0) {
          input_area = metadata_property_column.find('div[name="metadata-file-property-item"]').last();
          item_properties = item_properties[keys[ii].key];
        }
        else {
          // Add input area
          input_area = $('#template-metadata-file-property-item :first').clone(true);
          const tmp_area = metadata_property_column.find('div[name="metadata-file-property-item"]').last();
          tmp_area.after(input_area);

          const sub_items = item_properties['properties'];
          const select = input_area.find('select');
          for (let [key, value] of Object.entries(sub_items)) {
            select.append($('<option>').html(value['title']).val(key));
          }
          item_properties = sub_items[keys[ii].key];
        }
        input_area.find('select').val(keys[ii].key);
      }
    }
    else {
      if (typeof property_key == 'string') {
        const keys = splitPropertyKey(property_key);
        const length = keys.length;
        let item_properties = page_global.item_properties;
        for (let ii = 0; ii < length; ii++) {
          let input_area = null;
          if (ii == 0) {
            input_area = metadata_property_column.find('div[name="metadata-property-item"]').last();
            item_properties = item_properties[keys[ii].key];
          }
          else {
            // Add input area
            input_area = $('#template-metadata-property-item :first').clone(true);
            const tmp_area = metadata_property_column.find('div[name="metadata-property-item"]').last();
            tmp_area.after(input_area);

            const sub_items = item_properties['properties'];
            const select = input_area.find('select');
            for (let [key, value] of Object.entries(sub_items)) {
              select.append($('<option>').html(value['title']).val(key));
            }
            item_properties = sub_items[keys[ii].key];
          }

          input_area.find('select').val(keys[ii].key);
          if (item_properties['type'] == 'array') {
            input_area.find('label').removeClass('invisible');
          }
          if (keys[ii].index != null) {
            input_area.find('input[type="checkbox"]').prop('checked', true);
            const index_text = input_area.find('input[type="number"]');
            index_text.removeClass('invisible');
            index_text.val(keys[ii].index);
          }
        }
      }
      else {
        added_property.find('input[name="check-language"]').prop('checked', true);
        added_property.find('div[name="metadata-property"]').addClass('hide');
        added_property.find('div[name="metadata-property-with-lang"]').removeClass('hide');

        const value_keys = splitPropertyKey(property_key['value'])
        const lang_keys = splitPropertyKey(property_key['lang'])
        const length = Math.max(value_keys.length, lang_keys.length);
        let item_properties_value = page_global.item_properties;
        let item_properties_lang = page_global.item_properties;
        for (let ii = 0; ii < length; ii++) {
          let input_area = null;
          if (ii == 0) {
            input_area = metadata_property_column.find('div[name="metadata-property-item-with-lang"]').last();
            item_properties_value = item_properties_value[value_keys[ii].key];
            item_properties_lang = item_properties_lang[lang_keys[ii].key];
          }
          else {
            // Add input area
            input_area = $('#template-metadata-property-item-with-lang :first').clone(true);
            const tmp_area = metadata_property_column.find('div[name="metadata-property-item-with-lang"]');
            tmp_area.after(input_area);

            if (value_keys.length > ii) {
              const sub_items = item_properties_value['properties'];
              const select = input_area.find('select[name="select-metadata-property-value"]');
              for (let [key, value] of Object.entries(sub_items)) {
                select.append($('<option>').html(value['title']).val(key));
              }
              item_properties_value = sub_items[value_keys[ii].key];
            }
            if (lang_keys.length > ii) {
              const sub_items = item_properties_lang['properties'];
              const select = input_area.find('select[name="select-metadata-property-lang"]');
              for (let [key, value] of Object.entries(sub_items)) {
                select.append($('<option>').html(value['title']).val(key));
              }
              item_properties_lang = sub_items[lang_keys[ii].key];
            }
          }

          if (value_keys.length > ii) {
            const select = input_area.find('select[name="select-metadata-property-value"]');
            select.val(value_keys[ii].key);
            select.removeClass('invisible');
          }
          if (lang_keys.length > ii) {
            const select = input_area.find('select[name="select-metadata-property-lang"]');
            select.val(lang_keys[ii].key);
            select.removeClass('invisible');
          }
        }
      }
    }
  }

  function splitPropertyKey(property_key) {
    return property_key.split('.').map((value) => {
      const extract_index = value.split(/\[|\]/);
      let key = '';
      let index = null;
      if (extract_index.length == 1) {
        key = extract_index[0];
      }
      else {
        key = extract_index[0];
        index = extract_index[1];
      }

      return {
        key: key,
        index: index,
      };
    });
  }

  $('button[type="button"]').on('click', (ev) => {
    page_global.hasEdit = true;
    const target = ev.currentTarget;
    const action = target.dataset.action;
    if (action == 'add-node') {
      addNode(target);
    }
    else if (action == 'del-node') {
      delNode(target);
    }
    else if (action == 'add-mapping') {
      const editing_node = $('#editing-node').val();
      if (editing_node == '') {
        return;
      }

      // Add mapping
      const added_row = addMapping();

      // Add metadata property
      const add_button = added_row.find('button[data-action="add-metadata-property"]');
      addMetadataProperty(add_button);
    }
    else if (action == 'del-mapping') {
      delMapping(target);
    }
    else if (action == 'add-metadata-property') {
      addMetadataProperty(target);
    }
    else if (action == 'del-metadata-property') {
      delMetadataProperty(target);
    }
  });

  function addNode(target) {
    // Add node
    const template = $('#template-node-ul :first').clone(true);
    $(target).closest('li').before(template);

    // Add node id
    const node_id = 'node' + page_global.node_index_counter;
    template.get(0).dataset.id = node_id;
    page_global.node_index_counter = page_global.node_index_counter + 1;

    return template;
  }

  function delNode(target) {
    // Delete node
    $(target).closest('li').remove();
  }

  function addMapping() {
    let template = null;
    const editing_node = $('#editing-node').val();
    if (editing_node == 'file') {
      template = $('#template-mapping-file-row :first').clone(true);
    }
    else {
      template = $('#template-mapping-row :first').clone(true);
    }

    // Add mapping table row
    $('#mapping-table').append(template);
    $('#mapping-table').append('<hr>');

    return template;
  }

  function delMapping(target) {
    // Delete mapping table row
    const table_row = $(target).closest('div[name="mapping-row"]');
    table_row.next().remove();  // remove hr
    table_row.remove();
  }

  function addMetadataProperty(target) {
    let template = null;
    const editing_node = $('#editing-node').val();
    if (editing_node == 'file') {
      template = $('#template-metadata-file-property-row :first').clone(true);
    }
    else {
      template = $('#template-metadata-property-row :first').clone(true);
    }

    // Add metadata property
    $(target).closest('div[name="button-row"]').before(template);

    return template;
  }

  function delMetadataProperty(target) {
    // Remove metadata property
    $(target).closest('div[name="metadata-property-row"]').remove();
  }

  $('input[name="check-language"]').on('click', (ev) => {
    const check_value = $(ev.target).is(':checked');
    const column = $(ev.target).parents('div[name="metadata-property-row"]');
    const property = column.find('div[name="metadata-property"]');
    const property_with_lang = column.find('div[name="metadata-property-with-lang"]');
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

  $('select[name="select-metadata-property"]').change((ev) => {
    page_global.hasEdit = true;

    // Init input area
    const input_area = $(ev.target).closest('div[name="metadata-property-item"]');
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
    if ('properties' in selected_prop) {
      // Create child select box
      const template = $('#template-metadata-property-item :first').clone(true);
      input_area.after(template);

      // Set child property
      const child_select = template.find('select');
      const child_props = selected_prop['properties'];
      for (let [key, value] of Object.entries(child_props)) {
        child_select.append($('<option>').html(value['title']).val(key));
      }
    }
  });

  $('select[name="select-metadata-property-value"], select[name="select-metadata-property-lang"]').change((ev) => {
    page_global.hasEdit = true;
    const select_name = $(ev.target).prop('name');

    // Init input area
    const select_list = $(ev.target).closest('div[name="metadata-property-with-lang"]').find(`select[name="${select_name}"]`);
    const target_index = select_list.index(ev.target);
    select_list.each((index, elem) => {
      if (index <= target_index) {
        return;
      }
      // Init child select box
      $(elem).children().remove();
      $(elem).append($('<option>').html('').val(''));
    });

    // Delete waste area
    removeWasteArea(ev.target);

    if ($(ev.target).val() == '') {
      return;
    }

    // Get selected property
    const selected_prop_key = getSelectedKeys(ev.target, select_name);
    const selected_prop = getSelectedProp(selected_prop_key);

    if ('properties' in selected_prop) {
      const input_area = $(ev.target).closest('div[name="metadata-property-item-with-lang"]');
      if (input_area.next().length == 0) {
        // Add child property select box
        const template = $('#template-metadata-property-item-with-lang :first').clone(true);
        input_area.after(template);
      }

      // Set child property
      const child_select = $(ev.target)
        .closest('div[name="metadata-property-with-lang"]')
        .find(`select[name="${select_name}"]`)
        .eq(selected_prop_key.length);
      const child_props = selected_prop['properties'];
      for (let [key, value] of Object.entries(child_props)) {
        child_select.append($('<option>').html(value['title']).val(key));
      }
      child_select.removeClass('invisible');
    }
  });

  $('select[name="select-metadata-file-property"]').change((ev) => {
    page_global.hasEdit = true;

    // Init input area
    const input_area = $(ev.target).closest('div[name="metadata-file-property-item"]');
    input_area.nextAll().remove();

    if ($(ev.target).val() == '') {
      return;
    }

    // Get selected property
    const selected_prop_key = getSelectedKeys(ev.target);
    const selected_prop = getSelectedProp(selected_prop_key);

    // Add child property select box
    if ('properties' in selected_prop) {
      // Create child select box
      const template = $('#template-metadata-file-property-item :first').clone(true);
      input_area.after(template);

      // Set child property
      const child_select = template.find('select');
      const child_props = selected_prop['properties'];
      for (let [key, value] of Object.entries(child_props)) {
        child_select.append($('<option>').html(value['title']).val(key));
      }
    }
  });

  function getSelectedKeys(select_box, select_name) {
    let select_list = null;
    if (select_name == null) {
      select_list = $(select_box).closest('div[name="metadata-property"]').find('select');
    }
    else {
      select_list = $(select_box).closest('div[name="metadata-property-with-lang"]').find(`select[name="${select_name}"]`);
    }

    const keys = [];
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
    let selected_prop = page_global.item_properties;
    for (let key of keys) {
      if ('properties' in selected_prop) {
        selected_prop = selected_prop['properties'];
      }
      selected_prop = selected_prop[key];
    }
    return selected_prop;
  };

  function removeWasteArea(select_box) {
    let find = false;
    const select_value_list = $(select_box).closest('div[name="metadata-property-with-lang"]').find('select[name="select-metadata-property-value"]');
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
    const select_lang_list = $(select_box).closest('div[name="metadata-property-with-lang"]').find('select[name="select-metadata-property-lang"]');
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
    const input_areas = $(select_box).closest('div[name="metadata-property-item-with-lang"]').parent().find('div[name="metadata-property-item-with-lang"]');
    input_areas.eq(valid_num - 1).nextAll().remove();
  }

  $('#mapping-submit').on('click', (ev) => {
    saveCurrentMapping();
    const rocrate_mapping = buildMappingData();
    const data = {
      item_type_id: parseInt(page_global.src_mapping_name),
      mapping: rocrate_mapping,
    };
    send(page_global.url, data);
  });

  function buildMappingData() {
    const rocrate_mapping = {};

    // item_type_id
    rocrate_mapping['item_type_id'] = parseInt(page_global.src_mapping_name);

    // entity_types
    rocrate_mapping['entity_types'] = [];
    const layer_names = $('#layer-base').find('input[type="text"]');
    layer_names.each((_, layer_name) => {
      rocrate_mapping['entity_types'].push($(layer_name).val());
    });

    // tree_structure
    const root_node_li = $('#tree-base :first');
    rocrate_mapping['tree_structure'] = buildMappingNode(root_node_li, 0);

    // file
    rocrate_mapping['file'] = {
      map: page_global.node_mapping['file'],
    };

    return rocrate_mapping;
  };

  function buildMappingNode(node_li, depth) {
    const node = {};
    node['depth'] = depth;
    node['name'] = node_li.find('input[type="text"]').eq(0).val();

    // map
    const node_id = node_li.get(0).dataset.id;
    if (node_id in page_global.node_mapping) {
      node['map'] = page_global.node_mapping[node_id];
    }
    else {
      node['map'] = {};
    }

    // children
    const child_node_li = node_li.children('ul').children('li[name="node-li"]');
    if (child_node_li.length > 0) {
      node['children'] = [];
      child_node_li.each((_, elem) => {
        node['children'].push(buildMappingNode($(elem), depth + 1));
      });
    }

    return node;
  };

  function send(url, data) {
    $.ajax({
      method: 'POST',
      url: url,
      async: true,
      contentType: 'application/json',
      dataType: 'json',
      data: JSON.stringify(data),
      success: (data, textStatus) => {
        page_global.hasEdit = false;
        $('html,body').scrollTop(0);
        addAlert(data.msg);
      },
      error: (textStatus, errorThrown) => {
        $('.modal-body').text('Error: ' + JSON.stringify(textStatus));
        $('#message-modal').modal('show');
      }
    });
  }

  function createNode(node_mapping, node_li) {
    // Set node name
    const node_name = node_mapping['name'];
    const node_name_text = node_li.find('input[name="node-name"]').eq(0);
    node_name_text.val(node_name);

    // Set node mapping
    const node_id = node_li.get(0).dataset.id;
    page_global.node_mapping[node_id] = node_mapping['map'];

    // Create child node
    const addButton = node_li.children('ul').children('li[name="button-li"]').find('button');
    if ('children' in node_mapping) {
      for (let child_node_mapping of node_mapping['children']) {
        const added_node = addNode(addButton);
        const child_node_id = added_node.get(0).dataset.id
        const child_node_li = node_li.find(`li[data-id="${child_node_id}"]`);
        createNode(child_node_mapping, child_node_li);
      }
    }
  };

  // Init display
  if (page_global.rocrate_mapping != '') {
    // Create layer
    const entity_types = page_global.rocrate_mapping.entity_types;
    $('#layer-num').val(entity_types.length - 1);
    for (let ii = 1; ii < entity_types.length; ii++) {
      addLayer();
      const layer_text = $('#layer-base').find('input[name="layer-name"]').eq(-1);
      layer_text.val(entity_types[ii]);
    }

    // Create tree structure
    const tree_structure = page_global.rocrate_mapping.tree_structure;
    const root_node_li = $('#tree-base :first');
    createNode(tree_structure, root_node_li);
    page_global.node_mapping['file'] = page_global.rocrate_mapping.file.map;
  }
});
