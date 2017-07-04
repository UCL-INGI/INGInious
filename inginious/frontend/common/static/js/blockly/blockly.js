/**
 * @fileoverview This file contains the functions to handle a
 * blockly task inside an INGInious generated page.
 * It links all the HTML parts to their actions.
 * @author Florian Thuin (@fthuin)
 */

/**
 * Link the HTML to jQuery objects and initializes a blockly task
 * given the information from INGInious.
 * @constructor
 * @param options: options for the workspace (warning: if toolbox is included, it will be overwritted)
 * @param toolbox: the toolbox XML (usually as a string)
 * @param workspaceBlocks: a XML string of the blocks you want to appear when the workspace is initliazed
 */
BlocklyTask = function(options, toolbox, workspaceBlocks) {
    this.blocklyButtonsRow = $("#blocklyButtonsRow"); // the row of buttons above the workspace
    this.blocklyButtons = $("#blocklyButtons"); // a set of blockly buttons
    this.blocklyBlocksText = $("#blocklyBlocksText");
    this.playButton = $("#playButton"); // start a local execution of the code
    this.stopButton = $("#stopButton"); // stop a local execution of the code
    this.resetButton = $("#resetButton"); // reset the task
    this.blockModeButton = $("#blockModeButtons"); // button to show only the workspace
    this.splitModeButton = $("#splitModeButtons"); // button to show workspace + code
    this.textModeButton = $("#textModeButtons"); // button to show only the code
    this.blocksLimitText = $("#blocksLimitText"); // text to display the block limit
    this.blocksLimitNumber = $("#blocksLimitNumber"); // text to display the remaining amount of blocks
    this.blocklyApp = $("#blocklyApp");
    this.blocklyAppLeft = $("#blocklyAppLeft");
    this.blocklyAppWorkspace = $("#blocklyAppWorkspace");
    this.blocklyDiv = $("#blocklyDiv");
    this.blocklyAppEditor = $("#blocklyAppEditor");
    this.codeArea = $("#codeArea");
    this.blocklyAppRight = $("#blocklyAppRight");
    this.visualization = $("#visualization");
    this.blocklySvgZone = $("#blocklySvgZone");
    this.blocklyModal = $("#blocklyModal");
    this.blocklyButtonsModal = $("#blocklyButtonsModal");
    this.blocklyAppModal = $("#blocklyAppModal");
    this.blocklyAppModalLeft = $("#blocklyAppModalLeft");
    this.blocklyAppModalRight = $("#blocklyAppModalRight");
    this.blocklyXmlArea = $("#blocklyXmlArea");
    this.blocklyInterpreterAlert = $("#blocklyInterpreterAlert");
    this.blocklyModalBody = $("#blocklyModalBody");

    this.options = options;
    this.options.toolbox = toolbox;

    this.display();

    this.editor = registerCodeEditor(this.codeArea[0], 'python', 10);
    this.editor.setOption("readOnly", true);

    this.workspace = this.injectWorkspace(this.blocklyDiv[0], this.options, workspaceBlocks);

    var self = this;
    this.workspace.addChangeListener(self.onWorkspaceChange(self));

    this.addButtonsListeners();
    this.addModalListeners();

    window.BlocklyLoopTrap = 1000;
    Blockly.JavaScript.INFINITE_LOOP_TRAP = 'if(--window.BlocklyLoopTrap == 0) throw "Infinite loop.";\n';

    this.interpreter = new BlocklyTaskInterpreter(this);
};

/**
 * Change the display whether there is a viual part of the problem or not.
 * Display the limit of blocks if it exists.
 */
BlocklyTask.prototype.display = function() {
    /* Set classes to display the visualization or not,
     * depending on the options given in the task.
     */
    if ("visual" in this.options) {
        this.blocklyAppLeft.addClass("col-xs-10");
        this.blocklyAppRight.addClass("class-xs-2");
        this.blocklyAppModalLeft.addClass("col-xs-9");
        this.blocklyAppModalRight.addClass("col-xs-3");
        if ("position" in this.options.visual && this.options.visual.position == "left") {
            this.blocklyAppRight.parent().prepend(this.blocklyAppRight.detach());
            this.blocklyAppModalRight.parent().prepend(this.blocklyAppModalRight.detach());
        }
    } else {
        this.blocklyAppLeft.addClass("col-xs-12");
        this.blocklyAppRight.hide();
        this.blocklyAppModalLeft.addClass("col-xs-12");
        this.blocklyAppModalRight.hide();
    }
    /* Show the limit of blocks that can be dragged in the workspace
     * or do not show if there is no limit.
     */
    if ("maxBlocks" in this.options && this.options.maxBlocks && this.options.maxBlocks !== Infinity && this.options.maxBlocks !== 'Infinity') {
        this.blocksLimitNumber.text(this.options.maxBlocks);
    } else {
        this.blocksLimitText.hide();
        this.options.maxBlocks = Infinity;
    }
};

