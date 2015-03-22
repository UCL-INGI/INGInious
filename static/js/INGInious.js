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
    
    $('.code-editor').each(function(index,elem)
    {
        registerCodeEditor(elem, $(elem).attr('data-x-language'), $(elem).attr('data-x-lines'));
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
function registerCodeEditor(textarea,lang,lines)
{
    mode = lang;
    if(lang != "plain")
    {
        //fix some languages
        switch (lang.toLowerCase())
        {
            //clike handles all c-like languages
            case "c": lang = "text/x-csrc"; mode = "clike"; break;
            case "cpp":
            case "c++": lang = "text/x-c++src"; mode = "clike"; break;
            case "java": lang = "text/x-java"; mode = "clike"; break;
            case "c#":
            case "csharp": lang = "text/x-csharp"; mode = "clike"; break;
            case "objective-c":
            case "objectivec":
            case "objc": lang = "text/x-objectivec"; mode = "clike"; break;
            case "scala": lang = "text/x-scala"; mode = "clike"; break;
            //python 2, python 3
            case "python":
            case "python2": lang = "text/x-python"; mode = "python"; break;
            case "python3": lang = {name: "python", version: 3}; mode = "python"; break;
        }
    }
    
    
    CodeMirror.modeURL = "/static/js/codemirror/mode/%N/%N.js";
    editor = CodeMirror.fromTextArea(textarea, {
        lineNumbers: true,
        mode: lang,
        foldGutter: true,
        styleActiveLine: true,
        matchBrackets: true,
        autoCloseBrackets: true,
        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
        indentUnit: 4,
        viewportMargin: Infinity
    });
    editor.on("change", function(cm) { cm.save(); });
    editor.setSize(null, (21*lines)+"px");
    CodeMirror.autoLoadMode(editor, mode);
    codeEditors.push(editor);
    return editor;
}

//Blur task form
function blurTaskForm()
{
    for (idx in codeEditors)
        codeEditors[idx].setOption("readOnly", true);
    $("form#task input, form#task button").attr("disabled","disabled");
    $("form#task").addClass('form-blur');
    loadingSomething = true;
}
function unblurTaskForm()
{
    for (idx in codeEditors)
        codeEditors[idx].setOption("readOnly", false);
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
function updateTaskStatus(newStatus, grade)
{
	currentStatus = $('#task_status').text().trim();
	currentGrade = parseFloat($('#task_grade').text().trim());
	
	if(currentGrade < grade)
		$('#task_grade').text(grade);
	if(currentStatus != "Succeeded")
		$('#task_status').text(newStatus);
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
		{
			$(this).removeClass('list-group-item-warning').addClass(nclass);
			grade = "0.0";
			if(result["grade"])
				grade = result["grade"];
			$(this).text($(this).text() + " - " + grade+"%");
		}
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
            else if ("status" in data && data['status'] == "error" && "text" in data)
            {
            	displayTaskErrorAlert(data);
                updateTaskStatus("Internal error", 0);
                unblurTaskForm();
            }
            else
            {
                displayTaskErrorAlert();
                updateTaskStatus("Internal error", 0);
                unblurTaskForm();
            }
        },
    	error: function()
        {
            displayTaskErrorAlert();
            updateTaskStatus("Internal error", 0);
            unblurTaskForm();
        }
    });
    
    blurTaskForm();
    resetAlerts();
    displayTaskLoadingAlert();
    updateTaskStatus("Waiting for verification", 0);
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
            else if("status" in data && "result" in data && "grade" in data)
            {
            	if("debug" in data)
            		displayDebugInfo(data["debug"]);

                if(data['result'] == "failed")
                {
                    displayTaskStudentErrorAlert(data);
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Wrong answer", data["grade"]);
                    unblurTaskForm();
                }
                else if(data['result'] == "success")
                {
                    displayTaskStudentSuccessAlert(data);
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Succeeded", data["grade"]);
                    unblurTaskForm();
                }
                else if(data['result'] == "timeout")
                {
                    displayTimeOutAlert();
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Wrong answer", data["grade"]);
                    unblurTaskForm();
                }
                else if(data['result'] == "overflow")
                {
                    displayOverflowAlert();
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Wrong answer", data["grade"]);
                    unblurTaskForm();
                }
                else // == "error"
                {
                    displayTaskErrorAlert(data);
                    updateSubmission(submissionid,data['result']);
                    updateTaskStatus("Wrong answer", data["grade"]);
                    unblurTaskForm();
                }
            }
            else
            {
                displayTaskErrorAlert("");
                updateSubmission(submissionid,"error");
                updateTaskStatus("Wrong answer", 0);
                unblurTaskForm();
            }
        })
        .fail(function()
        {
            displayTaskErrorAlert("");
            updateSubmission(submissionid,"error");
            updateTaskStatus("Wrong answer", 0);
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
			"<b>There are some errors in your answer. Your score is "+content["grade"]+"%</b>",
			"<b>There are some errors in your answer. Your score is "+content["grade"]+"%</b><br/>",
			"<b>There are some errors in your answer:</b><br/>",
			"danger",false);
}

//Displays a student success alert in task form
function displayTaskStudentSuccessAlert(content)
{
	displayTaskStudentAlertWithProblems(content,
			"<b>Your answer passed the tests! Your score is "+content["grade"]+"%</b>",
			"<b>Your answer passed the tests! Your score is "+content["grade"]+"%</b><br/>",
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
		name = this.getTextArea().name;
		if(name in input)
			this.setValue(input[name],-1);
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