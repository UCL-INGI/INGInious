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

    var codeUploadLink = $('a[id^="link"]');
    codeUploadLink.each(function() {
        var codeUploadLinkID = $(this).attr('id');
        $(this).click(function(e) {
            var fileUploaderID = 'file' + codeUploadLinkID;
            var fileUploaderElement = $('#' + fileUploaderID);
            fileUploaderElement.click();
            e.preventDefault();
        });
    });

    var codeUploadInput = $('input[id^="filelink"]');
    codeUploadInput.each(function() {
        var codeUploadInputId = $(this).attr('id');
        var textareaId = codeUploadInputId.replace("filelink-", "");
        var input = this;
        var isCodeMirrorArea = $('#'+textareaId).hasClass("code-editor");
        var textarea = $('#'+textareaId)[0];

        $(this).change(function(e) {
            var reader = new FileReader();
            reader.onload = function(event) {
                var contents = event.target.result;

                if (isCodeMirrorArea) {
                    var editor = getEditorForProblemId(textareaId);
                    editor.setValue(contents, -1);
                } else
                    textarea.value = contents;
            };
            reader.readAsText(input.files[0]);
        });
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

    var custominputAreas = $('textarea[id^="custominput"]');
    custominputAreas.each(function() {
        $(this).attr("readonly", true);
        $(this).css("background-color", "#fff");
    });

    var task_form = $('form#task');
    $("input, button, select", task_form).attr("disabled", "disabled").addClass('form-blur');
    //task_form.addClass('form-blur');
    loadingSomething = true;
}

function unblurTaskForm()
{
    $.each(codeEditors, function(idx, editor)
    {
        editor.setOption("readOnly", false);
    });

    var custominputAreas = $('textarea[id^="custominput"]');
    custominputAreas.each(function() {
        $(this).attr("readonly", false);
    });

    var task_form = $('form#task');
    $("input, button, select", task_form).removeAttr("disabled").removeClass('form-blur');
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
        var shouldCheckElement = $(this).attr('name') != undefined && !$(this).attr('id').includes("custominput");
        if(shouldCheckElement) //skip codemirror's internal textareas and custominput areas
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

        //file input fields cannot be optional (unless it is an input defined for submitting using a link)
        if(filename == "") {
            var idDefined = $(this).get(0).hasAttribute('id');
            if (!idDefined || !$(this).attr("id").includes("filelink"))
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
            errors.push(filename+" has not a valid extension.");

        //try to get the size of the file
        var size = -1;
        try { size = $(this)[0].files[0].size; } catch (e) {} //modern browsers
        if(size == -1) try { size = $(this)[0].files[0].fileSize; } catch(e) { } //old versions of Firefox

        //Verify the maximum size
        var max_size = parseInt($(this).attr('data-max-size'));
        if(size != -1 && size > max_size)
            errors.push(filename + " is too heavy.");
    });

    if(!answered_to_all)
    {
        errors.push("Please answer to all the questions.");
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
                              displayTaskLoadingAlert(null, data["submissionid"]);
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

                          if("remove" in data) {
                              data["remove"].forEach(function(element, index, array) {
                                 removeSubmission(element);
                              });
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
    displayTaskLoadingAlert(null, null);
    updateTaskStatus("Waiting for verification", 0);
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
                        displayRemoteDebug(submissionid, data["ssh_host"], data["ssh_port"], data["ssh_password"])
                    else
                        displayTaskLoadingAlert(data, submissionid);
                }
                else if("status" in data && "result" in data && "grade" in data)
                {
                    if("debug" in data) {
                        displayDebugInfo(data["debug"]);
                        displayOutputDiff(data["debug"]);
                    }

                    if(data['result'] == "failed")
                    {
                        displayTaskStudentErrorAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        unblurTaskForm();
                    }
                    else if(data['result'] == "success")
                    {
                        displayTaskStudentSuccessAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        unblurTaskForm();
                    }
                    else if(data['result'] == "timeout")
                    {
                        displayTimeOutAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        unblurTaskForm();
                    }
                    else if(data['result'] == "overflow")
                    {
                        displayOverflowAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        unblurTaskForm();
                    }
                    else if(data['result'] == "killed")
                    {
                        displayKilledAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        unblurTaskForm();
                    }
                    else // == "error"
                    {
                        displayTaskErrorAlert(data);
                        updateSubmission(submissionid, data['result'], data["grade"]);
                        unblurTaskForm();
                    }

                    if("replace" in data && data["replace"]) {
                        setSelectedSubmission(submissionid, true);
                    } else {
                        setSelectedSubmission($('#my_submission').attr('data-submission-id'), false);
                    }
                }
                else
                {
                    displayTaskErrorAlert({});
                    updateSubmission(submissionid, "error", "0.0");
                    updateTaskStatus("Failed", 0);
                    unblurTaskForm();
                }

            })
            .fail(function()
            {
                displayTaskErrorAlert({});
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

function parseOutputDiff(diff) {
  var result = [];
  var lines = diff.split('\n');

  // Convention
  result.push('<strong>Legend:</strong> <span class="diff-missing-output">Only in the expected output</span> ' +
    '<span class="diff-additional-output">Only in your output</span> ' +
    '<span class="diff-common">Common</span> ' +
    '<span class="diff-position-control">Context information</span>');

  for(var i = 0; i < lines.length; ++i) {
    var line = lines[i];
    var output = null;

    if (line.startsWith("---")) {
      output = '<span class="diff-missing-output">' + line.substring(4) + '</span>';
    } else if (line.startsWith("+++")) {
      output = '<span class="diff-additional-output">' + line.substring(4) + '</span>';
    } else if (line.startsWith("@@")) {
      output = '<span class="diff-position-control">' + line + '</span>';
    } else if (line.startsWith("-")) {
      output = '<span class="diff-missing-output">' + line.substring(1) + '</span>';
    } else if (line.startsWith("+")) {
      output = '<span class="diff-additional-output">' + line.substring(1) + '</span>';
    } else if (line.startsWith(" ")) {
      output = '<span class="diff-common">' + line.substring(1) + '</span>';
    } else if (line.startsWith("...")) {
      output = '<span class="diff-position-control">' + line + '</span>';
    } else if (line === "") {
      // The diff output includes empty lines after position control lines, so we keep them
      // unformatted to avoid misleading the user (they are not actually part of any of the outputs)
      output = line;
    } else {
      throw new Error("Unable to parse diff line: " + line);
    }

    result.push(output);
  }

  return result.join("\n");
}

function updateDiffBlock(blockId) {
  var block = $("#" + blockId);
  block.html(parseOutputDiff(block.html()));
}

function displayOutputDiff(debugInfo)
{
    var container = $('#task_diff');
    var data = $(document.createElement('dl'));
    data.text(" ");
    container.html(data);

    var files_feedback = debugInfo;
    files_feedback = (files_feedback["custom"] || {});
    files_feedback = JSON.parse(files_feedback["additional_info"] || "{}");
    files_feedback = (files_feedback["files_feedback"] || []);

    var keys = $.map(files_feedback, function(element, index) { return index; });
    keys.sort();

    for (var i = 0; i < keys.length; ++i) {
      var key = keys[i];
      var element = files_feedback[key];

      var namebox = $(document.createElement('dt'));
      var content = $(document.createElement('dd'));
      data.append(namebox);
      data.append(content);

      namebox.text("Test case " + key);
      var collapseId = "collapseDiffAdmin" + i;

      var diff = element["diff"] || '';
      var html = '<a class="btn btn-default btn-link btn-xs" role="button"' +
        'data-toggle="collapse" href="#' + collapseId + '" aria-expanded="false" ' +
        'aria-controls="' + collapseId + '">Toggle diff</a>' +
        '<div class="collapse" id="' + collapseId + '"><pre>' + parseOutputDiff(diff) + '</pre></div>';

      content.html(html);
    }
}

//Get the code for a "loading" alert, with a button to kill the current submission
function getLoadingAlertCode(content, submissionid)
{
    var kill_button = "";
    if(submissionid != null)
        kill_button = "<button type='button' onclick='killSubmission(\""+submissionid+"\")' class='btn btn-danger kill-submission-btn btn-small'>"+
                        "<i class='fa fa-close'></i>"+
                        "</button>";
    var div_content = "<div class='loading-alert'>"+content+"</div>";
    return getAlertCode(kill_button + div_content, "info", false);
}

//Displays a loading alert in task form
function displayTaskLoadingAlert(submission_wait_data, submissionid)
{
    var task_alert = $('#task_alert');
    var content = '<i class="fa fa-spinner fa-pulse fa-fw" aria-hidden="true"></i> ';
    if(submission_wait_data != null && "nb_tasks_before" in submission_wait_data && "approx_wait_time" in submission_wait_data) {
        var nb_tasks_before = submission_wait_data["nb_tasks_before"];
        var wait_time = Math.round(submission_wait_data["approx_wait_time"]);
        if(nb_tasks_before == -1 && wait_time <= 0)
            content += "<b>INGInious is currently grading your answers.<b/> (almost done)";
        else if(nb_tasks_before == -1)
            content += "<b>INGInious is currently grading your answers.<b/> (Approx. wait time: "+wait_time+" seconds)";
        else if(nb_tasks_before == 0)
            content += "<b>You are next in the waiting queue!</b>";
        else if(nb_tasks_before == 1)
            content += "<b>There is one task in front of you in the waiting queue.</b>";
        else
            content += "<b>There are " + nb_tasks_before + " tasks in front of you in the waiting queue.</b>";
    }
    else
        content += "<b>Your submission has been sent...</b>";
    task_alert.html(getLoadingAlertCode(content, submissionid));
}

function displayTaskWaitingForUnsavedJob () {
    var task_alert = $('#task_alert');
    var content = '<i class="fa fa-spinner fa-pulse fa-fw" aria-hidden="true"></i> <b>Evaluating...</b>';
    var div_content = "<div class='loading-alert'>"+content+"</div>";
    task_alert.html(getAlertCode(div_content, "info", false));
}

//Display informations for remote debugging
function displayRemoteDebug(submissionid, ssh_host, ssh_port, ssh_password)
{
    var pre_content = "ssh worker@" + ssh_host + " -p " + ssh_port+ " -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no";
    var task_alert = $('#task_alert');

    //If not already set
    if($('pre#commandssh', task_alert).text() != pre_content)
    {

        var manual_content_1 = "Paste this command into your terminal:<br/>";
        var pre = $('<pre id="commandssh"><pre>').text(pre_content);
        var manual_content_2 = "The password to connect is <code>" + ssh_password + "</code><br/>";

        var alert = $(getLoadingAlertCode("<b>SSH server active</b><br/>", submissionid));
        alert.attr('id', 'ssh_remote_info');

        // Generate iframe
        var webterm_link = $('#webterm_link').val();
        if(webterm_link != undefined)
        {
            var full_link = webterm_link + "?host=" + ssh_host + "&port=" + ssh_port + "&password=" + ssh_password;
            var iframe = $('<iframe>', {
                src:         full_link,
                id:          'iframessh',
                frameborder: 0,
                scrolling:   'no'
            }).appendTo(alert);
            manual_content_1 = "Alternatively, you can also paste this command into your terminal:<br/>";
        }

        alert.append(manual_content_1);
        alert.append(pre);
        alert.append(manual_content_2);

        task_alert.empty().append(alert);
    }
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
function displayCustomTestAlertError(content)
{
    displayTaskStudentAlertWithProblems(content, "<b>Custom test error</b>", "danger", false);
}

//Displays an overflow error alert in task form
function displayOverflowAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>Your submission made an overflow. Your score is " + content["grade"] + "%</b>",
        "warning", false);
}

//Displays a 'killed' alert in task form
function displayKilledAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>Your submission was killed.</b>",
        "warning", false);
}

