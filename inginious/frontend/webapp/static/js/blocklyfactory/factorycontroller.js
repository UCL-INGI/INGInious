var FactoryController = function(id, basicToolbox, workspaceBlocks, options, pid) {
    this.view = new FactoryView(this, id, pid);
    this.toolboxFactory = new ToolboxFactory(this);
    this.workspaceFactory = new WorkspaceFactory(this);
    this.basicToolbox = basicToolbox;
    this.workspaceBlocks = workspaceBlocks;
    this.options = options;
    this.preview = null;
    this.previewWorkspace = null;
    this.toolboxWorkspace = null;
    this.preloadWorkspace = null;
};

FactoryController.prototype.dispose = function() {
    this.previewWorkspace && this.previewWorkspace.dispose();
    this.toolboxWorkspace && this.toolboxWorkspace.dispose();
    this.preloadWorkspace && this.preloadWorkspace.dispose();
    this.view.dispose();
};

FactoryController.prototype.injectWorkspaces = function () {
    this.previewWorkspace = this.view.injectPreviewWorkspace(this.getToolboxXml(), this.getWorkspaceXml(), this.options);
    var toolbox_with_unknown = Toolbox.get_unknown_blocks(this.previewWorkspace);
    var basicToolbox = $(this.basicToolbox);
    basicToolbox.append(toolbox_with_unknown);
    this.basicToolbox = basicToolbox[0];
    this.toolboxWorkspace = this.view.injectToolboxWorkspace(this.basicToolbox);
    this.toolboxFactory.setWorkspace(this.toolboxWorkspace);
    this.toolboxFactory.addWorkspaceListeners();
    this.preloadWorkspace = this.view.injectPreloadWorkspace(this.basicToolbox, this.getWorkspaceXml());
    this.workspaceFactory.setWorkspace(this.preloadWorkspace);
    this.workspaceFactory.addWorkspaceListeners();
};

FactoryController.prototype.addToolboxChangeListeners = function() {
};

FactoryController.prototype.append = function(element) {
    this.div.append(element);
};

FactoryController.prototype.setPreview = function(preview) {
    this.preview = preview;
};

FactoryController.prototype.updatePreview = function(updateToolbox) {
    if (updateToolbox) {
        this.previewWorkspace.updateToolbox(this.getToolboxXml());
    }
    var dom = Blockly.Xml.textToDom(this.getWorkspaceXml());
    this.previewWorkspace.clear();
    Blockly.Events.disable();
    Blockly.Xml.domToWorkspace(dom, this.previewWorkspace);
    Blockly.Events.enable();
    this.previewWorkspace.cleanUp();
};

FactoryController.prototype.getToolboxXml = function() {
    return this.view.toolboxTextarea.getValue();
};

FactoryController.prototype.setToolboxXml = function(xml) {
    var cleanXml = this.cleanXml(xml);
    this.view.toolboxTextarea.setValue(cleanXml);
    this.updatePreview(true);
};

FactoryController.prototype.setToolboxCategoryXml = function(categoryName, xml) {
    var cleanXml = this.cleanXml(xml);
    cleanXml = $(cleanXml).html();
    var toolbox = $(this.getToolboxXml());
    var categories = toolbox.find('category');
    for (var i = 0, len = categories.length; i < len; i++) {
        var category = $(categories[i]);
        if (category.attr('name') == categoryName) {
            category.html(cleanXml);
            break;
        }
    }
    this.setToolboxXml(toolbox[0].outerHTML);
};

FactoryController.prototype.getToolboxCategoryXml = function(categoryName) {
    var xml = $("<xml>");
    var toolbox = $(this.getToolboxXml());
    var categories = toolbox.find('category');
    for (var i = 0, len = categories.length; i < len; i++) {
        var category = $(categories[i]);
        if (category.attr('name') === categoryName) {
            xml.html(category.html());
        }
    }
    return xml[0].outerHTML;
};

FactoryController.prototype.getWorkspaceXml = function() {
    return this.view.workspaceTextarea.getValue();
};

FactoryController.prototype.setWorkspaceXml = function(xml) {
    var cleanXml = this.cleanXml(xml);
    this.view.workspaceTextarea.setValue(cleanXml);
    this.updatePreview(false);
};

FactoryController.prototype.savePreloadWorkspace = function() {
    var xml, xml_text;
    xml = Blockly.Xml.workspaceToDom(this.preloadWorkspace, true);
    xml_text = Blockly.Xml.domToPrettyText(xml);
    this.setWorkspaceXml(xml_text);
};

FactoryController.prototype.cleanXml = function(xmlText) {
    var cleanChildren = function(elem) {
        var children = elem.children();
        for (var i = 0, len = children.length; i < len; i++) {
            var child = $(children[i]);
            child.removeAttr('id');
            child.removeAttr('x');
            child.removeAttr('y');
            cleanChildren(child);
        }
    };
    var xml = $(xmlText);
    cleanChildren(xml);
    return xml[0].outerHTML;
};

