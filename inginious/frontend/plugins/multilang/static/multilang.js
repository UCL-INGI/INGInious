function load_input_code_multiple_languages(submissionid, key, input)
{
    load_input_code(submissionid, key, input);
    setDropDownWithTheRightLanguage(key, input[key + "/language"]);
}

function setDropDownWithTheRightLanguage(key, language)
{
    var dropDown = document.getElementById(key + '/language');
    dropDown.value = language;
}

function studio_init_template_code_multiple_languages(well, pid, problem)
{
    if("type" in problem)
        $('#type-' + pid, well).val(problem["type"]);
    if("optional" in problem && problem["optional"])
        $('#optional-' + pid, well).attr('checked', true);

    if ("languages" in problem) {
        jQuery.each(problem["languages"], function(language, allowed) {
            if (allowed)
                $("#" + language + "-" + pid, well).attr("checked", true);
        });
    }
}