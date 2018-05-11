// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE


function webLinter(language, code, callback, options, editor){
  var lintServerUrl = getLinterServerURL() + language;

  var serverCallback = function(response, status){
    var errors_and_warnings = JSON.parse(response);    
    callback(errors_and_warnings);
  }

  $.post(lintServerUrl, {code: code}, serverCallback);
}

function linterForLanguage(language) {
  return function(code, callback, options, editor){
    webLinter(language, code, callback, options, editor);    
  }
}

(function (mod) {
  if (typeof exports == "object" && typeof module == "object") // CommonJS
    mod(require("../../lib/codemirror"));
  else if (typeof define == "function" && define.amd) // AMD
    define(["../../lib/codemirror"], mod);
  else // Plain browser env
    mod(CodeMirror);
})(function (CodeMirror) {
  "use strict";

  CodeMirror.registerHelper("lint", "python", linterForLanguage("python"));
  CodeMirror.registerHelper("lint", "text/x-java", linterForLanguage("java"));
  CodeMirror.registerHelper("lint", "text/x-c++src", linterForLanguage("cpp"));
  CodeMirror.registerHelper("lint", "text/x-csrc", linterForLanguage("c"));
});
