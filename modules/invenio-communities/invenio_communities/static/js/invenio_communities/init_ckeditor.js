/*
 * This file is part of Invenio.
 * Copyright (C) 2016-2019 CERN.
 *
 * Invenio is free software; you can redistribute it and/or modify it
 * under the terms of the MIT License; see LICENSE file for more details.
 */

'use strict'

require([
  "node_modules/ckeditor/ckeditor",
  ], function() {

  var CKEDITOR_BASEPATH = '/ckeditor/';

  function init_ckeditor(selector, type) {
      if(type=="simple"){
          CKEDITOR.replace( selector, {
              toolbar: [
                  ['PasteText','PasteFromWord'],
                  ['Bold','Italic','Strike','-','Subscript','Superscript',],
                  ['NumberedList','BulletedList', 'Blockquote'],
                  ['Undo','Redo','-','Find','Replace','-', 'RemoveFormat'],
                  ['Mathjax', 'SpecialChar', 'ScientificChar'],
                  ['Source'], ['Maximize'],
              ],
              extraPlugins: 'scientificchar,mathjax,blockquote',
              disableNativeSpellChecker: false,
              removePlugins: 'elementspath',
              removeButtons: ''
          });
      } else {
          CKEDITOR.replace( selector, {
              toolbar: [
                  ['PasteText','PasteFromWord'],
                  ['Bold','Italic','Strike','-','Subscript','Superscript',],
                  ['NumberedList','BulletedList', 'Blockquote', 'Table', '-', 'Link', 'Anchor'],
                  ['Undo','Redo','-','Find','Replace','-', 'RemoveFormat'],
                  ['Mathjax', 'SpecialChar', 'ScientificChar'],
                  ['Styles', 'Format'], ['Source'], ['Maximize'],
              ],
              extraPlugins: 'scientificchar,mathjax,blockquote',
              disableNativeSpellChecker: false,
              removePlugins: 'elementspath',
              removeButtons: ''
          });
      }
  }

  if ( $('#page').length )
    init_ckeditor("page", 'advanced');
  if ( $('#description').length )
    init_ckeditor("description", 'simple');
  });