/**
 * @param self: The blockly task itself (JavaScript closure)
 * @return a function that updates the remaining number of blocks
 */
BlocklyTask.prototype.updateBlocksNumber = function(self) {
    return function() {
        self.blocksLimitNumber.html(self.options.maxBlocks - self.workspace.getAllBlocks().length);
    };
};

/**
 * Injects a workspace in the blocklyDiv given the options and insert
 * the workspaceBlocks inside it.
 * @param blocklyDiv: HTML element where the workspace will be injected
 * @param options: options for the workspace (must contain the toolbox)
 * @param workspaceBlocks: blocks to put in the workspace at the beginning
 */
BlocklyTask.prototype.injectWorkspace = function(blocklyDiv, options, workspaceBlocks) {
    var workspace = Blockly.inject(blocklyDiv, options);
    var xml = Blockly.Xml.textToDom(blocklyWorkspaceBlocks);
    Blockly.Xml.domToWorkspace(xml, workspace);
    workspace.cleanUp();
    return workspace;
};

/**
 * Add listeners to all buttons in the task.
 */
BlocklyTask.prototype.addButtonsListeners = function() {
    var self = this;
    this.playButton.on('click.simple', function() {
        self.playButton.hide();
        self.stopButton.show();
        self.executeCode();
    });

    this.stopButton.on('click.simple', function() {
        self.stopButton.hide();
        self.resetButton.show();
        self.stopCodeExecution();
    });

    this.resetButton.on('click.simple', function() {
        self.resetButton.hide();
        self.playButton.show();
        if (typeof Maze !== "undefined" && typeof Maze.reset !== "undefined") {
            Maze.reset(false);
        }
    });
    /* Link mode to their actions */
    this.blockModeButton.on('click.simple', function() {
        self.splitModeButton.removeClass("active");
        self.textModeButton.removeClass("active");
        $(this).addClass("active");
        self.onWorkspaceMode();
    });
    this.splitModeButton.on('click.simple', function() {
        self.blockModeButton.removeClass("active");
        self.textModeButton.removeClass("active");
        $(this).addClass("active");
        self.onSplitMode();
    });
    this.textModeButton.on('click.simple', function() {
        self.blockModeButton.removeClass("active");
        self.splitModeButton.removeClass("active");
        $(this).addClass("active");
        self.onTextMode();
    });
};

/**
 * Unlink all buttons from the actions linked by addButtonsListeners()
 */
BlocklyTask.prototype.removeButtonsListeners = function() {
    this.playButton.off('click.simple');
    this.stopButton.off('click.simple');
    this.resetButton.off('click.simple');
    this.blockModeButton.off('click.simple');
    this.splitModeButton.off('click.simple');
    this.textModeButton.off('click.simple');
};

/**
 * Link the modal open and close event to actions
 */
BlocklyTask.prototype.addModalListeners = function () {
    var self = this;
    this.blocklyModal.on('shown.bs.modal', self.onModalOpen(self));
    this.blocklyModal.on('hidden.bs.modal', self.onModalClose(self));
};

/**
 * Unlink the modal open/close events from the actions set in addModalListeners
 */
BlocklyTask.prototype.removeModalListeners = function () {
    this.blocklyModal.off('shown.bs.modal');
    this.blocklyModal.off('hidden.bs.modal');
};

/**
 * Execute the code in the browser
 */
BlocklyTask.prototype.executeCode = function() {
    this.interpreter.start();
};

/**
 * Stop the current execution of the code in the browser
 */
BlocklyTask.prototype.stopCodeExecution = function() {
    this.interpreter.stop();
};

/**
 * Update the code that will be
 * - shown aside the workspace
 * - sent to INGInious
 * Should be called everytime the code generated by blocks might change
 */
