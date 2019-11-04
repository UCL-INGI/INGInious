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
var codeEditors = {};

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

    codeEditors[$(textarea).attr("name")] =  editor;
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

/**
 * Select/deselect all the checkboxes of a panel
 * @param select: boolean indicating if we should select or deselect
 * @param panel_member: a child of the panel in which is the list
 */
function download_page_select(select, panel_member)
{
    panel_member = $(panel_member);
    while(!panel_member.hasClass('card'))
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
    $('input[name="audiences"]', panel_member).each(function() { $(this).prop('checked', $.inArray($(this).val(),groups) != -1); });
    $('input[name="users"]', panel_member).each(function() { $(this).prop('checked', $.inArray($(this).val(), users) != -1); });
    $('input[type="checkbox"]', panel_member).trigger('change');
}