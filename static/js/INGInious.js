//
// Copyright (c) 2014 Université Catholique de Louvain.
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
    $('#submissions .submission').on('click', clickOnSubmission);
    
    $('.aceEditor').each(function(index,elem)
    {
    	registerCodeEditor($(elem).attr('id'),$(elem).attr('data-x-language'),$(elem).attr('data-x-lines'));
    });
    
    //Start affix only if there the height of the sidebar is less than the height of the content
    if($('#sidebar').height() < $('#content').height())
    	$('#sidebar').affix({offset:{top:83,bottom:1}});
    
    //Registration form, disable the password field when not needed
    if($('#register_courseid'))
    {
    	$('#register_courseid').change(function()
    	{
    		if($('#register_courseid option[value="'+$('#register_courseid').val()+'"]').attr('data-password') == 1)
    			$('#register_password').removeAttr('disabled')
    		else
    			$('#register_password').attr('disabled','disabled')
    	});
    }
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
            	if("debug" in data)
            		displayDebugInfo(data["debug"]);

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

//Displays debug info
function displayDebugInfo(info)
{
	displayDebugInfoRecur(info,$('#task_debug'));
}
function displayDebugInfoRecur(info,box)
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
		if( jQuery.isPlainObject(elem) )
			displayDebugInfoRecur(elem, content);
		else
			content.text(elem);
	});
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
    		loadOldFeedback(data);
    		loadInput(id, data['input']);
    		//displayTaskInputDoneAlert();
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
            displayTimeOutAlert();
        else if(data['result'] == "overflow")
            displayOverflowAlert();
        else // == "error"
            displayTaskErrorAlert(data);
    }
    else
        displayTaskErrorAlert("");
}

