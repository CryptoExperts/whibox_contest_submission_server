$(function() {
    var programs = getProgramsToPlot();

    function dataGrowth(start, end, factor) {
        var minutes = Math.floor((end-start)/60);
        return [...Array(minutes+1).keys()].map(i => [start*1000 + i*60000, factor*Math.pow(i/1440,2)]);
    }

    function dataDecrease(start, peak, end, factor) {
        var minutes_before_peak = Math.floor((peak-start)/60);
        var minutes_after_peak = Math.floor((end-peak)/60);
        var minutes_decrease = Math.min(minutes_before_peak, minutes_after_peak);
        return [...Array(minutes_decrease+1).keys()].map(i => [peak*1000 + i*60000, factor*Math.pow((minutes_before_peak-i)/1440,2)]);
    }

    function getData() {
        var now = Math.floor(Date.now() / 1000);
        var deadline = Math.floor(new Date('2021-09-11T00:00:00Z').getTime() / 1000);
        now = Math.min(now, deadline);
        var strawberries = [];
        programs.forEach(function(p) {
            var strawberry_curve;
            if (p.ts_break > 0) {
                strawberry_curve1 = dataGrowth(p.ts_publish, p.ts_break, p.performance);
                strawberry_curve2 = dataDecrease(p.ts_publish, p.ts_break, now, p.performance);
                strawberry_curve = strawberry_curve1.concat(strawberry_curve2);
            } else {
                strawberry_curve = dataGrowth(p.ts_publish, now, p.performance);
            }
            strawberries.push({
                color: p.color,
                label: "&nbsp;" + p.name + " (" + p.id + ")&nbsp;&nbsp;",
                data: strawberry_curve
            });

        });

        return [strawberries];
    }

    // Set up the control widget
    var updateInterval = 600000; // 10 min
    var data = getData();
    var plotStrawberry = $.plot("#strawberryholder", data[0] , {
        series: {shadowSize: 0},
        yaxis: {min: 0, position: "right"},
        xaxis: { show: true, mode: "time", timeformat: "%m/%d" },
        legend: { position: "nw", noColumns: 2, margin: 10}
    });
    function update() {
        console.log("update chart at: ", Date());
        var data = getData()
        plotStrawberry.setData(data[0]);
        plotStrawberry.draw();
        setTimeout(update, updateInterval);
    }
    update();
});
