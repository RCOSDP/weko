// This file is part of InvenioRDM
// Copyright (C) 2022 TU Wien.
//
// Invenio Theme TUW is free software; you can redistribute it and/or modify it
// under the terms of the MIT License; see LICENSE file for more details.

document.addEventListener("DOMContentLoaded", function () {
  var fileUri = document.getElementById("pdf-file-uri").value;
  window.PDFView.open(fileUri);
});
