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