//Displays a timeout error alert in task form
function displayTimeOutAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>Your submission timed out. Your score is " + content["grade"] + "%</b>",
        "warning", false);
}

//Displays an internal error alert in task form
function displayTaskErrorAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>An internal error occurred. Please retry later. If the error persists, send an email to the course administrator.</b>",
        "danger", false);
}

//Displays a student error alert in task form
function displayTaskStudentErrorAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>There are some errors in your answer. Your score is " + content["grade"] + "%</b>",
        "danger", false);
}

//Displays a student success alert in task form
function displayTaskStudentSuccessAlert(content)
{
    displayTaskStudentAlertWithProblems(content,
        "<b>Your answer passed the tests! Your score is " + content["grade"] + "%</b>",
        "success", true);
}

//Displays a student error alert in task form
function displayTaskStudentAlertWithProblems(content, top, type, alwaysShowTop)
{
    resetAlerts();

    var firstPos = -1;
    var task_alert = $('#task_alert');

    if("text" in content && content.text != "")
    {
        task_alert.html(getAlertCode(top + "<br/>" + content.text, type, true));
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

    if(firstPos == -1 || (alwaysShowTop && !("text" in content && content.text != "")))
    {
        task_alert.html(getAlertCode(top, type, true));
        firstPos = task_alert.offset().top;
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
        if("debug" in data) {
            displayDebugInfo(data["debug"]);
            displayOutputDiff(data["debug"]);
        }

        if(data['result'] == "failed")
            displayTaskStudentErrorAlert(data);
        else if(data['result'] == "success")
            displayTaskStudentSuccessAlert(data);
        else if(data['result'] == "timeout")
            displayTimeOutAlert(data);
        else if(data['result'] == "overflow")
            displayOverflowAlert(data);
        else if(data['result'] == "killed")
            displayKilledAlert(data);
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

        if(input[name + "/language"]){
            setDropDownWithTheRightLanguage(name, input[name + "/language"]);
            changeSubmissionLanguage(name);
        }
    })
}

