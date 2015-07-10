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

/**
 * Redirect to the studio to create a new task
 */
function studio_create_new_task()
{
    var task_id = $('#new_task_id');
    if(!task_id.val().match(/^[a-zA-Z0-9\._\-]+$/))
    {
        alert('Task id should only contain alphanumeric characters (in addition to ".", "_" and "-").');
        return;
    }
    window.location.href = window.location.href + "/../edit/task/" + task_id.val()
}

/**
 * Load the studio, creating blocks for existing subproblems
 */
function studio_load(data)
{
    jQuery.each(data, function(pid, problem)
    {
        var template = studio_get_template_for_problem(problem);
        studio_create_from_template(template, pid);
        studio_init_template(template, pid, problem);
    });

    $('form#edit_task_form').on('submit', function()
    {
        studio_submit();
        return false;
    });
}

/**
 * Update the "files" tabs when editing a task
 */
function studio_update_file_tabs(data, method)
{
    if(data == undefined)
        data = {};
    if(method == undefined)
        method = "GET";

    jQuery.ajax({
        beforeSend: function()
                    {
                        $("#tab_files").html('Loading');
                    },
        success:    function(data)
                    {
                        $("#tab_files").html(data);
                    },
        method:     method,
        data:       data,
        url:        location.pathname + "/files"
    });
}

/**
 * Delete a file related to a task
 */
function studio_task_file_delete(path)
{
    if(!confirm("Are you sure you want to delete this?") || !studio_task_file_delete_tab(path))
        return;
    studio_update_file_tabs({"action": "delete", "path": path});
}

/**
 * Rename/move a file related to a task
 */
function studio_task_file_rename(path)
{
    var new_path = prompt("Enter the new path", path);
    if(new_path != null && studio_task_file_delete_tab(path))
        studio_update_file_tabs({"action": "rename", "path": path, "new_path": new_path});
}

/**
 * Create a file related to a task
 */
function studio_task_file_create()
{
    var new_path = prompt("Enter the path to the file", "newfile.sh");
    if(new_path != null && studio_task_file_delete_tab(new_path))
        studio_update_file_tabs({"action": "create", "path": new_path});
}

/**
 * Upload a new file for a task
 */
function studio_task_file_upload()
{
    $('#modal_file_upload').modal('hide');
    $('#task_upload_form').ajaxSubmit({
        beforeSend: function()
                    {
                        $("#tab_files").html('Loading');
                    },
        success:    function(data)
                    {
                        $("#tab_files").html(data);
                    },
        url:        location.pathname + "/files"
    });
}

//Stores data about opened tabs
var studio_file_editor_tabs = {};
var studio_file_editor_tabs_next_id = 0;

/**
 * Open a new tab for editing a file, if it does not exists yet
 */
function studio_task_file_open_tab(path)
{
    if(studio_file_editor_tabs[path] == undefined)
    {
        var tab_id = "task_file_editor_" + studio_file_editor_tabs_next_id;
        studio_file_editor_tabs_next_id += 1;
        studio_file_editor_tabs[path] = tab_id;

        var edit_file_tabs = $('#edit_file_tabs');
        edit_file_tabs.append('<li role="presentation" class="studio_file_editor_tab">' +
            '<a href="#' + tab_id + '" aria-controls="editor" role="tab" data-toggle="tab"><i class="fa fa-file-code-o"></i>&nbsp; ' + path +
            ' <button class="closetab" type="button"><i class="fa fa-remove"></i></button>' +
            '</a></li>');
        $('a[href="#' + studio_file_editor_tabs[path] + '"] .closetab', edit_file_tabs).click(function()
        {
            studio_task_file_delete_tab(path)
        });

        $('#edit_file_tabs_content').append('<div role="tabpanel" class="tab-pane" id="' + tab_id + '">Loading...</div>');

        jQuery.ajax({
            success:  function(data)
                      {
                          var newtab = $("#" + tab_id);
                          if(data["error"] != undefined)
                          {
                              newtab.html('INGInious can\'t read this file.');
                              return;
                          }

                          newtab.html('<form>' + '<textarea id="' + tab_id + '_editor" class="form-control"></textarea>' +
                              '<button type="button" id="' + tab_id + '_button" class="btn btn-primary btn-block">Save</button></form>');

                          var newtab_editor = $("#" + tab_id + '_editor');
                          newtab_editor.val(data['content']);

                          //try to find the mode for the editor
                          var mode = CodeMirror.findModeByFileName(path);
                          if(mode == undefined)
                          {
                              mode = "text/plain";
                              //verify if it is a UNIX executable file that starts with #!
                              if(data['content'].substring(0, 2) == "#!")
                              {
                                  var app = data['content'].split("\n")[0].substring(2).trim();

                                  //check in codemirror
                                  $.each(CodeMirror.modeInfo, function(key, val)
                                  {
                                      if(app.indexOf(val['name'].toLowerCase()) != -1)
                                          mode = val["mode"];
                                  });

                                  //else, check in our small hint-list
                                  if(mode == "text/plain")
                                  {
                                      var hintlist = {"bash": "shell", "sh": "shell", "zsh": "shell", "python": "python", "php": "php"};
                                      $.each(hintlist, function(key, val)
                                      {
                                          if(app.indexOf(key) != -1)
                                              mode = val;
                                      });
                                  }
                              }
                          }
                          else
                              mode = mode["mode"];

                          var editor = registerCodeEditor(newtab_editor[0], mode, 20);
                          $("#" + tab_id + '_button').click(function()
                          {
                              jQuery.ajax({
                                  success:  function(data)
                                            {
                                                if("error" in data)
                                                    studio_display_task_submit_message("An error occurred while saving the file", "danger", true);
                                                else
                                                {
                                                    editor.markClean();
                                                    studio_display_task_submit_message("File saved.", "success", true);
                                                }
                                            },
                                  url:      location.pathname + "/files",
                                  method:   "POST",
                                  dataType: "json",
                                  data:     {"path": path, "action": "edit_save", "content": editor.getValue()}
                              });
                          });
                      },
            method:   "GET",
            dataType: "json",
            data:     {"path": path, "action": "edit"},
            url:      location.pathname + "/files"
        });
    }
    $('a[href="#' + studio_file_editor_tabs[path] + '"]', edit_file_tabs).tab('show');
}

