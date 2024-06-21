/*
 * This file is part of Invenio.
 * Copyright (C) 2015-2023 CERN.
 *
 * Invenio is free software; you can redistribute it and/or modify it
 * under the terms of the MIT License; see LICENSE file for more details.
 */

import $ from "jquery";
import Papa from "papaparse";

(function ($, Papa) {
  function createDataElement(htmlTag, innerText) {
    const node = document.createElement(htmlTag);
    const textNode = document.createTextNode(innerText);
    node.appendChild(textNode);
    return node;
  }

  const URL = $("#app").attr("data-csv-source");
  const fileSize = $("#app").attr("data-csv-size");
  const maxRowsPerChunk = 50;
  const $tableHeader = $("#table-header");
  const $tableBody = $("#table-body");
  const $showMore = $("#show-more");

  let isFirst = true;
  let currentStep = 0;
  let papaParser = null;

  $showMore.hide(); // hide it when init
  $showMore.on("click", function () {
    currentStep = 0;
    papaParser.resume();
  });

  // If the RemoteChunkSize is bigger than the size of the file it fails with a 416
  if (fileSize < Papa.RemoteChunkSize) {
    Papa.RemoteChunkSize = fileSize
  }

  Papa.parse(URL, {
    download: true,
    skipEmptyLines: true,
    step: function (results, parser) {
      papaParser = papaParser || parser;
      currentStep++;
      console.debug("CSV previewer: rendering step", results);
      const row = results.data || [];

      const tableRowEl = document.createElement("tr");
      let tableColEl;
      if (isFirst) {
        $tableHeader.append(tableRowEl);
        tableColEl = "th";
        isFirst = false;
      } else {
        $tableBody.append(tableRowEl);
        tableColEl = "td";
      }

      row.forEach((col) => {
        const node = createDataElement(tableColEl, col);
        tableRowEl.appendChild(node);
      });

      if (currentStep >= maxRowsPerChunk) {
        parser.pause();
        $showMore.show();
      }
    },
    error: function (err, file, inputElem, reason) {
      console.error(
        "CSV previewer: error rendering CSV file: ",
        err,
        file,
        inputElem,
        reason
      );
    },
    complete: function (results, file) {
      console.debug("CSV previewer: rendering completed", results, file);
      $showMore.hide();
    },
  });
})($, Papa);
