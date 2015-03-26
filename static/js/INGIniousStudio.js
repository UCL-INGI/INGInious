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
	window.location.href=window.location.href+"/../edit/"+$('#new_task_id').val()
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
		success: function(data)
		{
			$("#tab_files").html(data);
		},
		method: method,
		data: data,
		url: location.pathname+"/files"
	});
}

/**
 * Delete a file related to a task
 */
function studio_task_file_delete(path)
{
	studio_update_file_tabs({"action": "delete", "path":path});
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
            	$('.task_edit_submit_button').attr('disabled', false);
            	studio_submitting = false;
            }
            else if ("message" in data)
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
    	error: function()
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
	
	//Default for every problem types
	if("name" in problem)
		$('#name-'+pid,well).val(problem["name"]);
	header_editor = registerCodeEditor($('#header-'+pid)[0], 'rst', 10);
	if("header" in problem)
		header_editor.setValue(problem["header"]);
	if("headerIsHTML" in problem && problem["headerIsHTML"])
		$('#headerIsHTML-'+pid,well).attr('checked', true);
	
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
	registerCodeEditor($('#custom-'+pid)[0], 'yaml', 10).setValue(problem["custom"]);
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

/**
 * Show the feedback for an old submission
 */
function studio_get_feedback(sid)
{
	if(loadingSomething)
		return;
	loadingSomething = true;
    $('#modal_feedback_content').text('Loading...');
    $('#modal_feedback').modal('show');
    
    jQuery.getJSON(document.location.pathname+'/'+sid)
    .done(function(data)
    {
    	if(data['status'] == "ok")
    	{
    		output = "<h1>Result</h1>";
    		output += data["data"]["result"] + " - " + data["data"]["grade"] + "%";
    		output += "<hr/><h1>Feedback - top</h1>";
    		output += data["data"]["text"];
    		$.each(data["data"]["problems"],function(index, elem)
    		{
    			output += "<hr/><h1>Feedback - subproblem "+index+"</h1>";
    			output += elem;
    		});
    		output += "<hr/><h1>Debug</h1>";
    		output += "<div id='modal_feedback_debug'></div>";
    		
    		$('#modal_feedback_content').html(output);
    		displayDebugInfoRecur(data["data"],$('#modal_feedback_debug'));
    	}
    	else
    	{
    		$('#modal_feedback_content').text('An error occured while retrieving the submission');
    	}
    	loadingSomething = false;
    }).fail(function(data)
    {
    	$('#modal_feedback_content').text('An error occured while retrieving the submission');
        loadingSomething = false;
    });
}