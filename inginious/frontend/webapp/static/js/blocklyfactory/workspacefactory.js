var WorkspaceFactory = function(controller) {
    Factory.call(this, controller);
    this.workspace = null;
};

WorkspaceFactory.prototype = new Factory();

WorkspaceFactory.prototype.setWorkspace = function(workspace) {
    this.workspace = workspace;
};

WorkspaceFactory.prototype.onWorkspaceChange = function(event) {
    var xml, xml_text;
    if (event.type == Blockly.Events.CREATE ||
        event.type == Blockly.Events.DELETE ||
        event.type == Blockly.Events.CHANGE ||
        (event.type == Blockly.Events.MOVE && event.oldParentId !== event.newParentId)) {
        this.controller.savePreloadWorkspace();
    }
    else if (event.type == Blockly.Events.UI && event.element === "selected") {
        if (Blockly.selected) {
            if (Blockly.selected.isDeletable()) {
                this.controller.view.undeletableButton.show();
                this.controller.view.deletableButton.hide();
            } else {
                this.controller.view.deletableButton.show();
                this.controller.view.undeletableButton.hide();
            }
            if (Blockly.selected.isMovable()) {
                this.controller.view.unmovableButton.show();
                this.controller.view.movableButton.hide();
            } else {
                this.controller.view.movableButton.show();
                this.controller.view.unmovableButton.hide();
            }
            if (Blockly.selected.disabled) {
                this.controller.view.enableButton.show();
                this.controller.view.disableButton.hide();
            } else {
                this.controller.view.disableButton.show();
                this.controller.view.enableButton.hide();
            }
            if (Blockly.selected.isEditable()) {
                this.controller.view.uneditableButton.show()
                this.controller.view.editableButton.hide()
            } else {
                this.controller.view.editableButton.show()
                this.controller.view.uneditableButton.hide()
            }
        } else {
            this.controller.view.deletableButton.hide();
            this.controller.view.undeletableButton.hide();
            this.controller.view.movableButton.hide();
            this.controller.view.unmovableButton.hide();
            this.controller.view.disableButton.hide();
            this.controller.view.enableButton.hide();
            this.controller.view.editableButton.hide();
            this.controller.view.uneditableButton.hide();
        }
    }
};

WorkspaceFactory.prototype.addWorkspaceListeners = function() {
    var self = this;
    this.workspace.addChangeListener(self.onWorkspaceChange.bind(self));
};
