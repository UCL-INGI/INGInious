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
    {
    	//fix some languages
    	switch (lang.toLowerCase())
    	{
	    	case "c":
	    	case "cpp":
	    	case "c++":
	    		lang = "c_cpp"
	    		break;
    	}
        editor.getSession().setMode("ace/mode/"+lang);
    }
    editor.getSession().setTabSize(4);
    editor.setOptions({minLines: lines, maxLines: Infinity});
    
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
	if(currentStatus == "Succeeded")
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
    
    //Must be done before blurTaskForm as when a form is disabled, no input is sent by the plugin
    $('form#task').ajaxSubmit(
    {
    	dataType: 'json',
    	success: function(data)
        {
            if ("status" in data && data["status"] == "ok" && "submissionid" in data)
            {
            	incrementTries();
                submissionid = data['submissionid'];
                displayNewSubmission(data['submissionid']);
                waitForSubmission(data['submissionid']);
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
        }, 
    	error: function()
        {
            displayTaskErrorAlert();
            updateTaskStatus("Internal error");
            unblurTaskForm();
        }
    });
    
    blurTaskForm();
    resetAlerts();
    displayTaskLoadingAlert();
    updateTaskStatus("Waiting for verification");
}

//Wait for a job to end
function waitForSubmission(submissionid)
{
    setTimeout(function()
    {
        var url = $('form#task').attr("action");
        jQuery.post(url, {"@action":"check","submissionid":submissionid}, null, "json")
        .done(function(data)
        {
            if("status" in data && data['status'] == "waiting")
            	waitForSubmission(submissionid);
            else if("status" in data && "result" in data)
            {
                if(data['result'] == "failed")
                {
                    displayTaskStudentErrorAlert(data);
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Wrong answer");
                    unblurTaskForm();
                }
                else if(data['result'] == "success")
                {
                    displayTaskStudentSuccessAlert(data);
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Succeeded");
                    unblurTaskForm();
                }
                else if(data['result'] == "timeout")
                {
                    displayTimeOutAlert();
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Wrong answer");
                    unblurTaskForm();
                }
                else if(data['result'] == "overflow")
                {
                    displayOverflowAlert();
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Wrong answer");
                    unblurTaskForm();
                }
                else // == "error"
                {
                    displayTaskErrorAlert(data);
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Wrong answer");
                    unblurTaskForm();
                }
            }
            else
            {
                displayTaskErrorAlert("");
                updateSubmission(submissionid,"error");
                updateTaskStatus("Wrong answer");
                unblurTaskForm();
            }
        })
        .fail(function()
        {
            displayTaskErrorAlert("");
            updateSubmission(submissionid,"error");
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
function displayTaskStudentAlertWithProblems(content, topEmpty, topPrefix, prefix, type, alwaysShowTop)
{
	resetAlerts();
	
	firstPos = -1;
	
	if("text" in content && content.text != "")
	{
        $('#task_alert').html(getAlertCode(topPrefix+content.text,type,true));
		firstPos = $("#task_alert").offset().top;
	}
	
	if("problems" in content)
	{
		$(".task_alert_problem").each(function(key, elem)
		{
			problemid = elem.id.substr(11); //skip "task_alert."
			if(problemid in content.problems)
			{
				$(elem).html(getAlertCode(prefix+content.problems[problemid],type,true));
				if(firstPos == -1 || firstPos > $(elem).offset().top)
					firstPos = $(elem).offset().top;
			}
		});
	}
	
	if(firstPos == -1 || (alwaysShowTop && !("text" in content && content.text != "")))
	{
		$('#task_alert').html(getAlertCode(topEmpty,type,true));
		firstPos = $("#task_alert").offset().top;
	}
	
    $('html, body').animate(
    {
        scrollTop: firstPos-100
    }, 200);
}

//Displays a student error alert in task form
function displayTaskStudentErrorAlert(content)
{
	displayTaskStudentAlertWithProblems(content,
			"<b>There are some errors in your answer</b>",
			"<b>There are some errors in your answer:</b><br/>",
			"<b>There are some errors in your answer:</b><br/>",
			"danger",false);
}

//Displays a student success alert in task form
function displayTaskStudentSuccessAlert(content)
{
	displayTaskStudentAlertWithProblems(content,
			"<b>Your answer passed the tests!</b>",
			"<b>Your answer passed the tests!</b><br/>",
			"",
			"success",true);
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
    jQuery.post(url, {"@action":"load_submission_input","submissionid":id}, null, "json")
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

//Ask user if (s/)he wants to download all the submissions or only the last ones
function ask_to_download(link)
{
	box = '<div class="modal fade" id="downloadModal" tabindex="-1" role="dialog" aria-labelledby="downloadLabel" aria-hidden="true">'+
			'<div class="modal-dialog">'+
    			'<div class="modal-content">'+
      				'<div class="modal-header">'+
        				'<button type="button" class="close" data-dismiss="modal"><span aria-hidden="true">&times;</span><span class="sr-only">Close</span></button>'+
        				'<h4 class="modal-title" id="downloadLabel">Do you want to download every submissions?</h4>'+
      				'</div>'+
      				'<div class="modal-footer">'+
        				'<button type="button" class="btn btn-default" data-dismiss="modal">Cancel</button>'+
        				'<a href="'+link+'" type="button" class="btn btn-primary">Only the last valid submission</button>'+
        				'<a href="'+link+'&include_all=1" type="button" class="btn btn-info">All submissions</button>'+
      				'</div>'+
    			'</div>'+
			'</div>'+
		'</div>';
	$(document.body).append(box);
	$("#downloadModal").on('hidden.bs.modal', function () {
		$(this).remove();
	});
	$('#downloadModal').modal('show');
}


/****************\
|     Studio     |
\****************/
/**
 * Load the studio, creating blocks for existing subproblems
 */
function studio_load(data)
{
	jQuery.each(data, function(pid, problem)
	{
		template = studio_get_template_for_problem(problem);
		studio_create_from_template(template, pid);
		studio_init_template(template,pid,problem);
	});
}

/**
 * Get the right template for a given problem
 * @param problem
 */
function studio_get_template_for_problem(problem)
{
	if(problem["type"] == "code" && !problem["boxes"])
		return "#subproblem_code";
	else if(problem["type"] == "code")
		return "#subproblem_custom";
	else if(problem["type"] == "match")
		return "#subproblem_match";
	else if(problem["type"] == "multiple-choice")
		return "#subproblem_multiple_choice";
	else
		return "#subproblem_custom";
	return "#subproblem_custom";
}

/**
 * Create a new template and put it at the bottom of the problem list
 * @param template
 * @param pid
 */
function studio_create_from_template(template, pid)
{
	tpl = $(template).html().replace(/PID/g,pid);
	$('#new_subproblem').before(tpl);
}

/**
 * Get the real id of the DOM element containing the problem
 * @param pid
 */
function studio_get_problem(pid)
{
	return "#subproblem_well_"+pid;
}

/**
 * Init a template with data from an existing problem
 * @param template
 * @param pid
 * @param problem
 */
function studio_init_template(template,pid,problem)
{
	well = $(studio_get_problem(pid));
	switch(template)
	{
	case "#subproblem_code":
		studio_init_template_code(well, pid, problem);
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
	return;
}

/**
 * Init a code template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_code(well, pid, problem)
{
	if("name" in problem)
		$('#name-'+pid,well).val(problem["name"])
	if("header" in problem)
		$('#header-'+pid,well).val(problem["header"])
	if("language" in problem)
		$('#language-'+pid,well).val(problem["language"])
	
}

/**
 * Init a custom template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_custom(well, pid, problem)
{
}

/**
 * Init a match template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_match(well, pid, problem)
{
}

/**
 * Init a multiple choice template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_multiple_choice(well, pid, problem)
{
}


