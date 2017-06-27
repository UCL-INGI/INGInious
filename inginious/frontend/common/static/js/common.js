//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
"use strict";

function init_common()
{
    //Init CodeMirror
    colorizeStaticCode();
    $('.code-editor').each(function(index, boxMultilineTextArea)
    {
        var editorLines = $(boxMultilineTextArea).attr('data-x-lines');
        var language = $(boxMultilineTextArea).attr('data-x-language');

        var shouldGetLanguageFromDropdown = (language == "plain");
        if(shouldGetLanguageFromDropdown){
            var problemId = $(boxMultilineTextArea).attr("name");
            language = getLanguageForProblemId(problemId);
        }

        registerCodeEditor(boxMultilineTextArea, language, editorLines);
    });

    //Fix a bug with codemirror and bootstrap tabs
    $('a[data-toggle="tab"]').on('shown.bs.tab', function(e)
    {
        var target = $(e.target).attr("href");
        $(target + ' .CodeMirror').each(function(i, el)
        {
            el.CodeMirror.refresh();
        });
    });

    //Enable tooltips
    $(function()
    {
        //Fix for button groups
        var all_needed_tooltips = $('[data-toggle="tooltip"]');
        var all_exceptions = $('.btn-group .btn[data-toggle="tooltip"], td[data-toggle="tooltip"]');

        var not_exceptions = all_needed_tooltips.not(all_exceptions);

        not_exceptions.tooltip();
        all_exceptions.tooltip({'container': 'body'});
    });
}

//Contains all code editors
var codeEditors = [];

//Run CodeMirror on static code
function colorizeStaticCode()
{
    $('.code.literal-block').each(function()
    {
        var classes = $(this).attr('class').split(' ');
        var mode = undefined;
        $.each(classes, function(idx, elem)
        {
            if(elem != "code" && elem != "literal-block")
            {
                var nmode = CodeMirror.findModeByName(elem);
                if(nmode != undefined)
                    mode = nmode;
            }
        });
        if(mode != undefined)
        {
            var elem = this;

            CodeMirror.requireMode(mode['mode'], function()
            {
                CodeMirror.colorize($(elem), mode["mime"]);
                $(elem).removeClass("cm-s-default").addClass("cm-s-inginious");
            });
        }
    });
}

//Register and init a code editor (ace)
function registerCodeEditor(textarea, lang, lines)
{
    var mode = CodeMirror.findModeByName(lang);
    if(mode == undefined)
        mode = {"mode": "plain", "mime": "text/plain"};

    var is_single = $(textarea).hasClass('single');

    var tabToSpaces = function(codeMirrorInstance) {
        var indentUnit = codeMirrorInstance.getOption("indentUnit");
        var spaces = Array(indentUnit + 1).join(" ");
        codeMirrorInstance.replaceSelection(spaces);
    }

    var fixTabs = function(codeMirrorInstance, changeObj){
        var indentUnit = codeMirrorInstance.getOption("indentUnit");
        var spaces = Array(indentUnit + 1).join(" ");
        changeObj.text = $.map(changeObj.text, function(line) {
            return line.replace(/\t/g, spaces);
        });
    }

    var editor = CodeMirror.fromTextArea(textarea, {
        lineNumbers:       true,
        mode:              mode["mime"],
        foldGutter:        true,
        styleActiveLine:   true,
        matchBrackets:     true,
        autoCloseBrackets: true,
        lineWrapping:      true,
        gutters:           ["CodeMirror-lint-markers", "CodeMirror-linenumbers", "CodeMirror-foldgutter"],
        indentUnit:        2,
        tabSize:           2,
        cursorHeight:      0.85,
        viewportMargin:    20,
        theme:             "inginious",
        lint:              true,
        extraKeys:         { "Ctrl-Space": "autocomplete", Tab: tabToSpaces }
    });

    if(is_single)
        $(editor.getWrapperElement()).addClass('single');

    editor.on("change", function(cm)
    {
        cm.save();
    });

    editor.on("beforeChange", fixTabs);

    var max_editor_height = "500";
    editor.setSize(null, max_editor_height + "px");

    if(mode["mode"] != "plain")
        CodeMirror.autoLoadMode(editor, mode["mode"]);

    codeEditors.push(editor);
    return editor;
}

// Apply parent function recursively
jQuery.fn.extend({
    rparent: function (number) {
        if(number==1)
            return $(this).parent();
        else
            return $(this).parent().rparent(number-1);
    }
});

/**
 * Select/deselect all the checkboxes of a panel
 * @param select: boolean indicating if we should select or deselect
 * @param panel_member: a child of the panel in which is the list
 */
function download_page_select(select, panel_member)
{
    panel_member = $(panel_member);
    while(!panel_member.hasClass('panel'))
        panel_member = panel_member.parent();
    $('input[type="checkbox"]', panel_member).prop('checked', select);
    $('input[type="checkbox"]', panel_member).trigger('change');
}

/**
 * Select/deselect all the checkboxes of the panel depending on a list of users and groups tutored.
 * @param panel_member: a child of the panel in which is the list
 * @param users: a list of usernames
 * @param groups: a list of group ids
 */
function download_page_select_tutor(panel_member, users, groups)
{
    panel_member = $(panel_member);
    while(!panel_member.hasClass('panel'))
        panel_member = panel_member.parent();
    $('input[name="aggregations"]', panel_member).each(function() { $(this).prop('checked', $.inArray($(this).val(),groups) != -1); });
    $('input[name="users"]', panel_member).each(function() { $(this).prop('checked', $.inArray($(this).val(), users) != -1); });
    $('input[type="checkbox"]', panel_member).trigger('change');
}

if (!String.prototype.startsWith) {
    String.prototype.startsWith = function(searchString, position) {
      return this.substr(position || 0, searchString.length) === searchString;
  };
}
