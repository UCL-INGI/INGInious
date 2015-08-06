//
// Copyright (c) 2014-2015 Université Catholique de Louvain.
//
// This file is part of INGInious.
//
// INGInious is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published
// by the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// INGInious is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public
// License along with INGInious.  If not, see <http://www.gnu.org/licenses/>.
"use strict";

$(function()
{
    init_common();
    init_task_page();
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
}