//Load data from input into the form inputs
function loadInput(submissionid, input)
{
	$('form#task input').each(function()
	{
		if($(this).attr('type') == "hidden") //do not try to change @action
			return;
		
		id = $(this).attr('name')
		
		if(id in input)
		{
			if($(this).attr('type') != "checkbox" && $(this).attr('type') != "radio" && $(this).attr('type') != "file")
				$(this).prop('value',input[id]);
			else if($(this).attr('type') == "checkbox" && jQuery.isArray(input[id]) && $.inArray(parseInt($(this).prop('value')),input[id]))
				$(this).prop('checked',true);
			else if($(this).attr('type') == "radio" && parseInt($(this).prop('value')) == input[id])
				$(this).prop('checked',true);
			else if($(this).attr('type') == "checkbox" || $(this).attr('type') == "radio")
				$(this).prop('checked',false);
			else if($(this).attr('type') == 'file')
			{
				//display the download button associated with this file
				$('#download-input-file-'+id).attr('href',$('form#task').attr("action")+"?submissionid="+submissionid+"&questionid="+id);
				$('#download-input-file-'+id).css('display','block');
			}
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
 * Redirect to the studio to create a new task
 */
function studio_create_new_task()
{
	if(!$('#new_task_id').val().match(/^[a-zA-Z0-9\._\-]+$/))
	{
		alert('Task id should only contain alphanumeric characters (in addition to ".", "_" and "-").');
		return;
	}
	window.location.href=window.location.href+"/edit/"+$('#new_task_id').val()
}

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
	
	$('form#edit_task_form').on('submit', function(){studio_submit(); return false;});
}

/**
 * Display a message indicating the status of a save action
 * @param type
 * @param message
 */
function studio_display_task_submit_message(content, type, dismissible)
{
	code = getAlertCode(content,type,dismissible)
	$('#task_edit_submit_status').html(code);
}

/**
 * Submit the form
 */
studio_submitting = false;
function studio_submit()
{
	if(studio_submitting)
		return;
	studio_submitting = true;
	
	studio_display_task_submit_message("Saving...", "info", false);
	
	$('form#edit_task_form .subproblem_order').each(function(index,elem)
	{
		$(elem).val(index);
	});
	
	$('form#edit_task_form').ajaxSubmit(
    {
    	dataType: 'json',
    	success: function(data)
        {
            if ("status" in data && data["status"] == "ok")
            {
            	studio_display_task_submit_message("Task saved.", "success", true);
            	$('#task_edit_submit_button').attr('disabled', false);
            	studio_submitting = false;
            }
            else if ("message" in data)
            {
            	studio_display_task_submit_message(data["message"], "danger", true);
            	$('#task_edit_submit_button').attr('disabled', false);
            	studio_submitting = false;
            }
            else
            {
            	studio_display_task_submit_message("An internal error occured", "danger", true);
            	$('#task_edit_submit_button').attr('disabled', false);
            	studio_submitting = false;
            }
        },
    	error: function()
        {
    		studio_display_task_submit_message("An internal error occured", "danger", true);
    		$('#task_edit_submit_button').attr('disabled', false);
    		studio_submitting = false;
        }
    });
	$('#task_edit_submit_button').attr('disabled', true);
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
	else
		return "#subproblem_custom";
	return "#subproblem_custom";
}

/**
 * Create new subproblem from the data in the form
 */
function studio_create_new_subproblem()
{
	if(!$('#new_subproblem_pid').val().match(/^[a-zA-Z0-9\._\-]+$/))
	{
		alert('Problem id should only contain alphanumeric characters (in addition to ".", "_" and "-").');
		return;
	}
	
	if($(studio_get_problem($('#new_subproblem_pid').val())).length != 0)
	{
		alert('This problem id is already used.');
		return;
	}
	
	studio_create_from_template('#'+$('#new_subproblem_type').val(),$('#new_subproblem_pid').val())
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
		$('#name-'+pid,well).val(problem["name"]);
	if("header" in problem)
		$('#header-'+pid,well).val(problem["header"]);
	if("headerIsHTML" in problem && problem["headerIsHTML"])
		$('#headerIsHTML-'+pid,well).attr('checked', true);
	
	if("language" in problem)
		$('#language-'+pid,well).val(problem["language"]);
	if("type" in problem)
		$('#type-'+pid,well).val(problem["type"]);
}

/**
 * Init a code_file template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_code_file(well, pid, problem)
{
	if("name" in problem)
		$('#name-'+pid,well).val(problem["name"]);
	if("header" in problem)
		$('#header-'+pid,well).val(problem["header"]);
	if("headerIsHTML" in problem && problem["headerIsHTML"])
		$('#headerIsHTML-'+pid,well).attr('checked', true);
	
	if("max_size" in problem)
		$('#maxsize-'+pid,well).val(problem["max_size"]);
	if("allowed_exts" in problem)
		$('#extensions-'+pid,well).val(problem["allowed_exts"].join());
}

/**
 * Init a custom template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_custom(well, pid, problem)
{
	if("name" in problem)
		$('#name-'+pid,well).val(problem["name"]);
	if("header" in problem)
		$('#header-'+pid,well).val(problem["header"]);
	if("headerIsHTML" in problem && problem["headerIsHTML"])
		$('#headerIsHTML-'+pid,well).attr('checked', true);
	
	delete problem["name"];
	delete problem["header"];
	$('#custom-'+pid,well).val(JSON.stringify(problem))
}

/**
 * Init a match template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_match(well, pid, problem)
{
	if("name" in problem)
		$('#name-'+pid,well).val(problem["name"]);
	if("header" in problem)
		$('#header-'+pid,well).val(problem["header"]);
	if("headerIsHTML" in problem && problem["headerIsHTML"])
		$('#headerIsHTML-'+pid,well).attr('checked', true);
	if("answer" in problem)
		$('#answer-'+pid,well).val(problem["answer"]);
}

/**
 * Init a multiple choice template
 * @param well: the DOM element containing the input fields
 * @param pid
 * @param problem
 */
function studio_init_template_multiple_choice(well, pid, problem)
{
	if("name" in problem)
		$('#name-'+pid,well).val(problem["name"]);
	if("header" in problem)
		$('#header-'+pid,well).val(problem["header"]);
	if("headerIsHTML" in problem && problem["headerIsHTML"])
		$('#headerIsHTML-'+pid,well).attr('checked', true);
	if("limit" in problem)
		$('#limit-'+pid,well).val(problem["limit"]);
	else
		$('#limit-'+pid,well).val(0);
	if("multiple" in problem && problem["multiple"])
		$('#multiple-'+pid,well).attr('checked', true);
	if("centralize" in problem && problem["centralize"])
		$('#centralize-'+pid,well).attr('checked', true);
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
	well = $(studio_get_problem(pid));
	
	index = 0;
	while($('#choice-'+index+'-'+pid).length != 0)
		index++;
	
	row = $("#subproblem_multiple_choice_choice").html()
	new_row_content = row.replace(/PID/g,pid).replace(/CHOICE/g,index);
	new_row = $("<tr></tr>").attr('id','choice-'+index+'-'+pid).html(new_row_content);
	$("#add-choices-"+pid,well).before(new_row);
	
	if("text" in choice_data)
		$(".subproblem_multiple_choice_text", new_row).val(choice_data["text"]);
	if("textIsHTML" in choice_data && choice_data["textIsHTML"] == true)
		$(".subproblem_multiple_choice_html", new_row).attr('checked', true)
	if("valid" in choice_data && choice_data["valid"] == true)
		$(".subproblem_multiple_choice_valid", new_row).attr('checked', true)
}

/**
 * Delete a multiple choice answer
 * @param pid
 * @param choice
 */
function studio_delete_choice(pid,choice)
{
	$('#choice-'+choice+'-'+pid).detach();
}

/**
 * Move subproblem up
 * @param pid
 */
function studio_subproblem_up(pid)
{
	well = $(studio_get_problem(pid));
	prev = well.prev(".well.row");
	if(prev.length)
		well.detach().insertBefore(prev);
}

/**
 * Move subproblem down
 * @param pid
 */
function studio_subproblem_down(pid)
{
	well = $(studio_get_problem(pid));
	next = well.next(".well.row");
	if(next.length)
		well.detach().insertAfter(next);
}

/**
 * Delete subproblem
 * @param pid
 */
function studio_subproblem_delete(pid)
{
	well = $(studio_get_problem(pid));
	if(!confirm("Are you sure that you want to delete this subproblem?"))
		return;
	well.detach();
}
