/*!
 * -*- coding: utf-8 -*-
 *
 * Copyright (C) 2020 National Institute of Informatics.
 *
 * WEKO3 is free software; you can redistribute it and/or
 * modify it under the terms of the MIT License; see LICENSE file for more
 * details.
 */

$(document).ready(function () {
  const leftSelect = $('#leftSelect');
  const rightSelect = $('#rightSelect');
  const moveRight = $('#moveRight');
  const moveLeft = $('#moveLeft');

  let labels = ['JaLC DOI', 'JaLC CrossRef DOI', 'JaLC DataCite DOI'];
  let targets = ['jalc_doi', 'jalc_crossref_doi', 'jalc_datacite_doi'];

  for (let index = 0; index < targets.length; index++) {
    let isChecked = $('#' + flag(targets[index])).prop('checked');
    if ($('#' + flag(targets[index])).prop('checked')) {
      rightSelect.append(`<option value="${targets[index]}">${labels[index]}</option>`);
    } else {
      leftSelect.append(`<option value="${targets[index]}">${labels[index]}</option>`);
    }
    $('#' + targets[index]).prop('readonly', !isChecked);
    $('#' + flag(targets[index])).parent().parent().hide()
  }

  let selectVal = 0
  $('#repo_selected').parent().parent().hide()
  selectVal = $('#repo_selected').val();
  $('#repository').val(selectVal);
  $('#repository').select2().trigger('change');

  updateButtonState();

  moveRight.on('click', function () {
    let selectors = leftSelect.find('option:selected');
    for (let index = 0; index < selectors.length; index++) {
      $('#' + selectors[index]["value"]).prop('readonly', false);
      $('#' + flag(selectors[index]["value"])).prop('checked', true);
    }
    selectors.detach().prop("selected", false).appendTo(rightSelect);
    updateButtonState();
  });

  moveLeft.on('click', function () {
    let selectors = rightSelect.find('option:selected');
    for (let index = 0; index < selectors.length; index++) {
      $('#' + selectors[index]["value"]).prop('readonly', true);
      $('#' + flag(selectors[index]["value"])).prop('checked', false);
    }
    selectors.detach().prop("selected", false).appendTo(leftSelect);
    updateButtonState();
  });

  function updateButtonState() {
    let moveRightDisabled = true;
    if (leftSelect.children().length) {
      moveRightDisabled = false;
    }
    moveRight.prop("disabled", moveRightDisabled);

    let moveLeftDisabled = true;
    if (rightSelect.children().length) {
      moveLeftDisabled = false;
    }
    moveLeft.prop("disabled", moveLeftDisabled);
  }

  function flag(inputId) {
    switch(inputId) {
      case 'jalc_doi':
        return 'jalc_flag';
      case 'jalc_crossref_doi':
        return 'jalc_crossref_flag';
      case 'jalc_datacite_doi':
        return 'jalc_datacite_flag';
      default:
        return inputId;
    } 
  }
});

