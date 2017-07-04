var FactoryView = function(controller, id, pid) {
    this.controller = controller;
    this.div = $('#' + id);
    this.div.addClass('col-xs-12');
    this.div.css('height', '60vh');
    this.factoryDiv = this.createColumn('Factory', 6);
    this.div.append(this.factoryDiv);
    this.middleDiv = this.createColumn('', 2);
    this.div.append(this.middleDiv);
    this.previewDiv = this.createColumn('Preview', 4);
    this.previewWorkspaceDiv = this.createWorkspaceDiv('previewWorkspace');
    this.previewDiv.append(this.previewWorkspaceDiv);
    this.toolboxWorkspaceDiv = this.createWorkspaceDiv('toolboxWorkspace');
    this.preloadWorkspaceDiv = this.createWorkspaceDiv('preloadWorkspace');
    this.div.append(this.previewDiv);
    this.tabList = BootstrapElement.tabList();
    this.factoryDiv.append(this.tabList);
    this.toolboxTab = BootstrapElement.tab('toolboxFactory', 'Toolbox');
    this.toolboxTab.addClass('active');
    this.workspaceTab = BootstrapElement.tab('workspaceFactory', 'Workspace');
    this.tabList.append(this.toolboxTab);
    this.tabList.append(this.workspaceTab);
    this.toolboxTextarea = $("#toolbox-" + pid).next('.CodeMirror')[0].CodeMirror;
    this.workspaceTextarea = $("#workspace-" + pid).next('.CodeMirror')[0].CodeMirror;

    /* Left part  */
    this.tabContent = BootstrapElement.tabContent();
    this.factoryDiv.append(this.tabContent);
    this.toolboxTabPane = BootstrapElement.tabPane('toolboxFactory');
    this.toolboxTabPane.addClass('fade');
    this.toolboxTabPane.addClass('active');
    this.toolboxTabPane.addClass('in');
    this.toolboxTabPane.append(this.toolboxWorkspaceDiv);
    this.workspaceTabPane = BootstrapElement.tabPane('workspaceFactory');
    this.workspaceTabPane.append(this.preloadWorkspaceDiv);
    this.tabContent.append(this.toolboxTabPane);
    this.tabContent.append(this.workspaceTabPane);

    /* Middle part */
    this.addButton = this.createAddButton();
    this.middleDiv.append(this.addButton);
    this.removeButton = this.createRemoveButton();
    this.middleDiv.append(this.removeButton);
    this.moveUpButton = this.createMoveUpButton();
    this.middleDiv.append(this.moveUpButton);
    this.moveDownButton = this.createMoveDownButton();
    this.middleDiv.append(this.moveDownButton);
    this.editCategoryButton = this.createEditCategoryButton();
    this.middleDiv.append(this.editCategoryButton);
    this.selectedCategory = null;
    this.categoriesName = this.controller.getToolboxCategories(this.toolboxTextarea.getValue());
    this.categoriesList = this.createCategoryList(this.categoriesName);
    if (this.categoriesName.length > 0) this.setSelectedCategory(this.categoriesName[0]);
    this.middleDiv.prepend(this.categoriesList);

    /* Blocks properties buttons */
    this.deletableButton = this.createMakeDeletableButton();
    this.middleDiv.append(this.deletableButton);
    this.undeletableButton = this.createMakeUndeletableButton();
    this.middleDiv.append(this.undeletableButton);
    this.movableButton = this.createMakeMovableButton();
    this.middleDiv.append(this.movableButton);
    this.unmovableButton = this.createMakeUnmovableButton();
    this.middleDiv.append(this.unmovableButton);
    this.enableButton = this.createMakeEnabledButton();
    this.middleDiv.append(this.enableButton);
    this.disableButton = this.createMakeDisabledButton();
    this.middleDiv.append(this.disableButton);
    this.editableButton = this.createMakeEditableButton();
    this.middleDiv.append(this.editableButton);
    this.uneditableButton = this.createMakeUneditableButton();
    this.middleDiv.append(this.uneditableButton);

    this.toolboxTab.on('shown.bs.tab', this.onToolboxTabClick.bind(this));
    this.workspaceTab.on('shown.bs.tab', this.onWorkspaceTabClick.bind(this));
};

