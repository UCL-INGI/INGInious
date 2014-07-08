$(function()
{
    $('form#task').on('submit', function(){submitTask(); return false;});
    if($('form#task').attr("data-wait-submission"))
    {
    	blurTaskForm();
        resetAlerts();
        displayTaskLoadingAlert();
    	waitForSubmission($('form#task').attr("data-wait-submission"));
    }
    $('#submissions .submission').on('click', clickOnSubmission)
});

//Contains all code editors
var codeEditors=[]

//True if loading something
var loadingSomething = false;

//Register and init a code editor (ace)
function registerCodeEditor(id,lang,lines)
{
    var editor = ace.edit(id);
    if(lang != "plain")
        editor.getSession().setMode("ace/mode/"+lang);
    editor.getSession().setTabSize(4);
    editor.setOptions({minLines: lines,maxLines: lines});
    
    var textarea = jQuery('input[name="'+id+'"]');
    editor.getSession().on("change", function()
    {
        textarea.val(editor.getSession().getValue());
    });
    
    codeEditors.push(editor);
}

//Blur task form
function blurTaskForm()
{
    for (idx in codeEditors)
        codeEditors[idx].setReadOnly(true);
    $("form#task input, form#task button").attr("disabled","disabled");
    $("form#task").addClass('form-blur');
    loadingSomething = true;
}
function unblurTaskForm()
{
    for (idx in codeEditors)
        codeEditors[idx].setReadOnly(false);
    $("form#task input, form#task button").removeAttr("disabled");
    $("form#task").removeClass('form-blur');
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
	$('#task_tries').text(parseInt($('#task_tries').text())+1);
}

//Update task status
function updateTaskStatus(newStatus)
{
	currentStatus = $('#task_status').text().trim();
	if(currentStatus == "Suceeded")
		return;
	$('#task_status').text(newStatus)
}

//Creates a new submission (left column)
function displayNewSubmission(id)
{
	$('#submissions .submission-empty').remove();
	
	$('#submissions').prepend($('<a></a>')
			.addClass('submission').addClass('list-group-item')
			.addClass('list-group-item-warning')
			.attr('data-submission-id',id).text(getDateTime()).on('click',clickOnSubmission))
}

//Updates a loading submission
function updateSubmission(id,result)
{
	nclass = "";
	if(result == "success") nclass="list-group-item-success";
	else if(result == "save") nclass="list-group-item-save";
	else nclass="list-group-item-danger";
	$('#submissions .submission').each(function(){
		if ($(this).attr('data-submission-id').trim() == id)
			$(this).removeClass('list-group-item-warning').addClass(nclass);
	});
}

//Submission's click handler
function clickOnSubmission()
{
	if(loadingSomething)
		return;
	loadOldSubmissionInput($(this).attr('data-submission-id'));
}

//Get current datetime
function getDateTime()
{
	var MyDate = new Date();

	return 		 ('0' + MyDate.getDate()).slice(-2) + '/'
	             + ('0' + (MyDate.getMonth()+1)).slice(-2) + '/'
	             + MyDate.getFullYear() + " "
	             + ('0' + MyDate.getHours()).slice(-2) + ':'
	             + ('0' + MyDate.getMinutes()).slice(-2) + ':'
	             + ('0' + MyDate.getSeconds()).slice(-2);
}

//Submits a task
function submitTask()
{
	if(loadingSomething)
		return;
	
    var form = $('form#task');
    serialized = form.serialize();
    
    blurTaskForm();
    resetAlerts();
    displayTaskLoadingAlert();
    incrementTries();
    updateTaskStatus("Waiting for verification")
    
    jQuery.post(form.attr("action"), serialized, null, "json")
    .done(function(data)
    {
        if ("status" in data && data["status"] == "ok" && "submissionId" in data)
        {
            submissionId = data['submissionId'];
            displayNewSubmission(data['submissionId']);
            waitForSubmission(data['submissionId']);
        }
        else if ("status" in data && data['status'] == "error")
        {
            displayTaskStudentErrorAlert(data);
            updateTaskStatus("Internal error");
            unblurTaskForm();
        }
        else
        {
            displayTaskErrorAlert();
            updateTaskStatus("Internal error");
            unblurTaskForm();
        }
    })
    .fail(function()
    {
        displayTaskErrorAlert();
        updateTaskStatus("Internal error");
        unblurTaskForm();
    });
}

