/*!
 * -*- coding: utf-8 -*-
 *
 * This file is part of WEKO3.
 * Copyright (C) 2017 National Institute of Informatics.
 *
 * WEKO3 is free software; you can redistribute it
 * and/or modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of the
 * License, or (at your option) any later version.
 *
 * WEKO3 is distributed in the hope that it will be
 * useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with WEKO3; if not, write to the
 * Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
 * MA 02111-1307, USA.
 */

$(document).ready(function () {
  const leftSelect = $('#leftSelect');
  const rightSelect = $('#rightSelect');
  const moveRight = $('#moveRight');
  const moveLeft = $('#moveLeft');

  let labels = ['JaLC DOI', 'JaLC CrossRef DOI', 'JaLC DataCite DOI', 'NDL JaLC DOI'];
  let targets = ['jalc_doi', 'jalc_crossref_doi', 'jalc_datacite_doi', 'ndl_jalc_doi'];

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
      case 'ndl_jalc_doi':
        return 'ndl_jalc_flag';
      default:
        return inputId;
    }
  }
});