/**
 * Delete an opened tab
 */
function studio_task_file_delete_tab(path)
{
    if(studio_file_editor_tabs[path] != undefined)
    {
        var editorId = -1;
        $.each(codeEditors, function(idx, editor)
        {
            if(editor.getTextArea().id == studio_file_editor_tabs[path] + '_editor')
            {
                if(!editor.isClean() && !confirm('You have unsaved change to this file. Do you really want to close it?'))
                    return false;
                editorId = idx;
            }
        });
        if(editorId != -1)
            codeEditors.splice(editorId, 1);

        var edit_file_tabs = $('#edit_file_tabs');
        if($('a[href="#' + studio_file_editor_tabs[path] + '"]', edit_file_tabs).parent().hasClass('active'))
            $('li:eq(0) a', edit_file_tabs).tab('show');
        $('a[href="#' + studio_file_editor_tabs[path] + '"]', edit_file_tabs).parent().remove();
        $('#' + studio_file_editor_tabs[path]).remove();
        delete studio_file_editor_tabs[path];
    }
    return true;
}

/**
 * Display a message indicating the status of a save action
 */
function studio_display_task_submit_message(content, type, dismissible)
{
    var code = getAlertCode(content, type, dismissible);
    $('#task_edit_submit_status').html(code);

    if(dismissible)
    {
        window.setTimeout(function()
        {
            $("#task_edit_submit_status").children().fadeTo(1000, 0).slideUp(1000, function()
            {
                $(this).remove();
            });
        }, 2000);
    }
}

/**
 * Submit the form
 */
var studio_submitting = false;
function studio_submit()
{
    if(studio_submitting)
        return;
    studio_submitting = true;

    studio_display_task_submit_message("Saving...", "info", false);

    $('form#edit_task_form .subproblem_order').each(function(index, elem)
    {
        $(elem).val(index);
    });

    $('form#edit_task_form').ajaxSubmit(
        {
            dataType: 'json',
            success:  function(data)
                      {
                          if("status" in data && data["status"] == "ok")
                          {
                              studio_display_task_submit_message("Task saved.", "success", true);
                              $('.task_edit_submit_button').attr('disabled', false);
                              studio_submitting = false;
                          }
                          else if("message" in data)
                          {
                              studio_display_task_submit_message(data["message"], "danger", true);
                              $('.task_edit_submit_button').attr('disabled', false);
                              studio_submitting = false;
                          }
                          else
                          {
                              studio_display_task_submit_message("An internal error occured", "danger", true);
                              $('.task_edit_submit_button').attr('disabled', false);
                              studio_submitting = false;
                          }
                      },
            error:    function()
                      {
                          studio_display_task_submit_message("An internal error occured", "danger", true);
                          $('.task_edit_submit_button').attr('disabled', false);
                          studio_submitting = false;
                      }
        });
    $('.task_edit_submit_button').attr('disabled', true);
}

/**
 * Get the right template for a given problem
 * @param problem
 */
