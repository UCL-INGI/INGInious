//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
"use strict";

function groups_prepare_submit()
{
    var groups = [];

    // for each group
    $("#groups .group").each(function(i) {
        var id = $(this).find("#_id").val();
        var description = (i == 0) ? '' : $(this).find("#description").val();
        var group_size = (i == 0) ? 0 : parseInt($(this).find("#size").val());
        var group_students = [];

        $(this).find(".group-entry").each(function (j) {
            var username = $(this).data('username');
            group_students.push(String(username));
        });

        var audiences = [];
        $(this).find(".audience").each(function (i) {
            var audience = $(this).find("input").val();
            audiences.push(audience);
        });

        if (i > 0) {
            var group = {_id: id, description: description, size: group_size, students: group_students, audiences: audiences};
            groups.push(group);
        }
    });

     var inputField = jQuery('<input/>', {
            type:"hidden",
            name:"groups",
            value: JSON.stringify(groups)
    }).appendTo($("#groups_form"));

}

function group_add()
{
    // New group hidden item
    var new_group_li = $("#groups .card").last();

    // Clone and change id for deletion
    var clone = new_group_li.clone();
    clone.find("#audience_list_" + parseInt(clone.attr("id"))).attr("id", "#audience_list_" + (parseInt(clone.attr("id")) + 1));
    clone.find("#group_" + parseInt(clone.attr("id"))).attr("id", "#group_" + (parseInt(clone.attr("id")) + 1));
    clone.attr("id", parseInt(clone.attr("id")) + 1);
    clone.find("#group_number").text(clone.attr("id"));

    // Remove the hidden style attribute and push
    new_group_li.removeAttr("style");
    new_group_li.addClass("group");
    new_group_li.after(clone);

    jQuery('<input/>', {
        type:'hidden',
        name: '_id',
        id: '_id',
        value: 'None'
    }).appendTo(new_group_li);

    // Regroup sortable lists
    $$("ul.students").each(function(){
        new Sortable(this, {group:"students"})
    });
    $("ul.students").bind("DOMSubtreeModified", function() {group_update($(this).parent())});
    $("input[id='size']").on('keyup click',function() {group_update($(this).rparent(5))});
}

function group_delete(id)
{
    // Append all the items to ungrouped users
    $("#" + id).find("#students li").each(function(index) {
        $(this).appendTo("#group_0");
    });

    // add the group id in delete field
    // if group_id is not none, inform to delete
    // do not remove last group id
    if($("#group_" + id).find("#_id").val() != 'None') {
        jQuery('<input/>', {
            type: 'hidden',
            name: 'delete',
            value: $("#" + id).find("#_id").val()
        }).appendTo($('form'));
    }


    // Remove item...
    $("#" + id).remove();

    // Renumbering groups
    $("#groups .group-card").each(function(index) {
        $(this).attr("id", index);
        $(this).find("#group_number").text(index+1);
    });
}

function groups_delete() {
    $("#groups .group").each(function(i) {
        if(i!=0) // first .group must not be deleted : non-grouped
            group_delete($(this).attr("id"));
    });
}

function groups_clean() {
    $("#groups .group").each(function(i) {
        $("#" + $(this).attr("id")).find("#students li").each(function(index) {
            $(this).appendTo("#group_0");
        });
    });
}

function group_audience_add(audienceid, description, id) {

    // Check if valid entry
    if(audienceid==null)
        return;

    var new_audience_div = $("#group_" + id + " li").last();
    var clone = new_audience_div.clone();

    new_audience_div.attr("id", audienceid);
    new_audience_div.find("span").text(description);

    new_audience_div.removeAttr("style");
    new_audience_div.addClass("audience");
    new_audience_div.after(clone);

    jQuery('<input/>', {
            type:"hidden",
            name:"audiences",
            value: audienceid
        }).appendTo(new_audience_div);

    // Add entry in user list for user
    // Remove user from select list and disable select if empty
    $("#audience_list_" + id + " option[value='"+ audienceid +"']").remove();
    if(!$("#audience_list_" + id ).val())
        $("#audience_list_" + id ).prop("disabled", true);
}

function group_audience_remove(audienceid, id) {
    // Put user back to select list
    jQuery('<option/>', {
        value: audienceid,
        text:  $("#" + audienceid).text()
    }).appendTo($("#audience_list_" + id));

    $("#audience_list_" + id).prop("disabled", false);

    // Remove user from user list
    $("#" + audienceid).remove();
}

function student_add() {
    if($("#tab_registered_student").hasClass("active")) {

        var new_li = jQuery('<li/>', {
            'class':"list-group-item group-entry",
            'data-username':$("#registered_students :selected").val()
        });

        var new_user = jQuery('<span/>', {
            id: new_li.data("username"),
            text: ' ' + $("#registered_students :selected").text()
        }).appendTo(new_li);

        jQuery('<i/>', {
            class: "fa fa-arrows",
        }).prependTo(new_user);

        $("#registered_students :selected").remove();
        if(!$("#registered_students").val())
            $("#registered_students").prop("disabled", true);
    }
    else {
        var new_li = jQuery('<li/>', {
            'class':"list-group-item group-entry",
            'data-username': $("#new_student").val()
        });

        var new_user = jQuery('<span/>', {
            id: new_li.data("username"),
            text: ' ' + $("#new_student").val() + ' (will be registered)'
        }).appendTo(new_li);

        jQuery('<i/>', {
            class: "fa fa-arrows",
        }).prependTo(new_user);
    }

    var user_del_link = jQuery('<a/>', {
        'class': "pull-right",
        'id': 'user_delete',
        'href': '#',
        'onclick': "javascript:student_remove('" + new_li.data("username") + "')",
        'data-toggle': 'tooltip',
        'data-placement': 'left',
        'title': 'Remove student'
    });

    jQuery('<i/>', {
        'class': 'fa fa-user-times'
    }).appendTo(user_del_link);

    new_li.append(user_del_link);
    new_li.appendTo($("#group_0"));

    $("#student_modal").modal('hide');
}

function student_remove(username) {
    jQuery('<option/>', {
        value: username,
        text:  $("#" + username).text()
    }).appendTo($("#registered_students"));

    $("#registered_students").prop("disabled", false);

    $(".group-entry[data-username='" + username + "']").remove();
}

function group_update(ref) {
    // Check group sizes
    var grp_size_input = ref.find("#size");
    var max_grp_size = parseInt(grp_size_input.val());

    var actual_grp_size = 0;
    ref.find(".group-entry").each(function (j) {
        actual_grp_size++;
    });

    // If actual size higher than max group size, update
    if(actual_grp_size > max_grp_size || isNaN(max_grp_size)) {
        grp_size_input.val(actual_grp_size);
        grp_size_input.fadeTo('fast', 0.5).fadeTo('fast', 1.0);
    }
}