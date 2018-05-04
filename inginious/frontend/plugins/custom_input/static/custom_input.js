function getTaskIdFromUrl() {
    var urlTokens = window.location.pathname.split("/");
    return urlTokens[urlTokens.length - 1];
}

function getCourseIdFromUrl() {
    var urlTokens = window.location.pathname.split("/");
    return urlTokens[urlTokens.length - 2];
}

function displayCustomTestAlertError(content) {
    displayTaskStudentAlertWithProblems(content, "<b>Custom test error</b>", "danger", false);
}

function runCustomTest (inputId) {
    var customTestOutputArea = $('#customoutput-'+inputId);
    var placeholderSpan = "<span class='placeholder-text'>Your output goes here</span>";

    var runCustomTestCallBack = function (data) {
        data = JSON.parse(data);
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
    taskForm.set("submit_action", "customtest");
    taskForm.set("courseid", getCourseIdFromUrl());
    taskForm.set("taskid", getTaskIdFromUrl());

    var taskUrl = $('form#task').attr("action");

    blurTaskForm();
    resetAlerts();
    customTestOutputArea.html("Running...");

    $.ajax({
            url: '/api/custom_input/',
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