function studio_get_template_for_problem(problem)
{
    if((problem["type"] == "code" && !problem["boxes"]) || problem["type"] == "code-single-line")
        return "#subproblem_code";
    else if(problem["type"] == "code-file")
        return "#subproblem_code_file";
    else if(problem["type"] == "code")
        return "#subproblem_custom";
    else if(problem["type"] == "match")
        return "#subproblem_match";
    else if(problem["type"] == "multiple-choice")
        return "#subproblem_multiple_choice";
    return "#subproblem_custom";
}

/**
 * Create new subproblem from the data in the form
 */
function studio_create_new_subproblem()
{
    var new_subproblem_pid = $('#new_subproblem_pid');
    if(!new_subproblem_pid.val().match(/^[a-zA-Z0-9\._\-]+$/))
    {
        alert('Problem id should only contain alphanumeric characters (in addition to ".", "_" and "-").');
        return;
    }

    if($(studio_get_problem(new_subproblem_pid.val())).length != 0)
    {
        alert('This problem id is already used.');
        return;
    }

    studio_create_from_template('#' + $('#new_subproblem_type').val(), new_subproblem_pid.val())
}

/**
 * Create a new template and put it at the bottom of the problem list
 * @param template
 * @param pid
 */
function studio_create_from_template(template, pid)
{
    var tpl = $(template).html().replace(/PID/g, pid);
    $('#new_subproblem').before(tpl);
}

/**
 * Get the real id of the DOM element containing the problem
 * @param pid
 */
function studio_get_problem(pid)
{
    return "#subproblem_well_" + pid;
}

/**
 * Init a template with data from an existing problem
 * @param template
 * @param pid
 * @param problem
 */
function studio_init_template(template, pid, problem)
{
    var well = $(studio_get_problem(pid));

    //Default for every problem types
    if("name" in problem)
        $('#name-' + pid, well).val(problem["name"]);
    var header_editor = registerCodeEditor($('#header-' + pid)[0], 'rst', 10);
    if("header" in problem)
        header_editor.setValue(problem["header"]);

    //Custom values for each problem type
    switch(template)
    {
        case "#subproblem_code":
            studio_init_template_code(well, pid, problem);
            break;
        case "#subproblem_code_file":
            studio_init_template_code_file(well, pid, problem);
            break;
        case "#subproblem_custom":
            studio_init_template_custom(well, pid, problem);
            break;
        case "#subproblem_match":
            studio_init_template_match(well, pid, problem);
            break;
        case "#subproblem_multiple_choice":
            studio_init_template_multiple_choice(well, pid, problem);
            break;
    }
}

/**
 * Init a code template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_code(well, pid, problem)
{
    if("language" in problem)
        $('#language-' + pid, well).val(problem["language"]);
    if("type" in problem)
        $('#type-' + pid, well).val(problem["type"]);
    if("optional" in problem && problem["optional"])
        $('#optional-' + pid, well).attr('checked', true);
}

/**
 * Init a code_file template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_code_file(well, pid, problem)
{
    if("max_size" in problem)
        $('#maxsize-' + pid, well).val(problem["max_size"]);
    if("allowed_exts" in problem)
        $('#extensions-' + pid, well).val(problem["allowed_exts"].join());
}

/**
 * Init a custom template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_custom(well, pid, problem)
{
    registerCodeEditor($('#custom-' + pid)[0], 'yaml', 10).setValue(problem["custom"]);
}

/**
 * Init a match template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_match(well, pid, problem)
{
    if("answer" in problem)
        $('#answer-' + pid, well).val(problem["answer"]);
}

/**
 * Init a multiple choice template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_multiple_choice(well, pid, problem)
{
    if("limit" in problem)
        $('#limit-' + pid, well).val(problem["limit"]);
    else
        $('#limit-' + pid, well).val(0);
    if("multiple" in problem && problem["multiple"])
        $('#multiple-' + pid, well).attr('checked', true);
    if("centralize" in problem && problem["centralize"])
        $('#centralize-' + pid, well).attr('checked', true);

    var success_message = "";
    var error_message = "";
    if("success_message" in problem)
        success_message = problem["success_message"];
    if("error_message" in problem)
        error_message = problem["error_message"];

    registerCodeEditor($('#success_message-' + pid)[0], 'rst', 1).setValue(success_message);
    registerCodeEditor($('#error_message-' + pid)[0], 'rst', 1).setValue(error_message);

    jQuery.each(problem["choices"], function(index, elem)
    {
        studio_create_choice(pid, elem);
    });
}

/**
 * Create a new choice in a given multiple-choice problem
 * @param pid
 * @param choice_data
 */
