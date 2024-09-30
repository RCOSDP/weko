/*
 * This file is part of WEKO3.
 * Copyright (C) 2017 National Institute of Informatics.
 */

import $ from 'jquery';
import 'bootstrap';
import 'select2';

// Pass a copied $ to functions using require(Must specify in files)
const noConflictjQuery = $.noConflict(true);

export { noConflictjQuery };
