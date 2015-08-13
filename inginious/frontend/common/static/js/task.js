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

function init_task_page()
{
    //Init the task form, if we are on the task submission page
    var task_form = $('form#task');
    task_form.on('submit', function()
    {
        submitTask(false);
        return false;
    });

    //Init the button that start a remote ssh server for debugging
    $('form#task #task-submit-debug').on('click', function()
    {
        submitTask(true);
    });

    if(task_form.attr("data-wait-submission"))
    {
        blurTaskForm();
        resetAlerts();
        displayTaskLoadingAlert();
        waitForSubmission(task_form.attr("data-wait-submission"));
    }
    $('#submissions').find('.submission').on('click', clickOnSubmission);
}

//True if loading something
var loadingSomething = false;

//Task page: find an editor by problem id
function getEditorForProblemId(problemId)
{
    var found = null;
    $.each(codeEditors, function(idx, editor)
    {
        if(!found && editor.getTextArea().name == problemId)
            found = editor;
    });
    return found;
}

//Blur task form
function blurTaskForm()
{
    $.each(codeEditors, function(idx, editor)
    {
        editor.setOption("readOnly", true);
    });
    var task_form = $('form#task');
    $("input, button", task_form).attr("disabled", "disabled");
    task_form.addClass('form-blur');
    loadingSomething = true;
}

function unblurTaskForm()
{
    $.each(codeEditors, function(idx, editor)
    {
        editor.setOption("readOnly", false);
    });
    var task_form = $('form#task');
    $("input, button", task_form).removeAttr("disabled");
    task_form.removeClass('form-blur');
    loadingSomething = false;
}

//Reset all alerts
function resetAlerts()
{
    $('#task_alert').html('');
    $('.task_alert_problem').html('');
}

//Increment tries count
function incrementTries()
{
    var ttries = $('#task_tries');
    ttries.text(parseInt(ttries.text()) + 1);
}

//Update task status
function updateTaskStatus(newStatus, grade)
{
    var task_status = $('#task_status');
    var task_grade = $('#task_grade');

    var currentStatus = task_status.text().trim();
    var currentGrade = parseFloat(task_grade.text().trim());

    if(currentStatus != "Succeeded")
        task_status.text(newStatus);
    if(currentGrade < grade)
        task_grade.text(grade);
}

//Creates a new submission (left column)
function displayNewSubmission(id)
{
    var submissions = $('#submissions');
    submissions.find('.submission-empty').remove();

    submissions.prepend($('<a></a>')
        .addClass('submission').addClass('list-group-item')
        .addClass('list-group-item-warning')
        .attr('data-submission-id', id).text(getDateTime()).on('click', clickOnSubmission))
}

//Updates a loading submission
function updateSubmission(id, result, grade)
{
    grade = grade || "0.0";

    var nclass = "";
    if(result == "success") nclass = "list-group-item-success";
    else if(result == "save") nclass = "list-group-item-save";
    else nclass = "list-group-item-danger";
    $('#submissions').find('.submission').each(function()
    {
        if($(this).attr('data-submission-id').trim() == id)
        {
            $(this).removeClass('list-group-item-warning').addClass(nclass);
            $(this).text($(this).text() + " - " + grade + "%");
        }
    });
}

//Submission's click handler
function clickOnSubmission()
{
    if(loadingSomething)
        return;
    loadOldSubmissionInput($(this).attr('data-submission-id'));
    $('body').removeClass('sidebar-active');
}

//Get current datetime
function getDateTime()
{
    var MyDate = new Date();

    return ('0' + MyDate.getDate()).slice(-2) + '/'
        + ('0' + (MyDate.getMonth() + 1)).slice(-2) + '/'
        + MyDate.getFullYear() + " "
        + ('0' + MyDate.getHours()).slice(-2) + ':'
        + ('0' + MyDate.getMinutes()).slice(-2) + ':'
        + ('0' + MyDate.getSeconds()).slice(-2);
}

