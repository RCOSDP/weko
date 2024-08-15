/*
 * This file is part of WEKO3.
 * Copyright (C) 2017 National Institute of Informatics.

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


//require([
//  'jquery',
//], function () {

import $ from 'jquery';

( function () {
    'use strict';

  $('.table tr').click(function (ev) {
    if (this.children.length > 0) {
      var data = this.children[0].dataset;
      if (data.groupId) {
        window.location.href = "./" + data.groupId;
      }
    }
  });

});