function setDropDownWithTheRightLanguage(problemId, language) {
    if(!language)
      return;
    var dropdown = document.getElementById(problemId + '/language');
    if(!dropdown)
        return;

    dropdown.value = language;
}

function changeSubmissionLanguage(problemId){
    var language = getLanguageForProblemId(problemId);
    var editor = getEditorForProblemId(problemId);
    var mode = CodeMirror.findModeByName(language);
    editor.setOption("mode", mode.mime);
    CodeMirror.autoLoadMode(editor, mode["mode"]);
    editor.updateLintStatus([]);
}

function getLanguageForProblemId(problemId){
    var codemirrorLanguages = {
        "java7": "java",
        "java8": "java",
        "js": "javascript",
        "cpp": "cpp",
        "cpp11": "cpp",
        "c": "c",
        "c11": "c",
        "python2": "python",
        "python3": "python",
        "ruby": "ruby"
    }

    var dropdown = document.getElementById(problemId + '/language');
    if(dropdown == null)
        return "plain";

    var backEndLanguage = dropdown.options[dropdown.selectedIndex].value;
    return codemirrorLanguages[backEndLanguage];
}

var PythonTutor = (function () {
    function PythonTutor(problemId, language) {
        this.defaultVisualServer = "http://127.0.0.1:8003/";
        this.javaVisualServer = "https://cscircles.cemc.uwaterloo.ca/";

        this.problemId = problemId;
        this.code = getEditorForProblemId(problemId).getValue();

        if (language == "plain")
            language = getLanguageForProblemId(this.problemId);

        this.language = language;
        this.input = document.getElementById("custominput-" + this.problemId).value;
    }

    PythonTutor.prototype.visualize = function () {
        var iframe = this.createIFrameFromCode();
        this.showIFrameIntoModal(iframe);
    };

    PythonTutor.prototype.createIFrameFromCode = function () {
        var iframe = document.createElement('iframe');
        iframe.src = this.generateVisualizerUrl();
        iframe.height = "650";
        iframe.width = "100%";
        iframe.frameborder = "0";
        return iframe;
    };

    PythonTutor.prototype.showIFrameIntoModal = function (iframe) {
        var modal = document.getElementById("modal-" + this.problemId);
        var modalBody = modal.getElementsByClassName("modal-body")[0];
        $(modalBody).empty();
        modalBody.innerHTML = "Plase wait while we excecute your code, this may take up to 10 seconds";
        modalBody.appendChild(iframe);
    };

    PythonTutor.prototype.generateVisualizerUrl = function () {
        if(this.language == "java")
            return this.generateJavaUrl();
        else
            return this.generateGenericUrl();
    };

    PythonTutor.prototype.generateJavaUrl = function () {
        var data = {
            "user_script": this.code,
            "options":{"showStringsAsValues":true,"showAllFields":false},
            "args":[],
            "stdin": this.input
        };

        return this.serverResource()
            + window.encodeURIComponent(JSON.stringify(data))
            + "&cumulative=false"
            + "&heapPrimitives=false"
            + "&drawParentPointers=false"
            + "&textReferences=false"
            + "&showOnlyOutputs=false"
            + "&py=3"
            + "&curInstr=0"
            + "&resizeContainer=true"
            + "&highlightLines=true"
            + "&rightStdout=true"
            + "&codeDivHeight=450"
            + "&codeDivWidth=500";
    };

    PythonTutor.prototype.generateGenericUrl = function () {
        var codeToURI = window.encodeURIComponent(this.code);
        var url = this.serverResource()
            + codeToURI
            + "&mode=edit"
            + "&py=" + this.languageURIName()
            + "&codeDivHeight=450"
            + "&codeDivWidth=500"
            + "&rawInputLstJSON=" + this.encodedInputArray();
        return url;
    };

    PythonTutor.prototype.serverResource = function () {
        if (this.language == "java")
            return this.javaVisualServer + "java_visualize/iframe-embed.html?faking_cpp=false#data=";
        return this.defaultVisualServer + "iframe-embed.html#code=";
    };

    PythonTutor.prototype.languageURIName = function () {
        if (this.language == "javascript")
            return "js";
        if (this.language == "python")
            return "2";
        return this.language;
    };

    PythonTutor.prototype.encodedInputArray = function() {
        var inputAsArray = this.input.split("\n");
        return window.encodeURIComponent(JSON.stringify(inputAsArray));
    };

    return PythonTutor;
}());