//Wait for a job to end
function waitForSubmission(submissionId)
{
    setTimeout(function()
    {
        var url = $('form#task').attr("action");
        jQuery.post(url, {"@action":"check","submissionId":submissionId}, null, "json")
        .done(function(data)
        {
            if("status" in data && data['status'] == "waiting")
            	waitForSubmission(submissionId);
            else if("status" in data && data['status'] == "done" && "result" in data)
            {
                if(data['result'] == "failed")
                {
                    displayTaskStudentErrorAlert(data);
                    updateSubmission(submissionId,data['result']);
                    updateTaskStatus("Wrong answer");
                    unblurTaskForm();
                }
                else if(data['result'] == "success")
                {
                    displayTaskStudentSuccessAlert();
                    updateSubmission(submissionId,data['result']);
                    updateTaskStatus("Suceeded");
                    unblurTaskForm();
                }
                else if(data['result'] == "timeout")
                {
                    displayTimeOutAlert();
                    updateSubmission(submissionId,data['result']);
                    updateTaskStatus("Wrong answer");
                    unblurTaskForm();
                }
                else if(data['result'] == "overflow")
                {
                    displayOverflowAlert();
                    updateSubmission(submissionId,data['result']);
                    updateTaskStatus("Wrong answer");
                    unblurTaskForm();
                }
                else // == "error"
                {
                    displayTaskErrorAlert(data);
                    updateSubmission(submissionId,data['result']);
                    updateTaskStatus("Wrong answer");
                    unblurTaskForm();
                }
            }
            else
            {
                displayTaskErrorAlert("");
                updateSubmission(submissionId,"error");
                updateTaskStatus("Wrong answer");
                unblurTaskForm();
            }
        })
        .fail(function()
        {
            displayTaskErrorAlert("");
            updateSubmission(submissionId,"error");
            updateTaskStatus("Wrong answer");
            unblurTaskForm();
        });
    }, 1000);
}

//Displays a loading alert in task form
function displayTaskLoadingAlert()
{
    $('#task_alert').html(getAlertCode("<b>Verifying your answers...</b>","info",false));
    $('html, body').animate(
    {
        scrollTop: $("#task_alert").offset().top-100
    }, 200);
}

//Displays a loading input alert in task form
function displayTaskInputLoadingAlert()
{
	$('#task_alert').html(getAlertCode("<b>Loading your submission...</b>","info",false));
    $('html, body').animate(
    {
        scrollTop: $("#task_alert").offset().top-100
    }, 200);
}

//Displays a loading input alert in task form
function displayTaskInputErrorAlert()
{
	$('#task_alert').html(getAlertCode("<b>Unable to load this submission</b>","danger",false));
    $('html, body').animate(
    {
        scrollTop: $("#task_alert").offset().top-100
    }, 200);
}

//Displays a loading input alert in task form
function displayTaskInputDoneAlert()
{
	$('#task_alert').html(getAlertCode("<b>Submission loaded</b>","success",false));
    $('html, body').animate(
    {
        scrollTop: $("#task_alert").offset().top-100
    }, 200);
}

//Displays an overflow error alert in task form
function displayOverflowAlert(content)
{
    msg = "<b>Your submission made an overflow.</b>";
    $('#task_alert').html(getAlertCode(msg,"warning",true));
    $('html, body').animate(
    {
        scrollTop: $("#task_alert").offset().top-100
    }, 200);
}

//Displays a timeout error alert in task form
function displayTimeOutAlert(content)
{
    msg = "<b>Your submission timed out.</b>";
    $('#task_alert').html(getAlertCode(msg,"warning",true));
    $('html, body').animate(
    {
        scrollTop: $("#task_alert").offset().top-100
    }, 200);
}