FactoryView.NO_CATEGORY_MSG = 'You currently have no categories.';
FactoryView.EDIT_CATEGORY_MSG = 'Edit category';

FactoryView.prototype.dispose = function() {
    this.div && this.div.html('');
};

FactoryView.prototype.createColumn = function(name, size) {
    var div = BootstrapElement.column(size);

    var title = $("<h2>");
    title.html(name);
    div.append(title);

    return div;
};

FactoryView.prototype.createWorkspaceDiv = function(divId) {
    var div = $("<div>");
    div.attr('id', divId);
    div.css('min-height', '300px');
    div.height('100%');
    div.css('min-width', '300px');
    div.width('100%');
    return div;
};

FactoryView.prototype.injectPreviewWorkspace = function(toolbox, workspaceBlocks, options) {
    var workspaceOptions = $.extend({toolbox: toolbox}, options);
    var workspace = Blockly.inject(this.previewWorkspaceDiv[0], workspaceOptions);
    Blockly.Events.disable();
    Blockly.Xml.domToWorkspace(Blockly.Xml.textToDom(workspaceBlocks), workspace);
    Blockly.Events.enable();
    workspace.cleanUp();
    return workspace;
};

FactoryView.prototype.injectToolboxWorkspace = function(toolbox) {
    var workspace = Blockly.inject(this.toolboxWorkspaceDiv[0], {
        toolbox: toolbox,
        grid: {
            spacing: 20,
            length: 3,
            colour: '#ccc',
            snap: true
        },
        zoom: {
            controls: true,
            wheel: false,
            startScale: 1.0,
            maxScale: 3,
            minScale: 0.3,
            scaleSpeed: 1.2
        },
        trashcan: true
    });
    if (this.categoriesName.length === 0) {
        var dom = Blockly.Xml.textToDom(this.controller.getToolboxXml());
        Blockly.Events.disable();
        Blockly.Xml.domToWorkspace(dom, workspace);
        Blockly.Events.enable();
        workspace.cleanUp();
    }
    return workspace;
};

FactoryView.prototype.injectPreloadWorkspace = function(toolbox, workspaceBlocks) {
    var workspace = Blockly.inject(this.preloadWorkspaceDiv[0], {
        toolbox: toolbox,
        grid: {
            spacing: 20,
            length: 3,
            colour: '#ccc',
            snap: true
        },
        zoom: {
            controls: true,
            wheel: false,
            startScale: 1.0,
            maxScale: 3,
            minScale: 0.3,
            scaleSpeed: 1.2
        },
        trashcan: true
    });
    Blockly.Events.disable();
    Blockly.Xml.domToWorkspace(Blockly.Xml.textToDom(workspaceBlocks), workspace);
    Blockly.Events.enable();
    workspace.cleanUp();
    return workspace;
};

FactoryView.prototype.onToolboxTabClick = function() {
    this.addButton.show();
    this.removeButton.show();
    this.moveUpButton.show();
    this.moveDownButton.show();
    this.editCategoryButton.show();
    this.categoriesList.show();
    this.deletableButton.hide();
    this.undeletableButton.hide();
    this.movableButton.hide();
    this.unmovableButton.hide();
    this.enableButton.hide();
    this.disableButton.hide();
    this.editableButton.hide();
    this.uneditableButton.hide();
    Blockly.svgResize(this.controller.toolboxWorkspace);
    this.controller.toolboxWorkspace.render();
};