function visualizeCode(language, problemId){
    var pythonTutor = new PythonTutor(problemId, language);
    pythonTutor.visualize();
}

var lintServerUrl = "http://localhost:4567/";

function lintCode(language, problemId, callback){
  if(language == "plain")
    language = getLanguageForProblemId(problemId);
  var editor =  getEditorForProblemId(problemId);
  var code = editor.getValue();
  var apiUrl = lintServerUrl + language;
  callback = callback || getCallbackForLanguage(language, editor);

  $.post(apiUrl, { code: code }, callback);
}

function getCallbackForLanguage(language, editor){
  if(language == "java") return updateLintingCallback(editor);
  if(language == "python") return updateLintingCallback(editor);
  if(language == "cpp") return updateLintingCallback(editor);
  if(language == "c") return updateLintingCallback(editor);
  return defaultCallback;
}

var updateLintingCallback = function(editor){
  return function(response, status){
    var errors_and_warnings = JSON.parse(response);
    editor.updateLintStatus(errors_and_warnings);
  }
}

function makeNewTabFromResponseCallback(response, status){
  var newTabUrl = "data:text/html," + window.encodeURIComponent(response);
  var newWindow = window.open(newTabUrl, '_blank');
}

function defaultCallback(response, status){
  alert(response + "\n\nresponse_status: " + status);
}