//Displays an internal error alert in task form
function displayTaskErrorAlert(content)
{
    msg = "<b>An internal error occured. Please retry later.</b>";
    if(content != "")
    {
        msg += "<br />Please send an email to the course administrator. Information : " + content.text;
    }
    
    $('#task_alert').html(getAlertCode(msg,"danger",true));
    $('html, body').animate(
    {
        scrollTop: $("#task_alert").offset().top-100
    }, 200);
}

//Displays a student error alert in task form
function displayTaskStudentErrorAlert(content)
{
	firstPos = -1;
	
	if("text" in content)
	{
        $('#task_alert').html(getAlertCode("<b>There are some errors in your answer:</b><br/>"+content.text,"danger",true));
		firstPos = $("#task_alert").offset().top;
	}
	
	if("problems" in content)
	{
		$(".task_alert_problem").each(function(key, elem)
		{
			problemId = elem.id.substr(11); //skip "task_alert."
			if(problemId in content.problems)
			{
				$(elem).html(getAlertCode("<b>There are some errors in your answer:</b><br/>"+content.problems[problemId],"danger",true));
				if(firstPos == -1 || firstPos > $(elem).offset().top)
					firstPos = $(elem).offset().top;
			}
		});
	}
	
	if(!("text" in content || "problems" in content))
	{
		$('#task_alert').html(getAlertCode("<b>There are some errors in your answer</b>","danger",true));
		firstPos = $("#task_alert").offset().top;
	}
	
    $('html, body').animate(
    {
        scrollTop: firstPos-100
    }, 200);
}

//Displays a student success alert in task form
function displayTaskStudentSuccessAlert(content)
{
    $('#task_alert').html(getAlertCode("<b>Your answer passed the tests!</b>","success",true));
    $('html, body').animate(
    {
        scrollTop: $("#task_alert").offset().top-100
    }, 200);
}

//Create an alert
//type is either alert, info, danger, warning
//dismissible is a boolean
function getAlertCode(content,type,dismissible)
{
    a = '<div class="alert fade in ';
    if(dismissible)
        a += 'alert-dismissible ';
    a += 'alert-'+type+'" role="alert">';
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
    jQuery.post(url, {"@action":"load_submission_input","submissionId":id}, null, "json")
    .done(function(data)
    {
    	if( "status" in data && data['status'] == "ok" && "input" in data)
    	{
    		unblurTaskForm();
    		loadInput(data['input']);
    		displayTaskInputDoneAlert();
    	}
    	else
    	{
    		displayTaskInputErrorAlert();
            unblurTaskForm();
    	}
    }).fail(function(data)
    {
    	displayTaskInputErrorAlert();
        unblurTaskForm();
    });
}

//Load data from input into the form inputs
function loadInput(input)
{
	$('form#task input').each(function()
	{
		if($(this).attr('type') == "hidden") //do not try to change @action
			return;
		
		id = $(this).attr('name')
		
		if(id in input)
		{
			if($(this).attr('type') != "checkbox" && $(this).attr('type') != "radio")
				$(this).prop('value',input[id]);
			else if($(this).attr('type') == "checkbox" && jQuery.isArray(input[id]) && $.inArray($(this).prop('value'),input[id]))
				$(this).prop('checked','checked');
			else if($(this).attr('type') == "radio" && $(this).prop('value') == input[id])
				$(this).prop('checked','checked');
			else if($(this).attr('type') == "checkbox" || $(this).attr('type') == "radio")
				$(this).prop('checked',false);
		}
		else if($(this).attr('type') == "checkbox" || $(this).attr('type') == "radio")
			$(this).prop('checked',false);
		else
			$(this).prop('value','');
	});
	
	$.each(codeEditors, function()
	{
		id = this.container.id;
		if(id in input)
			this.setValue(input[id]);
		else
			this.setValue("");
	})
}