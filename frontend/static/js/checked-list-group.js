//http://bootsnipp.com/snippets/featured/checked-list-group
$(function()
{
    $('.list-group.checked-list-box .list-group-item').each(function()
    {

        // Settings

        var $widget = $(this);
        var $checkbox = $('<input type="checkbox" class="hidden" />');
        if($widget.data('name'))
            $checkbox.attr('name', $widget.data('name'));
        if($widget.data('value'))
            $checkbox.attr('value', $widget.data('value'));
        var color = ($widget.data('color') ? $widget.data('color') : "primary"),
            style = ($widget.data('style') == "button" ? "btn-" : "list-group-item-"),
            settings = {
                on:  {
                    icon: 'fa fa-check-square fa-fw'
                },
                off: {
                    icon: 'fa fa-square-o fa-fw'
                }
            };

        $widget.css('cursor', 'pointer')
        $widget.append($checkbox);

        // Event Handlers
        $widget.on('click', function()
        {
            $checkbox.prop('checked', !$checkbox.is(':checked'));
            $checkbox.triggerHandler('change');
            updateDisplay();
        });
        $checkbox.on('change', function()
        {
            updateDisplay();
        });

        // Actions
        function updateDisplay()
        {
            var isChecked = $checkbox.is(':checked');

            // Set the button's state
            $widget.data('state', (isChecked) ? "on" : "off");

            // Set the button's icon
            $widget.find('.state-icon')
                .removeClass()
                .addClass('state-icon ' + settings[$widget.data('state')].icon);

            // Update the button's color
            if(isChecked)
            {
                $widget.addClass(style + color + ' active');
            }
            else
            {
                $widget.removeClass(style + color + ' active');
            }
        }

        // Initialization
        function init()
        {

            if($widget.data('checked') == true)
            {
                $checkbox.prop('checked', !$checkbox.is(':checked'));
            }

            updateDisplay();

            // Inject the icon if applicable
            if($widget.find('.state-icon').length == 0)
            {
                $widget.prepend('<i class="state-icon ' + settings[$widget.data('state')].icon + '"></i>&nbsp;');
            }
        }

        init();
    });

    $('#get-checked-data').on('click', function(event)
    {
        event.preventDefault();
        var checkedItems = {}, counter = 0;
        $("#check-list-box li.active").each(function(idx, li)
        {
            checkedItems[counter] = $(li).text();
            counter++;
        });
        $('#display-json').html(JSON.stringify(checkedItems, null, '\t'));
    });
});