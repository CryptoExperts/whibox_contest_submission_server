(function(crx_wb, $, undefined) {
    $(document).ready(function() {
	$('.flot-plot').each(function() {
	    $.plot($(this), eval($(this).attr('data-flot')),
		   {legend: {show: false},
		    xaxis: {show: true, mode: "time", timeformat: "%m/%d"},
		    yaxis: {position: "right"},
		    series: {shadowSize: 0}});
	});
    });
}(window.crx_wb = window.crx_wb || {}, jQuery));