//Submits a task
function submitTask(with_ssh)
{
    if(loadingSomething)
        return;

    $('#task-debug-mode').val(with_ssh ? "ssh" : "");

    //Must be done before blurTaskForm as when a form is disabled, no input is sent by the plugin
    $('form#task').ajaxSubmit(
        {
            dataType: 'json',
            success:  function(data)
                      {
                          if("status" in data && data["status"] == "ok" && "submissionid" in data)
                          {
                              incrementTries();
                              displayNewSubmission(data['submissionid']);
                              waitForSubmission(data['submissionid']);
                          }
                          else if("status" in data && data['status'] == "error" && "text" in data)
                          {
                              displayTaskErrorAlert(data);
                              updateTaskStatus("Internal error", 0);
                              unblurTaskForm();
                          }
                          else
                          {
                              displayTaskErrorAlert({});
                              updateTaskStatus("Internal error", 0);
                              unblurTaskForm();
                          }
                      },
            error:    function()
                      {
                          displayTaskErrorAlert({});
                          updateTaskStatus("Internal error", 0);
                          unblurTaskForm();
                      }
        });

    blurTaskForm();
    resetAlerts();
    displayTaskLoadingAlert();
    updateTaskStatus("Waiting for verification", 0);
}

//Display informations for remote debugging
function displayRemoteDebug(ssh_host, ssh_conn_id, ssh_key)
{
    var pre_content = "inginious-remote-debug " + ssh_host + "\n" + ssh_conn_id + "\n" + ssh_key;
    var task_alert = $('#task_alert');

    if($('pre', task_alert).text() != pre_content)
    {
        var pre = $('<pre><pre>').text(pre_content);
        var alert = $(getAlertCode("<b>SSH server active</b><br/>"+
                                   "Please paste this command into your terminal.<br/>"+
                                   "You need to have the <a href='https://pypi.python.org/pypi/INGInious/'>INGInious pip package</a> installed.<br/>",
                                   "info", false));
        alert.attr('id', 'ssh_remote_info');
        alert.append(pre);
        task_alert.empty().append(alert);
    }
}

//Wait for a job to end
function waitForSubmission(submissionid)
{
    setTimeout(function()
    {
        var url = $('form#task').attr("action");
        jQuery.post(url, {"@action": "check", "submissionid": submissionid}, null, "json")
            .done(function(data)
            {
                if("status" in data && data['status'] == "waiting")
                {
                    waitForSubmission(submissionid);
                    if("ssh_key" in data && "ssh_conn_id" in data && "ssh_host" in data)
                        displayRemoteDebug(data["ssh_host"], data["ssh_conn_id"], data["ssh_key"])
                }
                else if("status" in data && "result" in data && "grade" in data)
                {
                    if("debug" in data)
                        displayDebugInfo(data["debug"]);

                    if(data['result'] == "failed")
                    {
                        displayTaskStudentErrorAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        updateTaskStatus("Wrong answer", data["grade"]);
                        unblurTaskForm();
                    }
                    else if(data['result'] == "success")
                    {
                        displayTaskStudentSuccessAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        updateTaskStatus("Succeeded", data["grade"]);
                        unblurTaskForm();
                    }
                    else if(data['result'] == "timeout")
                    {
                        displayTimeOutAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        updateTaskStatus("Wrong answer", data["grade"]);
                        unblurTaskForm();
                    }
                    else if(data['result'] == "overflow")
                    {
                        displayOverflowAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        updateTaskStatus("Wrong answer", data["grade"]);
                        unblurTaskForm();
                    }
                    else // == "error"
                    {
                        displayTaskErrorAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        updateTaskStatus("Wrong answer", data["grade"]);
                        unblurTaskForm();
                    }
                }
                else
                {
                    displayTaskErrorAlert({});
                    updateSubmission(submissionid, "error", "0.0");
                    updateTaskStatus("Wrong answer", 0);
                    unblurTaskForm();
                }
            })
            .fail(function()
            {
                displayTaskErrorAlert({});
                updateSubmission(submissionid, "error", "0.0");
                updateTaskStatus("Wrong answer", 0);
                unblurTaskForm();
            });
    }, 1000);
}

