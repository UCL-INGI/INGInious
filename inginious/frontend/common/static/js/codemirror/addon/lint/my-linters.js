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

    function lint(code){
      var found = [];
      found.push({
        from: CodeMirror.Pos(1-1, 0),
        to: CodeMirror.Pos(2-1, 0),
        severity: "warning",
        message: "Package name contains upper case characters"
      });

      found.push({
        from: CodeMirror.Pos(6-1, 0),
        to: CodeMirror.Pos(7-1, 0),
        severity: "warning",
        message: "Avoid unused imports such as 'java.util.Scanner'"
      });

      found.push({
        from: CodeMirror.Pos(15-1, 0),
        to: CodeMirror.Pos(16-1, 0),
        severity: "warning",
        message: "This class has too many methods, consider refactoring it."
      });

      return found;
    }

    CodeMirror.registerHelper("lint", "text/x-java", lint);
    CodeMirror.registerHelper("lint", "text/x-c++src", lint);
    CodeMirror.registerHelper("lint", "text/x-csrc", lint);
    CodeMirror.registerHelper("lint", "python", lint);
  }
);
