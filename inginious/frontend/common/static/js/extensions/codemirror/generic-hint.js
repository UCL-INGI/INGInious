// CodeMirror, copyright (c) by Marijn Haverbeke and others
// Distributed under an MIT license: http://codemirror.net/LICENSE

(function (mod) {
  if (typeof exports == "object" && typeof module == "object") // CommonJS
    mod(require("../../lib/codemirror"));
  else if (typeof define == "function" && define.amd) // AMD
    define(["../../lib/codemirror"], mod);
  else // Plain browser env
    mod(CodeMirror);
})(function (CodeMirror) {
  var Pos = CodeMirror.Pos;

  function shouldIgnoreToken(token) {
    return token.type === null
           || token.type == "string"
           || token.type == "comment"
           || token.type == "operator"
           || token.type == "number";
  }

  function getShowableStringsFrom(tokenList) {
    var showableStrings = [];
    for (var i = 0; i < tokenList.length; i++) {
      if (!shouldIgnoreToken(tokenList[i]))
        showableStrings.push(tokenList[i].string);
    }
    return showableStrings;
  }

  function addWordsFromLine(lineNumber, words, editor) {
    var lineTokens = editor.getLineTokens(lineNumber);
    var showableStrings = getShowableStringsFrom(lineTokens);

    for (var i = 0; i < showableStrings.length; i++)
      words.push(showableStrings[i]);
  }

  function getWordsFromExistingCode(editor) {
    var lineCount = editor.lineCount();
    var words = [];

    for (var lineNumber = 0; lineNumber < lineCount; lineNumber++)
      addWordsFromLine(lineNumber, words, editor);
    
    return words;
  }

  function getKeywords(editor) {
    return editor.getHelper(editor.getCursor(), "hintWords");
  }

  function filterWords(acummulatorSet, words, prefix){
    for(var i = 0; i < words.length; i++){
      if(prefix == "" || words[i].toLowerCase().startsWith(prefix.toLowerCase()))
        acummulatorSet.add(words[i]);
    }
  }

  function genericHint(editor) {
    var cursor = editor.getCursor();
    var prefix = editor.getTokenAt(cursor).string.trim();
    var wordsSet = new Set();

    var wordsFromCode = getWordsFromExistingCode(editor);
    filterWords(wordsSet, wordsFromCode, prefix);

    var keywords = getKeywords(editor);
    filterWords(wordsSet, keywords, prefix);

    var selectedWords = Array.from(wordsSet).sort();

    return {
      list: selectedWords,
      from: Pos(cursor.line, editor.getTokenAt(cursor).start),
      to: Pos(cursor.line, editor.getTokenAt(cursor).end)
    };
  }
  
  CodeMirror.registerHelper("hint", "python", genericHint);
  CodeMirror.registerHelper("hint", "clike", genericHint);
  CodeMirror.registerHelper("hint", "ruby", genericHint);
});