function runCustomTest (inputId) {
    var customTestOutputArea = $('#customoutput-'+inputId);
    var placeholderSpan = "<span class='placeholder-text'>Your output goes here</span>";

    var runCustomTestCallBack = function (data) {
        customTestOutputArea.empty();

        if ('status' in data && data['status'] == 'done') {
            if ('result' in data) {
                var result = data['result'];
                var stdoutSpan = $("<span/>").addClass("stdout-text").text(data.stdout);
                var stderrSpan = $("<span/>").addClass("stderr-text").text(data.stderr);
                customTestOutputArea.append(stdoutSpan);
                customTestOutputArea.append(stderrSpan);

                if (result == 'failed') {
                    displayCustomTestAlertError(data);
                } else if (result == "timeout") {
                    displayTimeOutAlert(data);
                } else if (result == "overflow") {
                    displayOverflowAlert(data);
                } else if (result != "success" ){
                    displayCustomTestAlertError(data);
                }
            }
        } else if ('status' in data && data['status'] == 'error') {
            customTestOutputArea.html(placeholderSpan);
            displayCustomTestAlertError(data);
        } else {
            customTestOutputArea.html(placeholderSpan);
            displayCustomTestAlertError({});
        }

        unblurTaskForm();
    }

    var taskForm = new FormData($('form#task')[0]);
    taskForm.set("@action", "customtest");
    var taskUrl = $('form#task').attr("action");

    blurTaskForm();
    resetAlerts();
    customTestOutputArea.html("Running...");

    $.ajax({
            url: taskUrl,
            method: "POST",
            dataType: 'json',
            data: taskForm,
            processData: false,
            contentType: false,
            success: runCustomTestCallBack,
            error: function (error) {
                unblurTaskForm();
                customTestOutputArea.html(placeholderSpan);
            }
    });
}

function toggleElement (id) {
    var element = document.getElementById(id);
    if (element.style.display === 'none') {
        element.style.display = 'block';
    } else {
        element.style.display = 'none';
    }
}
