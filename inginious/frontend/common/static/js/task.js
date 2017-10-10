//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
"use strict";

function init_task_page(evaluate)
{
    evaluatedSubmission = evaluate;

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
        loadOldSubmissionInput(task_form.attr("data-wait-submission"), false);
        blurTaskForm();
        resetAlerts();
        displayTaskLoadingAlert(null, null);
        waitForSubmission(task_form.attr("data-wait-submission"));
    }

    $('.submission').each(function() {
        $(this).on('click', clickOnSubmission);
        $(this).find('a').on('click', selectSubmission);
    });
}

var evaluatedSubmission = 'best';
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
    $("input, button", task_form).attr("disabled", "disabled").addClass('form-blur');
    //task_form.addClass('form-blur');
    loadingSomething = true;
}

function unblurTaskForm()
{
    $.each(codeEditors, function(idx, editor)
    {
        editor.setOption("readOnly", false);
    });
    var task_form = $('form#task');
    $("input, button", task_form).removeAttr("disabled").removeClass('form-blur');
    //task_form.removeClass('form-blur');
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

    task_status.text(newStatus);
    task_grade.text(grade);
}

//Creates a new submission (left column)
function displayNewSubmission(id)
{
    var submissions = $('#submissions');
    submissions.find('.submission-empty').remove();

    var submission_link = jQuery('<li/>', {
        class: "submission list-group-item list-group-item-warning",
        "data-submission-id": id
    }).on('click', clickOnSubmission);

    if(evaluatedSubmission == "student") {
        var actual_link = jQuery('<a/>', {
            class:"allowed",
            title:"Select for evaluation",
            "data-toggle":"tooltip",
            "data-placement": "right"
        }).appendTo(submission_link).after("&nbsp;&nbsp;").on('click', selectSubmission);

         jQuery('<i/>', {class: "fa fa-bookmark fa-fw"}).appendTo(actual_link);
    }

    jQuery('<span/>', {}).text(getDateTime()).appendTo(submission_link);
    submissions.prepend(submission_link);

    $("body").tooltip({
        selector: '[data-toggle="tooltip"]'
    });
}

function removeSubmission(id) {
    var item;

    $('#submissions').find('.submission').each(function() {
        if($(this).attr('data-submission-id').trim() == id)
            item = $(this)
    });

    item.remove();
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
            $(this).find("span").append(" - " + grade + "%");
        }
    });
}

// Select submission handler
function selectSubmission(e) {

    e.stopPropagation();

    var item = $(this).parent();
    var id = item.attr('data-submission-id');

    if($(this).hasClass('allowed'))
        setSelectedSubmission(id, true, true);
}

// Set selected submission
function setSelectedSubmission(id, fade, makepost) {
    var item;

    $('#submissions').find('.submission').each(function() {
        if($(this).attr('data-submission-id').trim() == id)
            item = $(this)
    });

    // LTI does not support selecting a specific submission for evaluation
    if($("#my_submission").length) {
        var text = item.find("span").html();
        var url = $('form#task').attr("action");

        var applyfn = function (data) {
            if ('status' in data && data['status'] == 'done') {
                var submission_link = jQuery('<a/>', {
                    id: "my_submission",
                    class: "submission list-group-item list-group-item-info",
                    "data-submission-id": id
                }).on('click', clickOnSubmission);

                jQuery('<i/>', {class: "fa fa-chevron-right fa-fw"}).appendTo(submission_link).after("&nbsp;");
                submission_link.append(text);

                if (fade) {
                    $("#my_submission").fadeOut(function () {
                        $(this).replaceWith(submission_link.fadeIn().removeAttr('style'));
                    });
                } else {
                    $("#my_submission").replaceWith(submission_link);
                }
            }
        }

        if(makepost)
            jQuery.post(url, {"@action": "set_submission", "submissionid": id}, null, "json").done(applyfn);
        else
            applyfn({"status":"done"})
    }

    updateTaskStatus(item.hasClass("list-group-item-success") ? "Succeeded" : "Failed", parseFloat(item.text().split("-")[1]));
}