FactoryController.prototype.getToolboxCategories = function(toolbox_xml) {
    var toolbox = $(toolbox_xml);
    var categories = toolbox.find('category');
    var categoriesName = [];
    categories.each(function(ind, el) {
        categoriesName.push($(el).attr('name'));
    });
    return categoriesName;
};

FactoryController.prototype.getSelectedCategory = function () {
    return this.view.selectedCategory;
};

FactoryController.prototype.setCategoryColour = function(colour) {
    var categoryName = this.getSelectedCategory();
    var toolbox = $(this.getToolboxXml());
    var categories = toolbox.find('category');
    for (var i = 0, len = categories.length; i < len; i++) {
        var category = $(categories[i]);
        if (category.attr('name') == categoryName) {
            category.attr('colour', colour);
            break;
        }
    }
    this.setToolboxXml(toolbox[0].outerHTML);
};

FactoryController.prototype.changeCategoryName = function() {
    var selectedCategory = this.getSelectedCategory();

    var categoryName = prompt('Please enter the new category name:', selectedCategory);
    if (categoryName === null || categoryName === '') return;
    if (this.view.categoriesName.indexOf(categoryName) !== -1) {
        alert('Another category with name "' + categoryName + '" already exists.');
        return;
    }

    // Change name in view
    var index = this.view.categoriesName.indexOf(selectedCategory);
    this.view.categoriesName[index] = categoryName;
    this.view.changeCategoryName(selectedCategory, categoryName);

    // Change name in toolbox XML
    var toolbox = $(this.getToolboxXml());
    var categories = toolbox.find('category');
    for (var i = 0, len = categories.length; i < len; i++) {
        var category = $(categories[i]);
        if (category.attr('name') == selectedCategory) {
            category.attr('name', categoryName);
            break;
        }
    }
    this.setToolboxXml(toolbox[0].outerHTML);

    this.view.setSelectedCategory(categoryName);

};

FactoryController.prototype.createToolboxCategory = function() {
    var selectedCategory = this.getSelectedCategory();
    if (selectedCategory !== null) {
        var toolbox = $(this.getToolboxXml());
        var newCategory = $("<category>");
        newCategory.attr('name', selectedCategory);
        newCategory.attr('colour', 210);

        // Check if there are blocks at the root level
        var rootBlocks = toolbox.children('block');
        for (var i = 0, len = rootBlocks.length; i < len; i++) {
            newCategory.append($(rootBlocks[i]).detach());
        }

        toolbox.append(newCategory);
        this.setToolboxXml(toolbox[0]);

        // Set root blocks into the new category
        if (rootBlocks.length !== 0) {
            var xml = Blockly.Xml.workspaceToDom(this.toolboxWorkspace, true);
            var xmlText = Blockly.Xml.domToPrettyText(xml);
            var cleanXml = this.cleanXml(xmlText);
            this.setToolboxCategoryXml(selectedCategory, cleanXml);
        }

        this.toolboxFactory.loadCategoryInWorkspace(selectedCategory);
    }
};

FactoryController.prototype.removeCategory = function() {
    var selectedCategory = this.getSelectedCategory();
    if (selectedCategory !== null) {
        var toolbox = $(this.getToolboxXml());
        var categories = toolbox.find('category');
        for (var i = 0, len = categories.length; i < len; i++) {
            var category = $(categories[i]);
            if (category.attr('name') === selectedCategory) {
                category.remove();
                break;
            }
        }
        this.setToolboxXml(toolbox[0].outerHTML);

        var index = this.view.categoriesName.indexOf(selectedCategory);
        this.view.categoriesName.splice(index, 1);
        this.view.removeCategoryListItem(selectedCategory);

        if (this.view.categoriesName.length === 0) {
            this.view.setSelectedCategory(null);
            this.toolboxFactory.workspace.clear();
        } else {
            this.view.setSelectedCategory(this.view.categoriesName[0]);
            this.toolboxFactory.loadCategoryInWorkspace(this.view.categoriesName[0]);
        }
    }
};

FactoryController.prototype.moveUpCategory = function() {
    var selectedCategory = this.getSelectedCategory();
    var toolbox = $(this.getToolboxXml());
    var categories = toolbox.find('category');
    // We start at 1 because we cannot move up first category
    for (var i = 1, len = categories.length; i < len; i++) {
        var category = $(categories[i]);
        if (category.attr('name') == selectedCategory) {
            $(categories[i-1]).before(category.remove());
            break;
        }
    }
    this.setToolboxXml(toolbox[0].outerHTML);
};

FactoryController.prototype.moveDownCategory = function() {
    var selectedCategory = this.getSelectedCategory();
    var toolbox = $(this.getToolboxXml());
    var categories = toolbox.find('category');
    // We start at 1 because we cannot move up first category
    for (var i = 0, len = categories.length - 1; i < len; i++) {
        var category = $(categories[i]);
        if (category.attr('name') == selectedCategory) {
            $(categories[i+1]).after(category.remove());
            break;
        }
    }
    this.setToolboxXml(toolbox[0].outerHTML);
};
