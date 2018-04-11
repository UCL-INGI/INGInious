var PythonTutor = (function () {
    function PythonTutor(problemId, language) {
        this.defaultVisualServer = getDefaultVisualServerURL();
        this.javaVisualServer = "https://cscircles.cemc.uwaterloo.ca/";

        this.problemId = problemId;
        this.code = codeEditors[problemId].getValue();

        if (language == "plain")
            language = getLanguageForProblemId(this.problemId);

        this.language = language;
        this.input = document.getElementById("custominput-" + this.problemId).value;
    }

    PythonTutor.prototype.visualize = function () {
        var iframe = this.createIFrameFromCode();
        this.showIFrameIntoModal(iframe);
    };

    PythonTutor.prototype.createIFrameFromCode = function () {
        var iframe = document.createElement('iframe');
        iframe.src = this.generateVisualizerUrl();
        iframe.height = "400px";
        iframe.width = "100%";
        iframe.frameborder = "0";
        return iframe;
    };

    PythonTutor.prototype.showIFrameIntoModal = function (iframe) {
        var modal = document.getElementById("modal-" + this.problemId);
        var modalBody = modal.getElementsByClassName("modal-body")[0];
        $(modalBody).empty();
        modalBody.innerHTML = "Plase wait while we excecute your code, this may take up to 10 seconds";
        modalBody.appendChild(iframe);
    };

    PythonTutor.prototype.generateVisualizerUrl = function () {
        if(this.language == "java")
            return this.generateJavaUrl();
        else
            return this.generateGenericUrl();
    };

    PythonTutor.prototype.generateJavaUrl = function () {
        var data = {
            "user_script": this.code,
            "options":{"showStringsAsValues":true,"showAllFields":false},
            "args":[],
            "stdin": this.input
        };

        return this.serverResource()
            + window.encodeURIComponent(JSON.stringify(data))
            + "&cumulative=false"
            + "&heapPrimitives=false"
            + "&drawParentPointers=false"
            + "&textReferences=false"
            + "&showOnlyOutputs=false"
            + "&py=3"
            + "&curInstr=0"
            + "&resizeContainer=true"
            + "&highlightLines=true"
            + "&rightStdout=true"
            + "&codeDivHeight=450"
            + "&codeDivWidth=500";
    };

    PythonTutor.prototype.generateGenericUrl = function () {
        var codeToURI = window.encodeURIComponent(this.code);
        var url = this.serverResource()
            + codeToURI
            + "&mode=edit"
            + "&py=" + this.languageURIName()
            + "&codeDivHeight=450"
            + "&codeDivWidth=500"
            + "&rawInputLstJSON=" + this.encodedInputArray();
        return url;
    };

    PythonTutor.prototype.serverResource = function () {
        if (this.language == "java")
            return this.javaVisualServer + "java_visualize/iframe-embed.html?faking_cpp=false#data=";
        return this.defaultVisualServer + "iframe-embed.html#code=";
    };

    PythonTutor.prototype.languageURIName = function () {
        if (this.language == "javascript")
            return "js";
        if (this.language == "python")
            return "2";
        return this.language;
    };

    PythonTutor.prototype.encodedInputArray = function() {
        var inputAsArray = this.input.split("\n");
        return window.encodeURIComponent(JSON.stringify(inputAsArray));
    };

    return PythonTutor;
}());

function visualizeCode(language, problemId){
    var pythonTutor = new PythonTutor(problemId, language);
    pythonTutor.visualize();
}