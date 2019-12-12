//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
"use strict";

function audiences_prepare_submit()
{
    var students = [];
    $(".group-entry").each(function(i) {
            var username = $(this).data('username');
            students.push(username);
    });

    var tutors = [];
    $(".tutor").each(function(i) {
        var tutor = $(this).find("input").val();
        tutors.push(tutor);
    });

    var id = $("#_id").val();
    var description = $("#description").val();
    var audiences = [{_id: id, description: description, students: students, tutors: tutors}];

    var inputField = jQuery('<input/>', {
            type:"hidden",
            name:"audiences",
            value: JSON.stringify(audiences)
    }).appendTo($("form"));
}

function audiences_tutor_add(username, complete_name, id) {

    // Check if valid entry
    if(username==null)
        return;

    var new_tutor_div = $("#tutors_" + id + " li").last();
    var clone = new_tutor_div.clone();

    new_tutor_div.attr("id", username);
    new_tutor_div.find("span").text(complete_name);

    new_tutor_div.removeAttr("style");
    new_tutor_div.addClass("tutor");
    new_tutor_div.after(clone);

    jQuery('<input/>', {
            type:"hidden",
            name:"tutors",
            value: username
        }).appendTo(new_tutor_div);

    // Add entry in user list for user
    // Remove user from select list and disable select if empty
    $("#tutor_list_" + id + " option[value='"+ username +"']").remove();
    if(!$("#tutor_list_" + id ).val())
        $("#tutor_list_" + id ).prop("disabled", true);
}

function audiences_tutor_remove(username, id) {
    // Put user back to select list
    jQuery('<option/>', {
        value: username,
        text:  $("#" + username).text()
    }).appendTo($("#tutor_list_" + id));

    $("#tutor_list_" + id).prop("disabled", false);

    // Remove user from user list
    $("#" + username).remove();
}

function audiences_student_add() {
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

function audiences_student_remove(username) {
    jQuery('<option/>', {
        value: username,
        text:  $("#" + username).text()
    }).appendTo($("#registered_students"));

    $("#registered_students").prop("disabled", false);

    $(".group-entry[data-username='" + username + "']").remove();
}

function audience_delete(id) {
    jQuery('<input/>', {
        type:'hidden',
        name: 'delete',
        value: id
    }).appendTo($('form'));

    $('form').submit();
}