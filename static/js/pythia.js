$(function()
{
	$('form#task').on('submit', function(){submitTask(); return false;});
});

//Contains all code editors
var codeEditors=[]

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
}
function unblurTaskForm()
{
	for (idx in codeEditors)
		codeEditors[idx].setReadOnly(false);
	$("form#task input, form#task button").removeAttr("disabled");
	$("form#task").removeClass('form-blur');
}

//Submits a task
function submitTask()
{
	var form = $('form#task');
	blurTaskForm();
	displayTaskLoadingAlert();
	
	setTimeout(function()
	{
		jQuery.post(form.attr("action"), form.serialize())
		.done(function()
		{
			
		})
		.fail(function()
		{
			displayTaskErrorAlert();
			unblurTaskForm();
		});
	},5000);
}

//Displays a loading alert in task form
function displayTaskLoadingAlert()
{
	$('#task_alert').html(getAlertCode("<b>Verifying your answers...</b>","info",false));
	$('html, body').animate(
	{
        scrollTop: $("#task_alert").offset().top-100
    }, 1000);
}

//Displays an internal error alert in task form
function displayTaskErrorAlert()
{
	$('#task_alert').html(getAlertCode("<b>An internal error occured. Please retry later.</b>","danger",true));
	$('html, body').animate(
	{
        scrollTop: $("#task_alert").offset().top-100
    }, 1000);
}

//Displays a student error alert in task form
function displayTaskStudentErrorAlert(content)
{
	$('#task_alert').html(getAlertCode("<b>There are some errors in your answer:</b><br/>"+content,"danger",true));
	$('html, body').animate(
	{
        scrollTop: $("#task_alert").offset().top-100
    }, 1000);
}

//Displays a student success alert in task form
function displayTaskStudentSuccessAlert(content)
{
	$('#task_alert').html(getAlertCode("<b>Your answer passed the tests!</b>","success",true));
	$('html, body').animate(
	{
        scrollTop: $("#task_alert").offset().top-100
    }, 1000);
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