BlocklyTask.prototype.updateCodeArea = function(self) {
    return function() {
        /* Insert the translated code in the textarea from workspace */
        var code = Blockly.Python.workspaceToCode(self.workspace);
        self.codeArea.val(code.replace("\r", ""));
        self.editor.setValue(self.codeArea.val());
        self.editor.refresh();
    };
};

/**
 * Update the XML area where the XML of the blocks is stored.
 * Should be called everytime the blocks on the workspace are changed.
 */
BlocklyTask.prototype.updateXmlArea = function(self) {
    return function() {
        /* Insert the XML in the textarea from workspace ws */
        var xml = Blockly.Xml.domToText(Blockly.Xml.workspaceToDom(self.workspace));
        self.blocklyXmlArea.val(xml);
    };
};

BlocklyTask.prototype.onWorkspaceChange = function(self) {
    return function() {
        self.workspace.addChangeListener(self.updateCodeArea(self));
        self.workspace.addChangeListener(self.updateXmlArea(self));
        self.workspace.addChangeListener(self.updateBlocksNumber(self));
    };
};

/**
 * @return a function that should be called when the fullscreen modal for
 * a blockly task is opened.
 */
BlocklyTask.prototype.onModalOpen = function(self) {
    return function() {
        // FIXME Next line is a fix, please monitor https://github.com/google/blockly/issues/56
        $(document).off('focusin.modal');

        self.removeButtonsListeners();

        self.blocklyAppModalLeft.append(self.blocklyAppWorkspace.detach());
        self.blocklyAppModalLeft.append(self.blocklyAppEditor.detach());
        self.blocklyButtonsModal.prepend(self.blocklyButtons.detach());
        self.blocklyModalBody.prepend(self.blocklyInterpreterAlert.detach());
        self.blocklyButtonsModal.append(self.blocklyBlocksText.detach());
        self.blocklyAppModalRight.append(self.visualization.detach());

        self.addButtonsListeners();

        Blockly.svgResize(self.workspace);
        self.workspace.render();
    };
};

/**
 * @param self: the blockly task itself (JavaScript closure)
 * @return a function that can be called when the modal is closed
 */
BlocklyTask.prototype.onModalClose = function(self) {
    return function() {
        self.removeButtonsListeners();

        self.blocklyAppLeft.append(self.blocklyAppWorkspace.detach());
        self.blocklyAppLeft.append(self.blocklyAppEditor.detach());
        self.blocklyButtonsRow.prepend(self.blocklyButtons.detach());
        self.blocklyButtonsRow.append(self.blocklyBlocksText.detach());
        self.blocklyAppRight.append(self.visualization.detach());
        self.blocklyButtonsRow.before(self.blocklyInterpreterAlert.detach());

        self.addButtonsListeners();

        var xml = Blockly.Xml.textToDom(self.blocklyXmlArea.val() || "");
        if (xml !== "") {
            self.workspace.clear();
            Blockly.Xml.domToWorkspace(xml, self.workspace);
        }

        Blockly.svgResize(self.workspace);
        self.workspace.render();
    };
};

/**
 * Shows only the blockly workspace (should be the default behavior)
 */
BlocklyTask.prototype.onWorkspaceMode = function() {
    this.blocklyAppWorkspace.removeClass();
    this.blocklyAppWorkspace.addClass("col-xs-12");
    this.blocklyAppWorkspace.show();
    this.blocklyAppEditor.removeClass();
    this.blocklyAppEditor.hide();
    Blockly.svgResize(this.workspace);
    this.workspace.render();
};

/**
 * Split the workspace in two: half blocks and half text.
 * Text is not editable.
 */
BlocklyTask.prototype.onSplitMode = function() {
    this.blocklyAppWorkspace.removeClass();
    this.blocklyAppWorkspace.addClass("col-xs-6");
    this.blocklyAppWorkspace.show();
    this.blocklyAppEditor.removeClass();
    this.blocklyAppEditor.addClass("col-xs-6");
    this.blocklyAppEditor.show();
    if (this.editor.getValue() === "") {
        this.editor.setValue("\n\n");
    }
    this.editor.refresh();
    Blockly.svgResize(this.workspace);
    this.workspace.render();
};

/**
 * Show code as text (hide the workspace).
 * Text is not editable.
 */
