//Various functions to display remaining times
$(function()
{
    var timezone = $('.access_countdown').attr('timezone')

	$('.contest_starting_time').each(function(){
	    contest_starting_time.call(this, timezone);
	});
	$('.contest_remaining_time').each(function(){
	    contest_remaining_time.call(this, timezone);
	});
	$('.contest_blackout_time').each(function(){
	    contest_blackout_time.call(this, timezone);
	});
});

function contest_starting_time(timezone)
{
    var timezone_adapted_start = moment.utc($(this).attr('starts-at')).clone().tz(timezone).format('YYYY-MM-DD HH:mm:ss');
	$(this).countdown(timezone_adapted_start).on('update.countdown', function(event)
	{
		var format = '%H:%M:%S';
		if(event.offset.totalDays > 0) {
			format = '%-D day%!D ' + format;
		}

		var current_UTC_time = moment.utc(); // Get the current UTC time
		var contest_start_time = moment.utc($(this).attr('starts-at')); // Get the contest start time
        var duration = moment.duration(contest_start_time.diff(current_UTC_time));

        var hours = duration.hours().toString().padStart(2, '0'); // Ensure two digits with leading zero if needed
        var minutes = duration.minutes().toString().padStart(2, '0');
        var seconds = duration.seconds().toString().padStart(2, '0');
        var formatted_duration = hours + ':' + minutes + ':' + seconds;

		$(this).html("Contest starts in: " + formatted_duration);
	}).on('finish.countdown', function(event)
	{
		location.reload(); //reload the page
		$(this).html('<b>Contest started!</b>');
	});
}

function contest_remaining_time(timezone)
{
    var timezone_adapted_end = moment.utc($(this).attr('ends-at')).clone().tz(timezone).format('YYYY-MM-DD HH:mm:ss');
	$(this).countdown(timezone_adapted_end).on('update.countdown', function(event)
	{
		var format = '%H:%M:%S';
		if(event.offset.totalDays > 0) {
			format = '%-D day%!D ' + format;
		}

		var current_UTC_time = moment.utc();
		var contest_end_time = moment.utc($(this).attr('ends-at'));
        var duration = moment.duration(contest_end_time.diff(current_UTC_time));

        var hours = duration.hours().toString().padStart(2, '0');
        var minutes = duration.minutes().toString().padStart(2, '0');
        var seconds = duration.seconds().toString().padStart(2, '0');
        var formatted_duration = hours + ':' + minutes + ':' + seconds;

		$(this).html("Time remaining: " + formatted_duration);
	}).on('finish.countdown', function(event)
	{
		$(this).html('<b>Contest ended!</b>');
	});
}

function contest_blackout_time(timezone)
{
    var timezone_adapted_blackout = moment.utc($(this).attr('blackout-at')).clone().tz(timezone).format('YYYY-MM-DD HH:mm:ss');
	$(this).countdown(timezone_adapted_blackout).on('update.countdown', function(event)
	{
		var format = '%H:%M:%S';
		if(event.offset.totalDays > 0) {
			format = '%-D day%!D ' + format;
		}

		var current_UTC_time = moment.utc();
		var contest_blackout_time = moment.utc($(this).attr('blackout-at'));
        var duration = moment.duration(contest_blackout_time.diff(current_UTC_time));

        var hours = duration.hours().toString().padStart(2, '0');
        var minutes = duration.minutes().toString().padStart(2, '0');
        var seconds = duration.seconds().toString().padStart(2, '0');
        var formatted_duration = hours + ':' + minutes + ':' + seconds;

		$(this).html("Blackout in " + formatted_duration);
	}).on('finish.countdown', function(event)
	{
		$(this).html('<b>Blackout</b>');
	});
}

function dispenser_structure_contest() {
    return dispenser_util_structure();
}