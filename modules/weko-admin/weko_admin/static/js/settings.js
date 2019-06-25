/*
 * This file is part of WEKO3.
 * Copyright (C) 2017 National Institute of Informatics.
 */

require.config({
  baseUrl: "/static/",
  paths: {
    jquery: "node_modules/jquery/jquery",
    bootstrap: "node_modules/bootstrap-sass/assets/javascripts/bootstrap",
    select2: "node_modules/select2/dist/js/select2"
  },
  shim: {
    jquery: {
      exports: "$"
    },
    bootstrap: {
      deps: ["jquery"]
    },
    select2: {
      deps: ["jquery"],
      exports: "select2"
    }
  }
})

// Pass a copied $ to functions using require(Must specify in files)
define('noConflictjQuery', ['jquery'], function (jq) {
    return jq.noConflict(true);
});
