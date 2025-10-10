$(() => {
  $('#message-modal').modal({ show: false })

  const page_global = {
    url: '/admin/itemtypes/rocrate_mapping',
    src_mapping_name: $('#select-item-type').val(),
    dst_mapping_name: $('#select-item-type').val(),
    hasEdit: false,
    item_properties: null,
    rocrate_mapping: null,
    node_name: {},
    node_mapping: {},
    node_index_counter: 0,
  };
  const item_properties_str = $('#item-properties').text();
  page_global.item_properties = JSON.parse(item_properties_str);
  const rocrate_mapping_str = $('#rocrate-mapping').text();
  page_global.rocrate_mapping = JSON.parse(rocrate_mapping_str);

  $('#select-item-type').change((ev) => {
    page_global.dst_mapping_name = $(ev.target).val();
    if (page_global.hasEdit) {
      const title = $('#confirm-title').text();
      const body = $('#confirm-body').text();
      $('.modal-title').text(title);
      $('.modal-body').text(body);
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
  });

  $('#btn-confirm').on('click', (ev) => {
    window.location.href = page_global.url + '/' + page_global.dst_mapping_name;
  });

  const selectors = [
    'input#layer-num',
    'input[name="layer-name"]',
    'input[name="node-name-i18n"]',
    'select[name="select-rocrate-property"]',
    'input[name="list-index"]',
    'input[name="text-static-value"]',
  ];
  $(selectors.join(',')).change((ev) => {
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
  };

  $('.arrow').on('click', (ev) => {
    $(ev.target).parent().nextAll('.nested').toggleClass('active');
    $(ev.target).toggleClass('arrow-down');
  });

  $('input[name="select-node"]').change((ev) => {
    if (!checkNode()) {
      const editing_node_id = $('#editing-node').val();
      const editing_node_li = $('#tree-base').find(`li[data-id="${editing_node_id}"]`);
      editing_node_li.find('input[name="select-node"]').first().prop('checked', true);
      return;
    }

    saveCurrentNode();
    initCurrentNode();

    // Set editing node
    const node_id = $(ev.target).closest('li').get(0).dataset.id;
    $('#editing-node').val(node_id);

    setCurrentNode();

    $(window).scrollTop($('#area-node').position().top);
  });

  function saveCurrentNode() {
    saveCurrentNodeName();
    saveCurrentMapping();
  };

  function saveCurrentNodeName() {
    const node_id = $('#editing-node').val();
    if (node_id == '') {
      return;
    }
    if (node_id == 'root' || node_id == 'file') {
      return;
    }

    // save node name
    const node_name = $('#node-name').val();
    const name_i18n = {};
    $('input[name="node-name-i18n"]').each((_, textbox) => name_i18n[textbox.dataset.lang] = $(textbox).val());
    page_global.node_name[node_id] = {
      name: node_name,
      name_i18n: name_i18n,
    };
  };

  function saveCurrentMapping() {
    const node_id = $('#editing-node').val();
    if (node_id == '') {
      return;
    }

    const mapping = {};
    const table_rows = $('#mapping-table-body').find('div[name="mapping-row"]');
    table_rows.each((_, table_row) => {
      // rocrate property
      const rocrate_property = $(table_row).find('select[name="select-rocrate-property"]').val();

      // item property
      let item_property = null;
      const item_property_row = $(table_row).find('div[name="item-property-row"]');
      if (item_property_row.length == 1) {
        item_property = getItemProperty(item_property_row);
      }
      else if (item_property_row.length > 1) {
        item_property = [];
        item_property_row.each((_, elem) => {
          item_property.push(getItemProperty($(elem)));
        });
      }
      mapping[rocrate_property] = item_property;
    });

    page_global.node_mapping[node_id] = mapping;
  };

  function getItemProperty(item_property_row) {
    if (item_property_row.find('div[name="static-value"]').length > 0) {
      return getItemPropertyValueStatic(item_property_row);
    }

    const editing_node_id = $('#editing-node').val();
    if (editing_node_id == 'file') {
      return getItemPropertyValueFile(item_property_row);
    }

    const lang_check = item_property_row.find('input[name="check-language"]');
    if (lang_check.is(':checked')) {
      return getItemPropertyValueLang(item_property_row);
    }

    return getItemPropertyValue(item_property_row);
  };

  function getItemPropertyValue(item_property_row) {
    let item_property = '';
    const fields = item_property_row.find('div[name="item-property-field"]');
    fields.each((_, field) => {
      let field_key = $(field).find('select').val();
      const index_check = $(field).find('input[name="check-list-index"]');
      if (index_check.is(':checked')) {
        field_key = field_key + '[' + $(field).find('input[name="list-index"]').val() + ']';
      }
      item_property = item_property + '.' + field_key;
    });
    if (item_property != '') {
      item_property = item_property.slice(1);
    }
    return item_property;
  };

  function getItemPropertyValueLang(item_property_row) {
    let item_property_value = '';
    let item_property_lang = '';
    const fields = item_property_row.find('div[name="item-property-field-with-lang"]');
    fields.each((_, field) => {
      const field_key_value = $(field).find('select[name="select-item-property-value"]').val();
      if (field_key_value != '') {
        item_property_value = item_property_value + '.' + field_key_value;
      }
      const field_key_lang = $(field).find('select[name="select-item-property-lang"]').val();
      if (field_key_lang != '') {
        item_property_lang = item_property_lang + '.' + field_key_lang;
      }
    });
    if (item_property_value != '') {
      item_property_value = item_property_value.slice(1);
    }
    if (item_property_lang != '') {
      item_property_lang = item_property_lang.slice(1);
    }
    return {
      value: item_property_value,
      lang: item_property_lang,
    };
  };

  function getItemPropertyValueFile(item_property_row) {
    let item_property = '';
    const fields = item_property_row.find('div[name="item-property-field"]');
    fields.each((_, field) => {
      const field_key = $(field).find('select').val();
      item_property = item_property + '.' + field_key;
    });
    if (item_property != '') {
      item_property = item_property.slice(1);
    }
    return item_property;
  };

  function getItemPropertyValueStatic(item_property_row) {
    const item_property = item_property_row.find('input[name="text-static-value"]').val();
    return {
      static_value: item_property,
    }
  };

  function initCurrentNode() {
    initCurrentNodeName();
    initCurrentMapping();
  };

  function initCurrentNodeName() {
    $('#node-name').val('');
    $('#node-name').prop('disabled', true);
    $('input[name="node-name-i18n"]').val('');
    $('input[name="node-name-i18n"]').prop('disabled', true);

    // Init error message
    $('#node-name-setting').find('div[name="node-name-message"]').addClass('hide');
  };

  function initCurrentMapping() {
    $('#mapping-table-body').empty();

    $('label#rocrate-property-label').text('');
    $('label#item-property-label').text('');
    $('button[data-action="add-mapping"]').prop('disabled', true);
    $('button[data-action="add-mapping-static"]').prop('disabled', true);
  };

  function setCurrentNode() {
    setCurrentNodeName();
    setCurrentMapping();
  };

  function setCurrentNodeName() {
    const node_id = $('#editing-node').val();
    if (node_id == '') {
      return;
    }

    // Activate add button
    if (node_id != 'root' && node_id != 'file') {
      $('#node-name').prop('disabled', false);
      $('input[name="node-name-i18n"]').prop('disabled', false);
    }

    const node_name = page_global.node_name[node_id];
    $('#node-name').val(node_name['name']);

    const name_i18n = node_name['name_i18n'];
    if (name_i18n != null) {
      $('input[name="node-name-i18n"]').each((_, textbox) => $(textbox).val(name_i18n[textbox.dataset.lang]));
    }
  };

  function setCurrentMapping() {
    const node_id = $('#editing-node').val();
    if (node_id == '') {
      return;
    }

    // Set node path
    setNodePath(node_id);

    // Set item type name
    const item_type_name = $('#select-item-type option:selected').text();
    $('label#item-property-label').text(item_type_name);

    // Activate add button
    $('button[data-action="add-mapping"]').prop('disabled', false);
    $('button[data-action="add-mapping-static"]').prop('disabled', false);

    const node_mapping = page_global.node_mapping[node_id];
    if (Object.keys(node_mapping).length == 0) {
      return;
    }

    for (let [rocrate_property, item_property] of Object.entries(node_mapping)) {
      if (item_property instanceof Object && !(item_property instanceof Array)) {
        if ('static_value' in item_property) {
          const added_row = addMappingStatic();

          // Set RO-Crate property
          const rocrate_property_select = added_row.find('select[name="select-rocrate-property"]');
          rocrate_property_select.val(rocrate_property);

          // Set item property
          const item_property_cell = added_row.find('div[name="item-property-cell"]');
          setItemPropertyValueStatic(item_property_cell, item_property);
          continue;
        }
      }

      // Add table row
      const added_row = addMapping();

      // Set RO-Crate property
      const rocrate_property_select = added_row.find('select[name="select-rocrate-property"]');
      rocrate_property_select.val(rocrate_property);

      // Set item property
      const item_property_cell = added_row.find('div[name="item-property-cell"]');
      if (item_property instanceof Array) {
        item_property.forEach((elem) => {
          setItemProperty(item_property_cell, elem);
        });
      }
      else {
        setItemProperty(item_property_cell, item_property);
      }
    }
  };

  function setNodePath() {
    const node_id = $('#editing-node').val();
    if (node_id == '') {
      return;
    }

    let node_path = '';
    const selected_radio = $('#tree-base').find(`li[data-id="${node_id}"]`).children('div[name="node-contents"]').children('div[name="node"]').find('input[name="select-node"]');
    selected_radio.parents('li').each((_, elem) => {
      const node_text = $(elem).children('div[name="node-contents"]').children().eq(1).find('input[name="node-name"]').val();
      node_path = node_text + '/' + node_path;
    });
    node_path = node_path.slice(0, -1);
    $('label#rocrate-property-label').text(node_path);
  };

  function setItemProperty(item_property_cell, item_property) {
    // Add item property input area
    const add_button = item_property_cell.find('button[data-action="add-item-property"]');
    const added_property = addItemProperty(add_button);

    const editing_node = $('#editing-node').val();
    if (editing_node == 'file') {
      setItemPropertyValueFile(item_property_cell, item_property);
      return;
    }

    if (typeof item_property == 'string') {
      setItemPropertyValue(item_property_cell, item_property);
      return;
    }
    else {
      added_property.find('input[name="check-language"]').prop('checked', true);
      added_property.find('div[name="item-property"]').addClass('hide');
      added_property.find('div[name="item-property-with-lang"]').removeClass('hide');
      setItemPropertyValueLang(item_property_cell, item_property);
      return;
    }
  };

  function setItemPropertyValue(item_property_cell, item_property) {
    if (item_property == '') {
      return;
    }

    const field_keys = splitPropertyKey(item_property);
    let item_properties = page_global.item_properties;
    for (let ii = 0; ii < field_keys.length; ii++) {
      let field = null;
      if (ii == 0) {
        field = item_property_cell.find('div[name="item-property-field"]').last();
        item_properties = item_properties[field_keys[ii].key];
      }
      else {
        // Add field
        field = $('#template-item-property-field :first').clone(true);
        const last_field = item_property_cell.find('div[name="item-property-field"]').last();
        last_field.after(field);

        const sub_items = item_properties['properties'];
        const select = field.find('select');
        for (let [key, value] of Object.entries(sub_items)) {
          select.append($('<option>').html(value['title']).val(key));
        }
        item_properties = sub_items[field_keys[ii].key];
      }

      field.find('select').val(field_keys[ii].key);
      if (item_properties['type'] == 'array') {
        field.find('label').removeClass('invisible');
      }
      if (field_keys[ii].index != null) {
        field.find('input[name="check-list-index"]').prop('checked', true);
        const index_text = field.find('input[name="list-index"]');
        index_text.removeClass('invisible');
        index_text.val(field_keys[ii].index);
      }
    }
  };

  function setItemPropertyValueLang(item_property_cell, item_property) {
    if (item_property == '') {
      return;
    }

    const field_keys_value = splitPropertyKey(item_property['value'])
    const field_keys_lang = splitPropertyKey(item_property['lang'])
    const length = Math.max(field_keys_value.length, field_keys_lang.length);
    let item_properties_value = page_global.item_properties;
    let item_properties_lang = page_global.item_properties;
    for (let ii = 0; ii < length; ii++) {
      let field = null;
      if (ii == 0) {
        field = item_property_cell.find('div[name="item-property-field-with-lang"]').last();
        item_properties_value = item_properties_value[field_keys_value[ii].key];
        item_properties_lang = item_properties_lang[field_keys_lang[ii].key];
      }
      else {
        // Add field
        field = $('#template-item-property-field-with-lang :first').clone(true);
        const last_field = item_property_cell.find('div[name="item-property-field-with-lang"]').last();
        last_field.after(field);

        if (field_keys_value.length > ii) {
          const sub_items = item_properties_value['properties'];
          const select = field.find('select[name="select-item-property-value"]');
          for (let [key, value] of Object.entries(sub_items)) {
            select.append($('<option>').html(value['title']).val(key));
          }
          item_properties_value = sub_items[field_keys_value[ii].key];
        }
        if (field_keys_lang.length > ii) {
          const sub_items = item_properties_lang['properties'];
          const select = field.find('select[name="select-item-property-lang"]');
          for (let [key, value] of Object.entries(sub_items)) {
            select.append($('<option>').html(value['title']).val(key));
          }
          item_properties_lang = sub_items[field_keys_lang[ii].key];
        }
      }

      if (field_keys_value.length > ii) {
        const select = field.find('select[name="select-item-property-value"]');
        select.val(field_keys_value[ii].key);
        select.removeClass('invisible');
      }
      if (field_keys_lang.length > ii) {
        const select = field.find('select[name="select-item-property-lang"]');
        select.val(field_keys_lang[ii].key);
        select.removeClass('invisible');
      }
    }
  };

  function setItemPropertyValueFile(item_property_cell, item_property) {
    if (item_property == '') {
      return;
    }

    const field_keys = splitPropertyKey(item_property);
    let item_properties = page_global.item_properties;
    for (let ii = 0; ii < field_keys.length; ii++) {
      let field = null;
      if (ii == 0) {
        field = item_property_cell.find('div[name="item-property-field"]').last();
        item_properties = item_properties[field_keys[ii].key];
      }
      else {
        // Add input field
        field = $('#template-item-property-field-file :first').clone(true);
        const last_field = item_property_cell.find('div[name="item-property-field"]').last();
        last_field.after(field);

        const sub_items = item_properties['properties'];
        const select = field.find('select');
        for (let [key, value] of Object.entries(sub_items)) {
          select.append($('<option>').html(value['title']).val(key));
        }
        item_properties = sub_items[field_keys[ii].key];
      }
      field.find('select').val(field_keys[ii].key);
    }
  };

  function setItemPropertyValueStatic(item_property_cell, item_property) {
    if (item_property == '') {
      return;
    }

    item_property_cell.find('input[name="text-static-value"]').val(item_property['static_value']);
  };

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
  };

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

      // Add item property
      const add_button = added_row.find('button[data-action="add-item-property"]');
      addItemProperty(add_button);
    }
    else if (action == 'add-mapping-static') {
      const editing_node = $('#editing-node').val();
      if (editing_node == '') {
        return;
      }
      addMappingStatic();
    }
    else if (action == 'del-mapping') {
      delMapping(target);
    }
    else if (action == 'add-item-property') {
      addItemProperty(target);
    }
    else if (action == 'del-item-property') {
      delItemProperty(target);
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

    page_global.node_name[node_id] = {
      name: '',
      name_i18n: { ja: '', en: '', },
    };
    page_global.node_mapping[node_id] = {};

    return template;
  };

  function delNode(target) {
    // Delete node
    $(target).closest('li').remove();

    if ($('#tree-base').find('input[name="select-node"]:checked').length == 0) {
      $('#editing-node').val('');
      initCurrentNode();
    }
  };

  function addMapping() {
    let template = null;
    const editing_node = $('#editing-node').val();
    if (editing_node == 'file') {
      template = $('#template-mapping-row-file :first').clone(true);
    }
    else {
      template = $('#template-mapping-row :first').clone(true);
    }

    // Add mapping table row
    $('#mapping-table-body').append(template);
    $('#mapping-table-body').append('<hr>');

    return template;
  };

  function addMappingStatic() {
    const template = $('#template-mapping-static-row :first').clone(true);

    // Add mapping table row
    $('#mapping-table-body').append(template);
    $('#mapping-table-body').append('<hr>');

    // add property selectbox
    const editing_node = $('#editing-node').val();
    if (editing_node == 'file') {
      const select = $('#template-mapping-row-file').find('.form-group').clone(true);
      template.find('div[name="rocrate-property"]').append(select);
    }
    else {
      const select = $('#template-mapping-row').find('.form-group').clone(true);
      template.find('div[name="rocrate-property"]').append(select);
    }

    return template;
  };

  function delMapping(target) {
    // Delete mapping table row
    const table_row = $(target).closest('div[name="mapping-row"]');
    table_row.next().remove();  // remove hr
    table_row.remove();
  };

  function addItemProperty(target) {
    let template = null;
    const editing_node = $('#editing-node').val();
    if (editing_node == 'file') {
      template = $('#template-item-property-row-file :first').clone(true);
    }
    else {
      template = $('#template-item-property-row :first').clone(true);
    }

    // Add item property
    $(target).closest('div[name="button-row"]').before(template);

    // Disable delete button if number of properties is 1
    const item_property_rows = $(target).closest('div[name="item-property-cell"]').find('div[name="item-property-row"]');
    if (item_property_rows.length > 1) {
      item_property_rows.find('button[data-action="del-item-property"]').each((_, v) => $(v).prop('disabled', false));
    }
    else {
      item_property_rows.find('button[data-action="del-item-property"]').each((_, v) => $(v).prop('disabled', true));
    }

    return template;
  };

  function delItemProperty(target) {
    const item_property_cell = $(target).closest('div[name="item-property-cell"]');

    // Remove item property
    $(target).closest('div[name="item-property-row"]').remove();

    // Disable delete button if number of properties is 1
    const item_property_rows = item_property_cell.find('div[name="item-property-row"]');
    if (item_property_rows.length > 1) {
      item_property_rows.find('button[data-action="del-item-property"]').each((_, v) => $(v).prop('disabled', false));
    }
    else {
      item_property_rows.find('button[data-action="del-item-property"]').each((_, v) => $(v).prop('disabled', true));
    }
  };

  $('input[name="node-name"]').change((ev) => {
    page_global.hasEdit = true;

    const node_id = $(ev.target).closest('li').get(0).dataset.id;
    const node_name = $(ev.target).val();
    page_global.node_name[node_id]['name'] = node_name;
    setNodePath();

    const editing_node_id = $('#editing-node').val();
    if (node_id == editing_node_id) {
      $('#node-name').val(node_name);
    }
  });

  $('input#node-name').change((ev) => {
    page_global.hasEdit = true;

    const node_name = $(ev.target).val();

    const editing_node_id = $('#editing-node').val();
    const editing_node_li = $('#tree-base').find(`li[data-id="${editing_node_id}"]`);
    const editing_node_text = editing_node_li.find('input[name="node-name"]');
    editing_node_text.val(node_name);

    setNodePath();
  });

  $('input[name="check-language"]').on('click', (ev) => {
    page_global.hasEdit = true;

    const check_value = $(ev.target).is(':checked');
    const item_property_row = $(ev.target).parents('div[name="item-property-row"]');
    const item_property = item_property_row.find('div[name="item-property"]');
    const item_property_lang = item_property_row.find('div[name="item-property-with-lang"]');
    if (check_value) {
      item_property.addClass('hide');
      item_property_lang.removeClass('hide');
    }
    else {
      item_property.removeClass('hide');
      item_property_lang.addClass('hide');
    }
  });

  $('input[name="check-list-index"]').on('click', (ev) => {
    page_global.hasEdit = true;

    const index_text = $(ev.target).closest('div[name="item-property-field"]').find('input[name="list-index"]');
    index_text.toggleClass('invisible');
  });

  $('select[name="select-item-property"]').change((ev) => {
    page_global.hasEdit = true;

    // Init field
    const field = $(ev.target).closest('div[name="item-property-field"]');
    field.nextAll().remove();
    field.find('input[name="list-index"]').addClass('invisible');
    field.find('label').addClass('invisible');
    field.find('input[name="check-list-index"]').prop('checked', false);

    if ($(ev.target).val() == '') {
      return;
    }

    // Get selected property
    const selected_prop_key = getSelectedKeys(ev.target);
    const selected_prop = getSelectedProp(selected_prop_key);

    // Show specify index checkbox if selected property is list.
    if (selected_prop['type'] == 'array') {
      field.find('label').removeClass('invisible');
    }

    // Add child property select box
    if ('properties' in selected_prop) {
      // Create child select box
      const template = $('#template-item-property-field :first').clone(true);
      field.after(template);

      // Set child property
      const child_select = template.find('select');
      const child_props = selected_prop['properties'];
      for (let [key, value] of Object.entries(child_props)) {
        child_select.append($('<option>').html(value['title']).val(key));
      }
    }
  });

  $('select[name="select-item-property-value"], select[name="select-item-property-lang"]').change((ev) => {
    page_global.hasEdit = true;
    const select_name = $(ev.target).prop('name');

    // Init fields
    const select_list = $(ev.target).closest('div[name="item-property-with-lang"]').find(`select[name="${select_name}"]`);
    const target_index = select_list.index(ev.target);
    select_list.each((index, elem) => {
      if (index <= target_index) {
        return;
      }
      // Init child select box
      $(elem).children().remove();
      $(elem).append($('<option>').html('').val(''));
    });

    // Delete waste field
    removeWasteField(ev.target);

    if ($(ev.target).val() == '') {
      return;
    }

    // Get selected property
    const selected_prop_key = getSelectedKeys(ev.target, select_name);
    const selected_prop = getSelectedProp(selected_prop_key);

    if ('properties' in selected_prop) {
      const field = $(ev.target).closest('div[name="item-property-field-with-lang"]');
      if (field.next().length == 0) {
        // Add child property select box
        const template = $('#template-item-property-field-with-lang :first').clone(true);
        field.after(template);
      }

      // Set child property
      const child_select = $(ev.target)
        .closest('div[name="item-property-with-lang"]')
        .find(`select[name="${select_name}"]`)
        .eq(selected_prop_key.length);
      const child_props = selected_prop['properties'];
      for (let [key, value] of Object.entries(child_props)) {
        child_select.append($('<option>').html(value['title']).val(key));
      }
      child_select.removeClass('invisible');
    }
  });

  $('select[name="select-item-property-file"]').change((ev) => {
    page_global.hasEdit = true;

    // Init field
    const field = $(ev.target).closest('div[name="item-property-field"]');
    field.nextAll().remove();

    if ($(ev.target).val() == '') {
      return;
    }

    // Get selected property
    const selected_prop_key = getSelectedKeys(ev.target);
    const selected_prop = getSelectedProp(selected_prop_key);

    // Add child property select box
    if ('properties' in selected_prop) {
      // Create child select box
      const template = $('#template-item-property-field-file :first').clone(true);
      field.after(template);

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
      select_list = $(select_box).closest('div[name="item-property"]').find('select');
    }
    else {
      select_list = $(select_box).closest('div[name="item-property-with-lang"]').find(`select[name="${select_name}"]`);
    }

    const keys = [];
    for (const elem of select_list.toArray()) {
      if (elem.value == '') {
        break;
      }
      keys.push(elem.value);
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

  function removeWasteField(select_box) {
    let find = false;
    const selects_value = $(select_box)
      .closest('div[name="item-property-with-lang"]')
      .find('select[name="select-item-property-value"]');
    let valid_num_value = selects_value.length;
    for (let ii = 0; ii < selects_value.length; ii++) {
      const select = selects_value.eq(ii);
      if (select.find('option').length == 1) {
        if (!find) {
          valid_num_value = ii;
          find = true;
        }
        select.addClass('invisible');
      }
    }

    find = false;
    const selects_lang = $(select_box)
      .closest('div[name="item-property-with-lang"]')
      .find('select[name="select-item-property-lang"]');
    let valid_num_lang = selects_lang.length;
    for (let ii = 0; ii < selects_lang.length; ii++) {
      const select = selects_lang.eq(ii);
      if (select.find('option').length == 1) {
        if (!find) {
          valid_num_lang = ii;
          find = true;
        }
        select.addClass('invisible');
      }
    }

    const valid_num = Math.max(valid_num_value, valid_num_lang);
    const input_fields = $(select_box)
      .closest('div[name="item-property-field-with-lang"]')
      .parent()
      .find('div[name="item-property-field-with-lang"]');
    input_fields.eq(valid_num - 1).nextAll().remove();
  };

  $('#mapping-submit').on('click', (ev) => {
    if (!checkInput()) {
      return;
    }

    saveCurrentNode();
    const rocrate_mapping = buildMappingData();
    const data = {
      item_type_id: parseInt(page_global.src_mapping_name),
      mapping: rocrate_mapping,
    };
    send(page_global.url, data);
  });

  function checkInput() {
    let check_result = true;

    if (!checkLayer()) {
      check_result = false;
    }

    if (!checkTreeStructure()) {
      check_result = false;
    }

    if (!checkNode()) {
      check_result = false;
    }

    return check_result;
  };

  function checkLayer() {
    // Init error message
    $('#layer-base').find('div[name="layer-name-message"]').addClass('hide');

    let check_result = true;
    $('#layer-base').find('input[name="layer-name"]').each((_, value) => {
      if ($(value).val() == '') {
        $(value).next().removeClass('hide');
        check_result = false;
      }
    });
    return check_result;
  };

  function checkTreeStructure() {
    // Init error message
    $('#tree-base').find('div[name="node-name-message"]').addClass('hide');

    let check_result = true;
    $('#tree-base').find('input[name="node-name"]').each((_, value) => {
      if ($(value).val() == '') {
        $(value).next().removeClass('hide');
        check_result = false;
      }
    });
    return check_result;
  };

  function checkNode() {
    let check_result = true;

    if (!checkNodeName()) {
      check_result = false;
    }

    if (!checkMapping()) {
      check_result = false;
    }

    return check_result;
  };

  function checkNodeName() {
    // Init error message
    $('#node-name-setting').find('div[name="node-name-message"]').addClass('hide');

    let check_result = true;
    const node_name_text = $('#node-name');
    if (!node_name_text.is(':disabled')) {
      if (node_name_text.val() == '') {
        node_name_text.next().removeClass('hide');
        check_result = false;
      }
    }

    return check_result;
  };

  function checkMapping() {
    // Init error message
    $('#mapping-table-body').find('div[name="rocrate-property-name-message"]').addClass('hide');
    $('#mapping-table-body').find('div[name="item-property-name-message"]').addClass('hide');
    $('#mapping-table-body').find('div[name="item-property-index-message"]').addClass('hide');
    $('#mapping-table-body').find('div[name="static-value-message"]').addClass('hide');

    let check_result = true;
    $('#mapping-table-body').find('select[name="select-rocrate-property"]').each((_, value) => {
      if ($(value).val() == '') {
        $(value).next().removeClass('hide');
        check_result = false;
      }
    });

    $('#mapping-table-body').find('div[name="item-property"]').each((_, item_property) => {
      if ($(item_property).hasClass('hide')) {
        return;
      }
      $(item_property).find('div[name="item-property-field"]').each((_, item_property_field) => {
        const select = $(item_property_field).find('select');
        if ($(select).val() == '') {
          $(item_property_field).find('div[name="item-property-name-message"]').removeClass('hide');
          check_result = false;
        }
        const check = $(item_property_field).find('input[name="check-list-index"]');
        if (check.is(':checked')) {
          const input = $(item_property_field).find('input[name="list-index"]');
          if (input.val() == '') {
            $(item_property_field).find('div[name="item-property-index-message"]').removeClass('hide');
            check_result = false;
          }
        }
      });
    });

    $('#mapping-table-body').find('div[name="item-property-with-lang"]').each((_, item_property) => {
      if ($(item_property).hasClass('hide')) {
        return;
      }
      $(item_property).find('select').each((_, select) => {
        if ($(select).hasClass('invisible')) {
          return;
        }
        if ($(select).val() == '') {
          $(select).next().removeClass('hide');
          check_result = false;
        }
      });
    });

    $('#mapping-table-body').find('div[name="static-value"]').each((_, static_value) => {
      if ($(static_value).find('input').val() == '') {
        $(static_value).find('div[name="static-value-message"]').removeClass('hide');
        check_result = false;
      }
    });

    return check_result;
  };

  function buildMappingData() {
    const rocrate_mapping = {};

    // item_type_id
    rocrate_mapping['item_type_id'] = parseInt(page_global.src_mapping_name);

    // entity_types
    rocrate_mapping['entity_types'] = [];
    const layer_names = $('#layer-base').find('input[name="layer-name"]');
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
    const node_id = node_li.get(0).dataset.id;

    node['depth'] = depth;

    node['name'] = page_global.node_name[node_id]['name'];
    if (node_id != 'root') {
      node['name_i18n'] = page_global.node_name[node_id]['name_i18n'];
    }

    // map
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
      success: (data, textStatus, jqXHR) => {
        page_global.hasEdit = false;
        $('html,body').scrollTop(0);
        addAlert(data.msg);
      },
      error: (jqXHR, textStatus, errorThrown) => {
        $('html,body').scrollTop(0);
        addError('Error: ' + jqXHR.statusText);
      }
    });
  };

  function addAlert(message) {
    $('#alerts').append(
      '<div id="alert-style" class="alert">' +
      '<button type="button" class="close" data-dismiss="alert">&times;</button>' +
      message +
      '</div>');
  };

  function addError(message) {
    $('#errors').append(
      '<div class="alert alert-danger">' +
      '<button type="button" class="close" data-dismiss="alert">&times;</button>' +
      message +
      '</div>');
  };

  function createNode(node_mapping, node_li) {
    const node_id = node_li.get(0).dataset.id;

    // Set node name
    const node_name = node_mapping['name'];
    const node_name_i18n = node_mapping['name_i18n'];
    const node_name_text = node_li.find('input[name="node-name"]').eq(0);
    node_name_text.val(node_name);
    page_global.node_name[node_id] = {
      name: node_name,
      name_i18n: node_name_i18n,
    };

    // Set node mapping
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
    const entity_types = page_global.rocrate_mapping['entity_types'];
    $('#layer-num').val(entity_types.length - 1);
    for (let ii = 1; ii < entity_types.length; ii++) {
      addLayer();
      const layer_text = $('#layer-base').find('input[name="layer-name"]').eq(-1);
      layer_text.val(entity_types[ii]);
    }

    // Create tree structure
    const tree_structure = page_global.rocrate_mapping['tree_structure'];
    const root_node_li = $('#tree-base :first');
    createNode(tree_structure, root_node_li);
    page_global.node_name['root'] = { name: 'root' };
    page_global.node_name['file'] = { name: 'file' };
    page_global.node_mapping['file'] = page_global.rocrate_mapping['file']['map'];
  }
  else {
    page_global.node_name['root'] = { name: 'root' };
    page_global.node_name['file'] = { name: 'file' };
    page_global.node_mapping['root'] = {};
    page_global.node_mapping['file'] = {};
  }
});
