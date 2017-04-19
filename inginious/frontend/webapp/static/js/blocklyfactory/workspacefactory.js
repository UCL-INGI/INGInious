var WorkspaceFactory = function(controller) {
    Factory.call(this, controller);
    this.workspace = null;
};

WorkspaceFactory.prototype = new Factory();

WorkspaceFactory.prototype.setWorkspace = function(workspace) {
    this.workspace = workspace;
};

WorkspaceFactory.prototype.onWorkspaceChange = function(event) {
    if (event.type == Blockly.Events.CREATE ||
        event.type == Blockly.Events.DELETE ||
        event.type == Blockly.Events.CHANGE) {
        var xml = Blockly.Xml.workspaceToDom(this.workspace);
        var xml_text = Blockly.Xml.domToPrettyText(xml);
        this.controller.setWorkspaceXml(xml_text);
    }
};

WorkspaceFactory.prototype.addWorkspaceListeners = function() {
    var self = this;
    this.workspace.addChangeListener(self.onWorkspaceChange.bind(self));
};
