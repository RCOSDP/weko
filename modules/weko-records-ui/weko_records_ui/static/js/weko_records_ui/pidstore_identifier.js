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
    const moveRight = $('#moveRight');
    const moveLeft = $('#moveLeft')
    const leftSelect = $('#leftSelect');
    const rightSelect = $('#rightSelect');

    var jalcFlagLabel= $('#jalc_flag');
    var jalcCrossrefFlagData = $('#jalc_crossref_flag');
    var jalcDataciteFlagData = $('#jalc_datacite_flag');
    var cnriFlagData = $('#cnri_flag');

    // let results = []

    let leftOption = '';
    // let rightOption = '';

    leftOption += `<option value="${jalcFlagLabel}">${jalcFlagLabel}</option>`;
    leftOption += `<option value="${jalcCrossrefFlagData}">${jalcCrossrefFlagData}</option>`;
    leftOption += `<option value="${jalcDataciteFlagData}">${jalc_datacite_flag}</option>`;
    leftOption += `<option value="${cnriFlagData}">${cnriFlagData}</option>`;
    leftSelect.append(leftOption);

    // $.ajax({
    //   url: urlLoad,
    //   type: 'GET',
    //   success: function (data) {
    //     results = data.results;
  
    //     let leftOption = '';
    //     let rightOption = '';
  
    //     for (let index = 0; index < results.length; index++) {
    //       const element = results[index];
    //       if (element.is_registered) {
    //         rightOption += `<option value="${element.lang_code}">${element.lang_code}&nbsp;${element.lang_name}</option>`;
    //         continue;
    //       }
    //       leftOption += `<option value="${element.lang_code}">${element.lang_code}&nbsp;${element.lang_name}</option>`;
    //     }
    //     leftSelect.append(leftOption);
    //     rightSelect.append(rightOption);
    //   },
    //   error: function (error) {
    //     console.log(error);
    //     alert('Error when get languages');
    //   }
    // });
  
    moveRight.on('click', function () {
      leftSelect.find('option:selected').detach().prop("selected", false).appendTo(rightSelect);
      updateButton();
    });
  
    moveLeft.on('click', function () {
      rightSelect.find('option:selected').detach().prop("selected", false).appendTo(leftSelect);
      updateButton();
      updateRightButtons();
    });
  
    function updateRightButtons() {
      moveTop.prop('disabled', true);
      moveUp.prop('disabled', true);
      moveDown.prop('disabled', true);
      moveBottom.prop('disabled', true);
    }
  });  