FactoryView.prototype.onWorkspaceTabClick = function() {
    this.addButton.hide();
    this.removeButton.hide();
    this.moveUpButton.hide();
    this.moveDownButton.hide();
    this.editCategoryButton.hide();
    this.categoriesList.hide();
    Blockly.svgResize(this.controller.preloadWorkspace);
    this.controller.preloadWorkspace.render();
};

FactoryView.prototype.createAddButton = function() {
    var btnGroup = BootstrapElement.dropdownGroup();
    var btn = BootstrapElement.dropdownButton('buttonAdd', '+');
    btnGroup.append(btn);

    var dropdownMenu = BootstrapElement.dropdownMenu('buttonAdd');
    var newCategoryItem = BootstrapElement.dropdownMenuItem('dropdownNewCategory', 'New category');
    newCategoryItem.on('click.simple', this.onNewCategoryClick.bind(this));
    dropdownMenu.append(newCategoryItem);
    btnGroup.append(dropdownMenu);

    return btnGroup;
};

FactoryView.prototype.createRemoveButton = function () {
    var btn = BootstrapElement.button(undefined, '-');

    btn.on('click.simple', function() {
        this.controller.removeCategory();
    }.bind(this));

    return btn;
};

FactoryView.prototype.createEditCategoryButton = function () {
    var self = this;
    var changeColour = function(colour) {
        return function() {
            self.controller.setCategoryColour(colour);
        };
    };
    var colours = [
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(165, 91, 91), changeColour(0)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(165, 109, 91), changeColour(15)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(165, 128, 91), changeColour(30)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(165, 147, 91), changeColour(45)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(165, 165, 91), changeColour(60)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(147, 165, 91), changeColour(75)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(128, 165, 91), changeColour(90)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(109, 165, 91), changeColour(105)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(91, 165, 91), changeColour(120)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(91, 165, 109), changeColour(135)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(91, 165, 128), changeColour(150)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(91, 165, 147), changeColour(165)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(91, 165, 165), changeColour(180)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(91, 147, 165), changeColour(195)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(91, 128, 165), changeColour(210)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(91, 109, 165), changeColour(225)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(91, 91, 165), changeColour(240)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(109, 91, 165), changeColour(255)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(128, 91, 165), changeColour(270)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(147, 91, 165), changeColour(285)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(165, 91, 165), changeColour(300)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(165, 91, 147), changeColour(315)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(165, 91, 128), changeColour(330)),
        BootstrapElement.dropdownMenuItem(undefined, BootstrapElement.colorSquare(165, 91, 109), changeColour(345))
    ];

    var dropdown = BootstrapElement.dropdown('Edit category');
    var dropdownMenu, dropdownSubMenu, dropdownItem;

    dropdownMenu = dropdown.dropdownMenu;
    dropdownSubMenu = BootstrapElement.dropdownSubMenu('Edit colour', colours);
    dropdownMenu.append(dropdownSubMenu);
    dropdownItem = BootstrapElement.dropdownMenuItem(undefined, 'Edit name', function() { self.controller.changeCategoryName(); });
    dropdownMenu.append(dropdownItem);

    return dropdown;
};

FactoryView.prototype.disableEditCategoryButton = function(bool) {
    var btn = $(this.editCategoryButton.children('button')[0]);
    btn.prop('disabled', bool);
};

FactoryView.prototype.changeCategoryName = function(oldName, newName) {
    var categories = this.categoriesList.find('a');
    for (var i = 0, len = categories.length; i < len; i++) {
        var category = $(categories[i]);
        if (category.html() == oldName) {
            category.html(newName);
            break;
        }
    }
};

