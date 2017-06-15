//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
"use strict";

$(function()
{
    init_common();
    
    init_webapp();
});

function init_webapp()
{
    //Start affix only if there the height of the sidebar is less than the height of the content
    if($('#sidebar').height() < $('#content').height())
    {
        var start_affix = function() { $('#sidebar_affix').affix({offset: {top: 65, bottom: 61}}); };
        var update_size = function() { $('#sidebar_affix').width($('#sidebar').width()); };
        $(window).scroll(update_size);
        $(window).resize(update_size);
        update_size();
        start_affix();
    }

    //Registration form, disable the password field when not needed
    var register_courseid = $('#register_courseid');
    if(register_courseid)
    {
        register_courseid.change(function()
        {
            if($('option[value="' + register_courseid.val() + '"]', register_courseid).attr('data-password') == 1)
                $('#register_password').removeAttr('disabled');
            else
                $('#register_password').attr('disabled', 'disabled');
        });
    }

    //Wide modal size listener
    $(".modal-wide").on("show.bs.modal", function() {
        var height = $(window).height() - 200;
        $(this).find(".modal-body").css("max-height", height);
    });
}