BlocklyTask.prototype.onTextMode = function() {
    this.blocklyAppWorkspace.removeClass();
    this.blocklyAppWorkspace.hide();
    this.blocklyAppEditor.removeClass();
    this.blocklyAppEditor.addClass("col-xs-12");
    this.blocklyAppEditor.show();
    if (this.editor.getValue() === "") {
        this.editor.setValue("\n\n");
    }
    this.editor.refresh();
};

/**
 * @constructor
 * @param task: a BlocklyTask object
 */
var BlocklyTaskInterpreter = function(task) {
    this.task = task;
    this.workspace = this.task.workspace;
    this.highlightPause = false;
    this.interpreter = null;
    this.timeout = null;
};

BlocklyTaskInterpreter.prototype.init = function(self) {
    return function(interpreter, scope) {
        if (typeof initInterpreterApi !== "undefined") {
            initInterpreterApi(interpreter, scope);
        }

        // Add an API function for the alert() block.
        var wrapper = function(text) {
            text = text ? text.toString() : '';
            return interpreter.createPrimitive(alert(text));
        };
        interpreter.setProperty(scope, 'alert', interpreter.createNativeFunction(wrapper));

        // Add an API function for the prompt() block.
        wrapper = function(text) {
            text = text ? text.toString() : '';
            return interpreter.createPrimitive(prompt(text));
        };
        interpreter.setProperty(scope, 'prompt', interpreter.createNativeFunction(wrapper));

        // Add an API function for highlighting blocks.
        wrapper = function(id) {
            id = id ? id.toString() : '';
            return interpreter.createPrimitive(self.highlightBlock(id));
        };
        interpreter.setProperty(scope, 'highlightBlock', interpreter.createNativeFunction(wrapper));
    };
};

/**
 * Translate block into javascript and links this.interpreter to a new interpreter
 * of the code.
 */
BlocklyTaskInterpreter.prototype.parseCode = function() {
    // Generate JavaScript code and parse it.
    Blockly.JavaScript.STATEMENT_PREFIX = 'highlightBlock(%1);\n';
    Blockly.JavaScript.addReservedWords('highlightBlock');

    var code = Blockly.JavaScript.workspaceToCode(this.workspace);
    this.interpreter = new Interpreter(code, this.init(this));

    this.highlightPause = false;
    this.workspace.highlightBlock(null);
};

/**
 * Start the execution of the code produced by blocks in the workspace.
 */
BlocklyTaskInterpreter.prototype.start = function() {
    this.parseCode();
    this.stepCode(this);
};

/**
 * Stop the code execution.
 */
BlocklyTaskInterpreter.prototype.stop = function() {
    if (this.timeout !== null) {
        window.clearTimeout(this.timeout);
    }
    this.workspace.highlightBlock(null);
};

/**
 * Execute a step of the code
 */
BlocklyTaskInterpreter.prototype.stepCode = function(self) {
    var ok;
    try {
        ok = self.interpreter.step();
        if (typeof animate !== "undefined") {
            animate();
        }
        return;
    } finally {
        if (!ok) {
            if (self.timeout !== null) {
                window.clearTimeout(self.timeout);
                self.timeout = null;
            }
            self.workspace.highlightBlock(null);
            self.task.stopButton.hide();
            self.task.resetButton.show();
        } else {
            self.timeout = window.setTimeout(function() {self.stepCode(self); }, 60);
        }
    }
};

/**
 * Highlight a block
 * @param id: id of the block to be highlighted
 */
BlocklyTaskInterpreter.prototype.highlightBlock = function(id) {
    this.workspace.highlightBlock(id);
    this.highlightPause = true;
};

/**
 * Show a message above the blockly workspace during 10 seconds.
 * @param message: the string to be displayed
 */
BlocklyTaskInterpreter.alert = function(message) {
    var blocklyInterpreterAlert = $("#blocklyInterpreterAlert");
    var blocklyInterpreterAlertText = $("#blocklyInterpreterAlertText");
    blocklyInterpreterAlertText.html(message);
    blocklyInterpreterAlert.alert();
    blocklyInterpreterAlert.fadeTo(10000, 500).slideUp(500, function() {
        blocklyInterpreterAlert.slideUp(500);
    });
};

var blocklyTask = new BlocklyTask(blocklyOptions, blocklyToolbox, blocklyWorkspaceBlocks);

/* We need to disable the full screen if the elements are not loaded (because
some elements might be missing on the full screen. )*/
$(document).ready(function() {
    $('#buttonFullscreen').attr("disabled", false);
});