//Displays debug info
function displayDebugInfo(info)
{
    displayDebugInfoRecur(info, $('#task_debug'));
}
function displayDebugInfoRecur(info, box)
{
    var data = $(document.createElement('dl'));
    data.text(" ");
    box.html(data);

    jQuery.each(info, function(index, elem)
    {
        var namebox = $(document.createElement('dt'));
        var content = $(document.createElement('dd'));
        data.append(namebox);
        data.append(content);

        namebox.text(index);
        if(jQuery.isPlainObject(elem))
            displayDebugInfoRecur(elem, content);
        else
            content.text(elem);
    });
}

//Displays a loading alert in task form
function displayTaskLoadingAlert()
{
    var task_alert = $('#task_alert');
    task_alert.html(getAlertCode("<b>Verifying your answers...</b>", "info", false));
    $('html, body').animate(
        {
            scrollTop: task_alert.offset().top - 100
        }, 200);
}

//Displays a loading input alert in task form
function displayTaskInputLoadingAlert()
{
    var task_alert = $('#task_alert');
    task_alert.html(getAlertCode("<b>Loading your submission...</b>", "info", false));
    $('html, body').animate(
        {
            scrollTop: task_alert.offset().top - 100
        }, 200);
}

//Displays a loading input alert in task form
function displayTaskInputErrorAlert()
{
    var task_alert = $('#task_alert');
    task_alert.html(getAlertCode("<b>Unable to load this submission</b>", "danger", false));
    $('html, body').animate(
        {
            scrollTop: task_alert.offset().top - 100
        }, 200);
}

//Displays an overflow error alert in task form
function displayOverflowAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>Your submission made an overflow. Your score is " + content["grade"] + "%</b>",
        "<b>Your submission made an overflow. Your score is " + content["grade"] + "%</b><br/>",
        "",
        "warning", false);
}

//Displays a timeout error alert in task form
function displayTimeOutAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>Your submission timed out. Your score is " + content["grade"] + "%</b>",
        "<b>Your submission timed out. Your score is " + content["grade"] + "%</b><br/>",
        "",
        "warning", false);
}

//Displays an internal error alert in task form
function displayTaskErrorAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>An internal error occured. Please retry later. If the error persists, send an email to the course administrator.</b>",
        "<b>An internal error occured. Please retry later. If the error persists, send an email to the course administrator.</b><br/>",
        "",
        "danger", false);
}

//Displays a student error alert in task form
function displayTaskStudentErrorAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>There are some errors in your answer. Your score is " + content["grade"] + "%</b>",
        "<b>There are some errors in your answer. Your score is " + content["grade"] + "%</b><br/>",
        "",
        "danger", false);
}

//Displays a student success alert in task form
function displayTaskStudentSuccessAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>Your answer passed the tests! Your score is " + content["grade"] + "%</b>",
        "<b>Your answer passed the tests! Your score is " + content["grade"] + "%</b><br/>",
        "",
        "success", true);
}

//Displays a student error alert in task form
function displayTaskStudentAlertWithProblems(content, topEmpty, topPrefix, prefix, type, alwaysShowTop)
{
    resetAlerts();

    var firstPos = -1;
    var task_alert = $('#task_alert');

    if("text" in content && content.text != "")
    {
        task_alert.html(getAlertCode(topPrefix + content.text, type, true));
        firstPos = task_alert.offset().top;
    }

    if("problems" in content)
    {
        $(".task_alert_problem").each(function(key, elem)
        {
            var problemid = elem.id.substr(11); //skip "task_alert."
            if(problemid in content.problems)
            {
                $(elem).html(getAlertCode(prefix + content.problems[problemid], "info", true));
                if(firstPos == -1 || firstPos > $(elem).offset().top)
                    firstPos = $(elem).offset().top;
            }
        });
    }

    if(firstPos == -1 || (alwaysShowTop && !("text" in content && content.text != "")))
    {
        task_alert.html(getAlertCode(topEmpty, type, true));
        firstPos = task_alert.offset().top;
    }

    $('html, body').animate(
        {
            scrollTop: firstPos - 100
        }, 200);
}