//Submission's click handler
function clickOnSubmission()
{
    if(loadingSomething)
        return;
    loadOldSubmissionInput($(this).attr('data-submission-id'), true);
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

//Verify the task form (files, ...)
function taskFormValid()
{
    var answered_to_all = true;
    var errors = [];
    var form = $('#task');

    form.find('textarea,input[type="text"]').each(function()
    {
        if($(this).attr('name') != undefined) //skip codemirror's internal textareas
        {
            if($(this).val() == "" && $(this).attr('data-optional') != "True")
                answered_to_all = false;
        }
    });

    form.find('input[type="checkbox"],input[type="radio"]').each(function()
    {
        if(form.find("input[name='"+ $(this).attr('name')+"']:checked").length == 0)
        {
            answered_to_all = false;
        }
    });

    form.find('input[type="file"]').each(function()
    {
        var filename = $(this).val().split(/(\\|\/)/g).pop();

        //file input fields cannot be optional
        if(filename == "")
        {
            answered_to_all = false;
            return;
        }

        //verify ext
        var allowed_extensions = $.parseJSON($(this).attr('data-allowed-exts'));
        var has_one = false;
        $.each(allowed_extensions, function(idx, ext){
            has_one = has_one || (filename.lastIndexOf(ext) === filename.length - ext.length) > 0;
        });
        if(!has_one)
            errors.push($("#invalidext").text().replace("{}", filename));

        //try to get the size of the file
        var size = -1;
        try { size = $(this)[0].files[0].size; } catch (e) {} //modern browsers
        if(size == -1) try { size = $(this)[0].files[0].fileSize; } catch(e) { } //old versions of Firefox

        //Verify the maximum size
        var max_size = parseInt($(this).attr('data-max-size'));
        if(size != -1 && size > max_size)
            errors.push($("#filetooheavy").text().replace("{}", filename));
    });

    if(!answered_to_all)
    {
        errors.push($("#answerall").text());
    }

    if(errors.length != 0)
    {
        var task_alert = $('#task_alert');
        var content = $('<div></div>');
        var first = true;
        $.each(errors, function(idx, elem){
            if(!first)
                content.append($('<br>'));
            first = false;
            content.append($('<span></span>').text(elem));
        });
        task_alert.html(getAlertCode(content.html(), "danger", false));
        $('html, body').animate({
            scrollTop: task_alert.offset().top - 100
        }, 200);
        return false;
    }
    else
    {
        return true;
    }
}

//Submits a task
function submitTask(with_ssh)
{
    if(loadingSomething)
        return;

    if(!taskFormValid())
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
                              displayTaskLoadingAlert(data, data["submissionid"]);
                              incrementTries();
                              displayNewSubmission(data['submissionid']);
                              waitForSubmission(data['submissionid']);
                          }
                          else if("status" in data && data['status'] == "error" && "text" in data)
                          {
                              displayTaskStudentAlertWithProblems(data, "danger", false);
                              updateTaskStatus(data["text"], 0);
                              unblurTaskForm();
                          }

                          if("remove" in data) {
                              data["remove"].forEach(function(element, index, array) {
                                 removeSubmission(element);
                              });
                          }
                      },
            error:    function()
                      {
                          displayTaskStudentAlertWithProblems($("#internalerror").text(), "danger", false);
                          updateTaskStatus($("#internalerror").text(), 0);
                          unblurTaskForm();
                      }
        });

    blurTaskForm();
    resetAlerts();
    displayTaskLoadingAlert(null, null);
    updateTaskStatus("<i class=\"fa fa-spinner fa-pulse fa-fw\" aria-hidden=\"true\"></i>", 0);
    $('html, body').animate({
        scrollTop: $('#task_alert').offset().top - 100
    }, 200);
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
                    if("ssh_host" in data && "ssh_port" in data && "ssh_password" in data)
                        displayRemoteDebug(submissionid, data);
                    else
                        displayTaskLoadingAlert(data, submissionid);

                }
                else if("status" in data && "result" in data && "grade" in data)
                {
                    if("debug" in data)
                        displayDebugInfo(data["debug"]);

                    if(data['result'] == "failed")
                        displayTaskStudentAlertWithProblems(data, "danger", false);
                    else if(data['result'] == "success")
                        displayTaskStudentAlertWithProblems(data, "success", false);
                    else if(data['result'] == "timeout")
                        displayTaskStudentAlertWithProblems(data, "warning", false);
                    else if(data['result'] == "overflow")
                        displayTaskStudentAlertWithProblems(data, "warning", false);
                    else if(data['result'] == "killed")
                        displayTaskStudentAlertWithProblems(data, "warning", false);
                    else // == "error"
                        displayTaskStudentAlertWithProblems(data, "danger", false);

                    updateSubmission(submissionid, data['result'], data["grade"]);
                    unblurTaskForm();

                    if("replace" in data && data["replace"]) {
                        setSelectedSubmission(submissionid, true);
                    } else {
                        setSelectedSubmission($('#my_submission').attr('data-submission-id'), false);
                    }
                }
                else
                {
                    displayTaskStudentAlertWithProblems($("#internalerror").text(), "danger", false);
                    updateSubmission(submissionid, "error", "0.0");
                    updateTaskStatus("Failed", 0);
                    unblurTaskForm();
                }

            })
            .fail(function()
            {
                displayTaskStudentAlertWithProblems($("#internalerror").text(), "danger", false);
                updateSubmission(submissionid, "error", "0.0");
                updateTaskStatus("Failed", 0);
                unblurTaskForm();
            });
    }, 1000);
}

