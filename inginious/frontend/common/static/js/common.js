//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
"use strict";

function init_common()
{
    //Init CodeMirror
    colorizeStaticCode();
    $('.code-editor').each(function(index, elem)
    {
        registerCodeEditor(elem, $(elem).attr('data-x-language'), $(elem).attr('data-x-lines'));
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
    CodeMirror.modeURL = "/static/common/js/codemirror/mode/%N/%N.js";
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
    CodeMirror.modeURL = "/static/common/js/codemirror/mode/%N/%N.js";
    var mode = CodeMirror.findModeByName(lang);
    if(mode == undefined)
        mode = {"mode": "plain", "mime": "text/plain"};

    var is_single = $(textarea).hasClass('single');

    var editor = CodeMirror.fromTextArea(textarea, {
        lineNumbers:       true,
        mode:              mode["mime"],
        foldGutter:        true,
        styleActiveLine:   true,
        matchBrackets:     true,
        autoCloseBrackets: true,
        lineWrapping:      true,
        gutters:           ["CodeMirror-linenumbers", "CodeMirror-foldgutter"],
        indentUnit:        4,
        viewportMargin:    Infinity,
        theme:             "inginious",
        lint:              function()
                           {
                               return []
                           }
    });

    if(is_single)
        $(editor.getWrapperElement()).addClass('single');

    editor.on("change", function(cm)
    {
        cm.save();
    });

    var min_editor_height = (21 * lines);
    editor.on("viewportChange", function(cm) { onEditorViewportChange(min_editor_height, cm); });
    editor.setSize(null, min_editor_height + "px");
    onEditorViewportChange(min_editor_height, editor); //immediately trigger a size update

    if(mode["mode"] != "plain")
        CodeMirror.autoLoadMode(editor, mode["mode"]);

    codeEditors.push(editor);
    return editor;
}

// Verify if the size of each code editor is sufficient
function onEditorViewportChange(min_editor_height, cm)
{
    if(cm.getScrollInfo()["height"] > min_editor_height)
        cm.setSize(null, "auto");
    else
        cm.setSize(null, min_editor_height + "px");
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