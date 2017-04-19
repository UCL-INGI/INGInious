var BootstrapElement = function() {
};

BootstrapElement.button = function(id, content) {
    var button = $("<button>");
    button.addClass('btn');
    button.addClass('btn-default');
    button.attr('id', id);
    button.attr('type', 'button');
    button.css('margin-top', '5px');
    button.css('margin-right', '5px');
    button.css('margin-left', '5px');
    button.html(content);
    return button;
};

BootstrapElement.colorSquare = function(red, green, blue) {
    var div = $('<div>');
    div.css('border', '1px solid #000');
    div.css('height', '13px');
    div.css('position', 'relative');
    div.css('width', '15px');
    div.css('background-color', 'rgb('+red+','+green+','+blue+')');
    return div;
};

BootstrapElement.column = function(size) {
    var div = $('<div>');
    div.addClass('col-xs-' + size);
    div.css('height', '100%');
    return div;
};

BootstrapElement.divider = function() {
    var li = $('<li>');
    li.addClass('divider');
    return li;
};

BootstrapElement.dropdown = function(name) {
    var div = BootstrapElement.dropdownGroup();

    var btn = BootstrapElement.dropdownButton(null, name);
    div.append(btn);

    var dropdownMenu = BootstrapElement.dropdownMenu();
    dropdownMenu.addClass('multi-level');
    div.append(dropdownMenu);
    div.dropdownMenu = dropdownMenu;

    return div;
};

BootstrapElement.dropdownButton = function(id, content) {
    var button = $("<button>");
    button.addClass('btn');
    button.addClass('btn-default');
    button.addClass('dropdown-toggle');
    button.attr('id', id);
    button.attr('type', 'button');
    button.attr('data-toggle', 'dropdown');
    button.attr('aria-haspopup', 'true');
    button.attr('aria-expanded', 'false');
    button.html(content);
    return button;
};

BootstrapElement.dropdownGroup = function() {
    var div = $("<div>");
    div.addClass('btn-group');
    div.attr('role', 'group');
    div.css('padding-top', '5px');
    div.css('padding-right', '5px');
    div.css('padding-left', '5px');
    return div;
};

BootstrapElement.dropdownMenu = function(buttonId) {
    var ul = $("<ul>");
    ul.addClass('dropdown-menu');
    ul.attr('role', 'menu');
    ul.attr('aria-labelledby', buttonId);
    return ul;
};

BootstrapElement.dropdownMenuItem = function(id, content, onclick) {
    var li = $("<li>");
    var a = $("<a>");
    a.attr('id', id);
    a.on('click.simple', onclick);
    a.append(content);
    li.append(a);
    li.a = a;
    return li;
};

BootstrapElement.dropdownSubMenu = function(name, content) {
    var li = BootstrapElement.listItem();
    li.addClass('dropdown-submenu');
    var a = BootstrapElement.link();
    a.html(name);
    a.attr('tabindex', '-1');
    li.append(a);
    var ul = BootstrapElement.dropdownMenu();
    ul.append(content);

    li.append(ul);
    return li;
};

/*
 * @return a list item jQuery element
 */
BootstrapElement.listItem = function(content) {
    var li = $('<li>');
    li.append(content);
    return li;
};

/*
 * @return a jQuery link element
 */
BootstrapElement.link = function(content) {
    var a = $("<a>");
    a.append(content);
    return a;
};

BootstrapElement.paragraph = function(content) {
    var p = $('<p>');
    p.append(content);
    return p;
};

BootstrapElement.stackedTabs = function(content) {
    var ul = $("<ul>");
    ul.addClass('nav');
    ul.addClass('nav-pills');
    ul.addClass('nav-stacked');
    ul.append(content);
    return ul;
};

BootstrapElement.tab = function(targetId, name) {
    var tab = $("<li>");
    tab.attr('role', 'presentation');

    var link = $("<a>");
    link.attr('href', '#' + targetId);
    link.attr('role', 'tab');
    link.attr('data-toggle', 'tab');
    link.html(name);
    tab.append(link);

    return tab;
};

BootstrapElement.tabContent = function () {
    var div = $("<div>");
    div.addClass('tab-content');
    div.css('height', '100%');
    return div;
};

BootstrapElement.tabList = function() {
    var tabList = $("<ul>");
    tabList.addClass('nav');
    tabList.addClass('nav-tabs');
    tabList.attr('role', 'tablist');
    return tabList;
};

BootstrapElement.tabPane = function(divId) {
    var div = $("<div>");
    div.attr('id', divId);
    div.addClass('tab-pane');
    div.css('height', '100%');
    return div;
};

BootstrapElement.textArea = function(id, content) {
    var textarea = $('<textarea>');
    textarea.attr('id', id);
    textarea.text(content);
    textarea.hide();
    return textarea;
};