FactoryView.prototype.onNewCategoryClick = function() {
    var categoryName = prompt('Please enter the new category name:');
    if (categoryName === null || categoryName === '') return;
    if (this.categoriesName.indexOf(categoryName) !== -1) {
        alert('Another category with name "' + categoryName + '" already exists.');
        return;
    }
    this.categoriesName.push(categoryName);
    if (this.categoriesList.html() == FactoryView.NO_CATEGORY_MSG) {
        this.categoriesList.remove();
        this.categoriesList = this.createCategoryList(this.categoriesName);
        this.setSelectedCategory(categoryName);
        this.controller.createToolboxCategory();
        this.middleDiv.prepend(this.categoriesList);
        this.removeButton.prop('disabled', false);
        this.disableEditCategoryButton(false);
    } else {
        this.categoriesList.append(this.createCategoryListItem(categoryName));
        this.setSelectedCategory(categoryName);
        this.controller.createToolboxCategory();
        if (this.categoriesName.length > 1) {
            this.moveUpButton.prop('disabled', false);
            this.moveDownButton.prop('disabled', false);
        }
    }
};


FactoryView.prototype.createEmptyCategoryList = function() {
    return BootstrapElement.paragraph(FactoryView.NO_CATEGORY_MSG);
};

FactoryView.prototype.createCategoryList = function(categoriesName) {
    var ul = null;
    if (categoriesName.length === 0) {
        ul = this.createEmptyCategoryList();
        this.removeButton.prop('disabled', true);
        this.disableEditCategoryButton(true);
    } else {
        if (categoriesName.length > 1) {
            this.moveUpButton.prop('disabled', false);
            this.moveDownButton.prop('disabled', false);
        }
        ul = BootstrapElement.stackedTabs();
        for (var i = 0, len = categoriesName.length ; i < len; i ++) {
            var item = this.createCategoryListItem(categoriesName[i]);
            ul.append(item);
        }
        this.removeButton.prop('disabled', false);
        this.disableEditCategoryButton(false);
    }
    return ul;
};

FactoryView.prototype.setSelectedCategory = function(categoryName) {
    var categories = this.categoriesList.find('li');
    categories.removeClass('active');
    for (var i = 0, len = categories.length; i < len ; i++) {
        var category = $($(categories[i]).find('a')[0]);
        if (category.html() === categoryName) {
            $(categories[i]).addClass('active');
        }
    }
    this.selectedCategory = categoryName;
};

FactoryView.prototype.createCategoryListItem = function(name) {
    var li = BootstrapElement.listItem();
    var a = BootstrapElement.link();
    a.html(name);
    a.on('click.simple', function() {
        this.setSelectedCategory(name);
        this.controller.toolboxFactory.loadCategoryInWorkspace(name);
    }.bind(this));
    li.append(a);
    return li;
};

FactoryView.prototype.removeCategoryListItem = function(name) {
    var categoriesList = this.categoriesList;
    var lis = categoriesList.find('li');
    for (var i = 0, len = lis.length; i < len; i++) {
        var li = $(lis[i]);
        var a = $(li.find('a')[0]);
        if (a.html() == name) {
            li.remove();
            break;
        }
    }
    if (lis.length <= 2) {
        this.moveUpButton.prop('disabled', true);
        this.moveDownButton.prop('disabled', true);
    }
    if (lis.length === 1) {
        this.removeButton.prop('disabled', true);
        this.disableEditCategoryButton(true);
        this.categoriesList.remove();
        this.categoriesList = this.createEmptyCategoryList();
        this.middleDiv.prepend(this.categoriesList);
    }
};

FactoryView.prototype.createMoveUpButton = function() {
    var btn = BootstrapElement.button(undefined, '↑');

    btn.on('click.simple', function() {
        this.moveUpCategory();
        this.controller.moveUpCategory();
    }.bind(this));
    btn.prop('disabled', true);

    return btn;
};

FactoryView.prototype.moveUpCategory = function() {
    var categories = this.categoriesList.find('li');
    for (var i = 1, len = categories.length; i < len; i++) {
        var categoryItem = $(categories[i]);
        var category = $(categoryItem.first('a'));
        if (category.text() == this.selectedCategory) {
            $(categories[i-1]).before(categoryItem.detach());
        }
    }
};

