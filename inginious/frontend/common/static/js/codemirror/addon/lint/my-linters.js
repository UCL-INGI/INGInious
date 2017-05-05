(
  function(mod) {
    if (typeof exports == "object" && typeof module == "object")
      mod(require("../../lib/codemirror"));
    else if (typeof define == "function" && define.amd)
      define(["../../lib/codemirror"], mod);
    else
      mod(CodeMirror);
  }
)
(
  function(CodeMirror) {
    "use strict";

    var clikeLanguageDict = {};
    clikeLanguageDict["text/x-java"] = "java";
    clikeLanguageDict["text/x-c++src"] = "cpp";
    clikeLanguageDict["text/x-csrc"] = "c";

    function getLanguageFromMode(mode) {
      if(mode.name == "clike")
        return clikeLanguageDict[mode.helperType];
      return mode.name;
    }

    function lint(code, options, editor){
      var language = getLanguageFromMode(editor.getMode());
      var errors_and_warnings = [];
      return errors_and_warnings;
    }

    CodeMirror.registerHelper("lint", "text/x-java", lint);
    CodeMirror.registerHelper("lint", "text/x-c++src", lint);
    CodeMirror.registerHelper("lint", "text/x-csrc", lint);
    CodeMirror.registerHelper("lint", "python", lint);
  }
);