function studio_create_choice(pid, choice_data)
{
    var well = $(studio_get_problem(pid));

    var index = 0;
    while($('#choice-' + index + '-' + pid).length != 0)
        index++;

    var row = $("#subproblem_multiple_choice_choice").html();
    var new_row_content = row.replace(/PID/g, pid).replace(/CHOICE/g, index);
    var new_row = $("<div></div>").attr('id', 'choice-' + index + '-' + pid).html(new_row_content);
    $("#choices-" + pid, well).append(new_row);

    var editor = registerCodeEditor($(".subproblem_multiple_choice_text", new_row)[0], 'rst', 1);
    var editor_feedback = registerCodeEditor($(".subproblem_multiple_choice_feedback", new_row)[0], 'rst', 1);

    if("text" in choice_data)
        editor.setValue(choice_data["text"]);
    if("feedback" in choice_data)
        editor_feedback.setValue(choice_data["feedback"]);

    if("valid" in choice_data && choice_data["valid"] == true)
    {
        $(".subproblem_multiple_choice_valid", new_row).trigger('click');
        $(".subproblem_multiple_choice_valid", new_row).attr('checked', true);
    }
}

/**
 * Delete a multiple choice answer
 * @param pid
 * @param choice
 */
function studio_delete_choice(pid, choice)
{
    $('#choice-' + choice + '-' + pid).detach();
}

/**
 * Move subproblem up
 * @param pid
 */
function studio_subproblem_up(pid)
{
    var well = $(studio_get_problem(pid));
    var prev = well.prev(".well.row");
    if(prev.length)
        well.detach().insertBefore(prev);
}

/**
 * Move subproblem down
 * @param pid
 */
function studio_subproblem_down(pid)
{
    var well = $(studio_get_problem(pid));
    var next = well.next(".well.row");
    if(next.length)
        well.detach().insertAfter(next);
}

/**
 * Delete subproblem
 * @param pid
 */
function studio_subproblem_delete(pid)
{
    var well = $(studio_get_problem(pid));
    if(!confirm("Are you sure that you want to delete this subproblem?"))
        return;
    var codeEditors_todelete = [];
    $.each(codeEditors, function(i, editor)
    {
        if(jQuery.contains(well[0], editor.getTextArea()))
            codeEditors_todelete.push(i);
    });
    $.each(codeEditors_todelete, function(_, editor_idx)
    {
        codeEditors.splice(editor_idx, 1);
    });
    well.detach();
}

/**
 * Shows the feedback for an old submission
 */
var loadingSomething = false;
function studio_get_feedback(sid)
{
    if(loadingSomething)
        return;
    loadingSomething = true;
    $('#modal_feedback_content').text('Loading...');
    $('#modal_feedback').modal('show');

    $.getJSON(document.location.pathname + '/' + sid).done(function(data)
    {
        if(data['status'] == "ok")
        {
            var output = "<h4><b>Result</b></h4>";
            output += data["data"]["result"] + " - " + data["data"]["grade"] + "%";
            output += "<hr/><h4><b>Feedback - top</b></h4>";
            output += data["data"]["text"];
            $.each(data["data"]["problems"], function(index, elem)
            {
                output += "<hr/><h4><b>Feedback - subproblem " + index + "</b></h4>";
                output += elem;
            });
            output += "<hr/><h4><b>Debug</b></h4>";
            output += "<div id='modal_feedback_debug'></div>";

            $('#modal_feedback_content').html(output);
            displayDebugInfoRecur(data["data"], $('#modal_feedback_debug'));
        }
        else
        {
            $('#modal_feedback_content').text('An error occured while retrieving the submission');
        }
        loadingSomething = false;
    }).fail(function()
    {
        $('#modal_feedback_content').text('An error occured while retrieving the submission');
        loadingSomething = false;
    });
}

/**
 * Select/deselect all the checkboxes of a panel
 * @param select: boolean indicating if we should select or deselect
 * @param panel_member: a child of the panel in which is the list
 */
function download_page_select(select, panel_member)
{
    panel_member = $(panel_member);
    while(!panel_member.hasClass('panel'))
        panel_member = panel_member.parent();
    $('input[type="checkbox"]', panel_member).prop('checked', select);
    $('input[type="checkbox"]', panel_member).trigger('change');
}

/**
 * Select/deselect all the checkboxes of the panel depending on a list of users and groups tutored.
 * @param panel_member: a child of the panel in which is the list
 * @param users: a list of usernames
 * @param groups: a list of group ids
 */
function download_page_select_tutor(panel_member, users, groups)
{
    panel_member = $(panel_member);
    while(!panel_member.hasClass('panel'))
        panel_member = panel_member.parent();
    $('input[name="groups"]', panel_member).each(function() { $(this).prop('checked', $.inArray($(this).val(),groups) != -1); });
    $('input[name="users"]', panel_member).each(function() { $(this).prop('checked', $.inArray($(this).val(), users) != -1); });
    $('input[type="checkbox"]', panel_member).trigger('change');
}