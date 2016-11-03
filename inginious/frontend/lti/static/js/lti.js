//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
"use strict";

$(function()
{
    init_common();
    init_lti();
});

function init_lti()
{
    // Fix sidebar rendering issue
    var height = Math.max($('#lti-sidebar-inner').height(), $('#content').height());
    $('#lti-sidebar-inner').height(height);
    $('#content').height(height);
}