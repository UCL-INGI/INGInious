function getTaskIdFromUrl() {
    var urlTokens = window.location.pathname.split("/");
    return urlTokens[urlTokens.length - 1];
}

function getCourseIdFromUrl() {
    var urlTokens = window.location.pathname.split("/");
    return urlTokens[urlTokens.length - 2];
}

function displayTaskWaitingForUnsavedJob () {
    var task_alert = $('#task_alert');
    var content = '<i class="fa fa-spinner fa-pulse fa-fw" aria-hidden="true"></i> <b>Evaluating...</b>';
    var div_content = "<div class='loading-alert'>"+content+"</div>";
    task_alert.html(getAlertCode(div_content, "info", false));
}

function displayCustomInputSuccessfullyRan() {
    var task_alert = $('#task_alert');
    var content = 'Your code has finished executing';
    var div_content = "<div class='loading-alert'>"+content+"</div>";
    task_alert.html(getAlertCode(div_content, "info", false));
}

function runCustomInput(inputId) {
    var customTestOuputArea = $('#customoutput-'+inputId);

    var runCustomInputCallBack = function (data) {
        unblurTaskForm();

        data = JSON.parse(data);
        if ('status' in data && data['status'] === 'done'
              && ('result' in data) ){
            customTestOuputArea.text(data.text);
        }

        displayCustomInputSuccessfullyRan();
    };

    blurTaskForm();
    resetAlerts();
    displayTaskWaitingForUnsavedJob();
    customTestOuputArea.text('Running...');

    var taskForm = new FormData($('form#task')[0]);
    console.log(taskForm);
    
    taskForm.set("@submission_type", "customtest");
    taskForm.set("courseid", getCourseIdFromUrl());
    taskForm.set("taskid", getTaskIdFromUrl());

    $.ajax({
        url: '/api/custom_input/',
        method: "POST",
        dataType: 'json',
        data: taskForm,
        processData: false,
        contentType: false,
        success: runCustomInputCallBack,
        error: function (er) {
            unblurTaskForm();
        }
    });
}