FactoryView.prototype.createMoveDownButton = function() {
    var btn = BootstrapElement.button(undefined, '↓');

    btn.on('click.simple', function() {
        this.moveDownCategory();
        this.controller.moveDownCategory();
    }.bind(this));
    btn.prop('disabled', true);

    return btn;
};

FactoryView.prototype.moveDownCategory = function() {
    var categories = this.categoriesList.find('li');
    for (var i = 0, len = categories.length - 1; i < len; i++) {
        var categoryItem = $(categories[i]);
        var category = $(categoryItem.first('a'));
        if (category.text() == this.selectedCategory) {
            $(categories[i+1]).after(categoryItem.detach());
        }
    }
};

FactoryView.prototype.createMakeUndeletableButton = function() {
    var btn = BootstrapElement.button(undefined, "Make undeletable");

    btn.on('click.simple', function() {
        if (Blockly.selected) {
            Blockly.selected.setDeletable(false);
            this.controller.savePreloadWorkspace();
            this.deletableButton.show();
            this.undeletableButton.hide();
        }
    }.bind(this));

    btn.hide();
    return btn;
};

FactoryView.prototype.createMakeDeletableButton = function() {
    var btn = BootstrapElement.button(undefined, "Make deletable");

    btn.on('click.simple', function() {
        if (Blockly.selected) {
            Blockly.selected.setDeletable(true);
            this.controller.savePreloadWorkspace();
            this.undeletableButton.show();
            this.deletableButton.hide();
        }
    }.bind(this));

    btn.hide();
    return btn;
};

FactoryView.prototype.createMakeMovableButton = function() {
    var btn = BootstrapElement.button(undefined, "Make movable");

    btn.on("click.simple", function() {
        if (Blockly.selected) {
            Blockly.selected.setMovable(true);
            this.controller.savePreloadWorkspace();
            this.unmovableButton.show();
            this.movableButton.hide();
        }
    }.bind(this));

    btn.hide();
    return btn;
};

FactoryView.prototype.createMakeUnmovableButton = function() {
    var btn = BootstrapElement.button(undefined, "Make unmovable");

    btn.on("click.simple", function() {
        if (Blockly.selected) {
            Blockly.selected.setMovable(false);
            this.controller.savePreloadWorkspace();
            this.movableButton.show();
            this.unmovableButton.hide();
        }
    }.bind(this));

    btn.hide();
    return btn;
};

FactoryView.prototype.createMakeEnabledButton = function() {
    var btn = BootstrapElement.button(undefined, "Enable");

    btn.on('click.simple', function() {
        this.enableButton.hide();
        Blockly.selected.setDisabled(false);
        this.controller.savePreloadWorkspace();
        this.disableButton.show();
    }.bind(this));

    btn.hide();
    return btn;
};

FactoryView.prototype.createMakeDisabledButton = function() {
    var btn = BootstrapElement.button(undefined, "Disable");

    btn.on('click.simple', function() {
        this.disableButton.hide();
        Blockly.selected.setDisabled(true);
        this.controller.savePreloadWorkspace();
        this.enableButton.show();
    }.bind(this));

    btn.hide();
    return btn;
};

FactoryView.prototype.createMakeEditableButton = function() {
    var btn = BootstrapElement.button(undefined, "Make editable");

    btn.on('click.simple', function() {
        this.editableButton.hide();
        Blockly.selected.setEditable(true);
        this.controller.savePreloadWorkspace();
        this.uneditableButton.show();
    }.bind(this));

    btn.hide();
    return btn;
};

FactoryView.prototype.createMakeUneditableButton = function() {
    var btn = BootstrapElement.button(undefined, "Make uneditable");

    btn.on('click.simple', function() {
        this.uneditableButton.hide();
        Blockly.selected.setEditable(false);
        this.controller.savePreloadWorkspace();
        this.editableButton.show();
    }.bind(this));

    btn.hide();
    return btn;
};
