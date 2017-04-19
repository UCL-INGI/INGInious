var ToolboxFactory = function(controller) {
    Factory.call(this, controller);
    this.workspace = null;
};

ToolboxFactory.prototype = new Factory();

ToolboxFactory.prototype.setWorkspace = function(workspace) {
    this.workspace = workspace;
    var selectedCategory = this.controller.getSelectedCategory();
    if (selectedCategory !== null) {
        this.loadCategoryInWorkspace(selectedCategory);
    }
};

ToolboxFactory.prototype.onWorkspaceChange = function(event) {
    if (event.type == Blockly.Events.CREATE ||
        event.type == Blockly.Events.DELETE ||
        event.type == Blockly.Events.CHANGE) {
        var xml = Blockly.Xml.workspaceToDom(this.workspace);
        var xml_text = Blockly.Xml.domToPrettyText(xml);
        var selectedCategory = this.controller.getSelectedCategory();
        if (selectedCategory === null) {
            this.controller.setToolboxXml(xml_text);
        } else {
            this.controller.setToolboxCategoryXml(selectedCategory, xml_text);
        }
    }
};

ToolboxFactory.prototype.loadCategoryInWorkspace = function(categoryName) {
    var categoryXml = this.controller.getToolboxCategoryXml(categoryName);
    var dom = Blockly.Xml.textToDom(categoryXml);
    this.workspace.clear();
    Blockly.Xml.domToWorkspace(dom, this.workspace);
    this.workspace.cleanUp();
};

ToolboxFactory.prototype.addWorkspaceListeners = function() {
    var self = this;
    this.workspace.addChangeListener(self.onWorkspaceChange.bind(self));
};