//Kill a running submission
function killSubmission(submissionid)
{
    $('.kill-submission-btn').attr('disabled', 'disabled');
    var url = $('form#task').attr("action");
    jQuery.post(url, {"@action": "kill", "submissionid": submissionid}, null, "json").done(function()
    {
        $('.kill-submission-btn').removeAttr('disabled');
    }).fail(function()
    {
        $('.kill-submission-btn').removeAttr('disabled');
    });
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

//Get the code for a "loading" alert, with a button to kill the current submission
function getLoadingAlertCode(content, submissionid)
{
    var kill_button = "";
    if(submissionid != null)
        kill_button =   "<button type='button' onclick='killSubmission(\""+submissionid+"\")' class='btn btn-danger kill-submission-btn btn-small'>"+
                            "<i class='fa fa-close'></i>"+
                        "</button>";
    var div_content =   "<div class='loading-alert'>"+content+"</div>";
    return getAlertCode(kill_button + div_content, "info", false);
}

//Displays a loading alert in task form
function displayTaskLoadingAlert(submission_wait_data, submissionid)
{
    var task_alert = $('#task_alert');
    var content = '<i class="fa fa-spinner fa-pulse fa-fw" aria-hidden="true"></i> ';
    if(submission_wait_data != null)
        content += submission_wait_data["text"];
    task_alert.html(getLoadingAlertCode(content, submissionid));
}

//Display informations for remote debugging
function displayRemoteDebug(submissionid, submission_wait_data)
{
    var ssh_host = submission_wait_data["ssh_host"];
    var ssh_port = submission_wait_data["ssh_port"];
    var ssh_password = submission_wait_data["ssh_password"];

    var pre_content = "ssh worker@" + ssh_host + " -p " + ssh_port+ " -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no";
    var task_alert = $('#task_alert');
    var content = '<i class="fa fa-spinner fa-pulse fa-fw" aria-hidden="true"></i> ';
    content += submission_wait_data["text"];

    //If not already set
    if($('pre#commandssh', task_alert).text() != pre_content)
    {
        var remote_info = $("#ssh_template").clone();
        remote_info.attr("id", "ssh_remote_info");

        $('#commandssh', remote_info).text(pre_content);

        // Generate iframe
        var webtermdiv = $("#webterm", remote_info);
        var webterm_link = $('#webterm_link', remote_info).val();
        if(webterm_link != undefined)
        {
            var full_link = webterm_link + "?host=" + ssh_host + "&port=" + ssh_port + "&password=" + ssh_password;
            var iframe = $('<iframe>', {
                src:         full_link,
                id:          'iframessh',
                frameborder: 0,
                scrolling:   'no'
            }).appendTo(webtermdiv);
        }

        task_alert.html(getLoadingAlertCode(content, submissionid));
        remote_info.appendTo($(".loading-alert"), task_alert);
        $("#ssh_remote_info code", task_alert).text(ssh_password);
        $("#ssh_remote_info", task_alert).show();
    }
}

//Displays a loading input alert in task form
function displayTaskInputLoadingAlert()
{
    var task_alert = $('#task_alert');
    task_alert.html(getAlertCode("<i class=\"fa fa-spinner fa-pulse fa-fw\" aria-hidden=\"true\"></i>", "info", false));
    $('html, body').animate(
        {
            scrollTop: task_alert.offset().top - 100
        }, 200);
}

//Displays a loading input alert in task form
function displayTaskInputErrorAlert()
{
    var task_alert = $('#task_alert');
    task_alert.html(getAlertCode("<b>" + $("#internalerror").text() + "</b>", "danger", false));
    $('html, body').animate(
        {
            scrollTop: task_alert.offset().top - 100
        }, 200);
}

//Displays a student error alert in task form
function displayTaskStudentAlertWithProblems(content, type)
{
    resetAlerts();

    var firstPos = -1;
    var task_alert = $('#task_alert');

    if("text" in content && content.text != "")
    {
        task_alert.html(getAlertCode(content.text, type, true));
        firstPos = task_alert.offset().top;
    }

    if("problems" in content)
    {
        $(".task_alert_problem").each(function(key, elem)
        {
            var problemid = elem.id.substr(11); //skip "task_alert."
            if(problemid in content.problems)
            {
                var alert_type = "danger";
                if(content.problems[problemid][0] == "timeout" || content.problems[problemid][0] == "overflow")
                    alert_type = "warning";
                if(content.problems[problemid][0] == "success")
                    alert_type = "success";
                $(elem).html(getAlertCode(content.problems[problemid][1], alert_type, true));
                if(firstPos == -1 || firstPos > $(elem).offset().top)
                    firstPos = $(elem).offset().top;
            }
        });
    }

    $('html, body').animate(
    {
        scrollTop: firstPos - 100
    }, 200);

    colorizeStaticCode();
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
function loadOldSubmissionInput(id, with_feedback)
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
                if(with_feedback)
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
            displayTaskStudentAlertWithProblems(data, "danger", false);
        else if(data['result'] == "success")
            displayTaskStudentAlertWithProblems(data, "success", false);
        else if(data['result'] == "timeout")
            displayTaskStudentAlertWithProblems(data, "warning", false);
        else if(data['result'] == "overflow")
            displayTaskStudentAlertWithProblems(data, "warning", false);
        else if(data['result'] == "killed")
            displayTaskStudentAlertWithProblems(data, "warning", false);
        else // == "error"
            displayTaskStudentAlertWithProblems(data, "danger", false);
    }
    else
        displayTaskStudentAlertWithProblems($("#internalerror").text(), "danger", false);
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
            else if($(this).attr('type') == "checkbox" && jQuery.isArray(input[id]) && $.inArray($(this).prop('value'), input[id]) >= 0)
                $(this).prop('checked', true);
            else if($(this).attr('type') == "radio" && $(this).prop('value') == input[id])
                $(this).prop('checked', true);
            else if($(this).attr('type') == "checkbox" || $(this).attr('type') == "radio")
                $(this).prop('checked', false);
            else if($(this).attr('type') == 'file')
            {
                //display the download button associated with this file
                var input_file = $('#download-input-file-' + id);
                input_file.attr('href', document.location.pathname + "?submissionid=" + submissionid + "&questionid=" + id);
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