//Create an alert
//type is either alert, info, danger, warning
//dismissible is a boolean
function getAlertCode(content, type, dismissible)
{
    var a = '<div class="alert fade in ';
    if(dismissible)
        a += 'alert-dismissible ';
    a += 'alert-' + type + '" role="alert">';
    if(dismissible)
        a += '<button type="button" class="close" data-dismiss="alert"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>';
    a += content;
    a += '</div>';
    return a;
}

//Load an old submission input
function loadOldSubmissionInput(id)
{
    if(loadingSomething)
        return;

    blurTaskForm();
    resetAlerts();
    displayTaskInputLoadingAlert();

    var url = $('form#task').attr("action");
    jQuery.post(url, {"@action": "load_submission_input", "submissionid": id}, null, "json")
        .done(function(data)
        {
            if("status" in data && data['status'] == "ok" && "input" in data)
            {
                unblurTaskForm();
                loadOldFeedback(data);
                loadInput(id, data['input']);
            }
            else
            {
                displayTaskInputErrorAlert();
                unblurTaskForm();
            }
        }).fail(function()
        {
            displayTaskInputErrorAlert();
            unblurTaskForm();
        });
}

//Load feedback from an old submission
function loadOldFeedback(data)
{
    if("status" in data && "result" in data)
    {
        if("debug" in data)
            displayDebugInfo(data["debug"]);

        if(data['result'] == "failed")
            displayTaskStudentErrorAlert(data);
        else if(data['result'] == "success")
            displayTaskStudentSuccessAlert(data);
        else if(data['result'] == "timeout")
            displayTimeOutAlert(data);
        else if(data['result'] == "overflow")
            displayOverflowAlert(data);
        else // == "error"
            displayTaskErrorAlert(data);
    }
    else
        displayTaskErrorAlert({});
}

//Load data from input into the form inputs
function loadInput(submissionid, input)
{
    $('form#task input').each(function()
    {
        if($(this).attr('type') == "hidden") //do not try to change @action
            return;

        var id = $(this).attr('name');

        if(id in input)
        {
            if($(this).attr('type') != "checkbox" && $(this).attr('type') != "radio" && $(this).attr('type') != "file")
                $(this).prop('value', input[id]);
            else if($(this).attr('type') == "checkbox" && jQuery.isArray(input[id]) && $.inArray(parseInt($(this).prop('value')), input[id]))
                $(this).prop('checked', true);
            else if($(this).attr('type') == "radio" && parseInt($(this).prop('value')) == input[id])
                $(this).prop('checked', true);
            else if($(this).attr('type') == "checkbox" || $(this).attr('type') == "radio")
                $(this).prop('checked', false);
            else if($(this).attr('type') == 'file')
            {
                //display the download button associated with this file
                var input_file = $('#download-input-file-' + id);
                input_file.attr('href', $('form#task').attr("action") + "?submissionid=" + submissionid + "&questionid=" + id);
                input_file.css('display', 'block');
            }
        }
        else if($(this).attr('type') == "checkbox" || $(this).attr('type') == "radio")
            $(this).prop('checked', false);
        else
            $(this).prop('value', '');
    });

    $.each(codeEditors, function()
    {
        var name = this.getTextArea().name;
        if(name in input)
            this.setValue(input[name], -1);
        else
            this.setValue("");
    })
}