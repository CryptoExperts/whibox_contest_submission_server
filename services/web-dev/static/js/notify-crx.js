(function(crx_wb, $, undefined) {
    $(document).ready(function() {
	delay_between_alerts = 250; // in ms
	t = 0;
	$('.alert').each(function() {
	    $(this).delay( t ).queue(function() {
		$(this).addClass('alert-active');
	    });
	    t += delay_between_alerts;
	});
    });
}(window.crx_wb = window.crx_wb || {}, jQuery));
