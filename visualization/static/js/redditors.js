

function getContributors(){

    $.get("contributors",drawContributorsChart)
}

function drawContributorsChart(data){
    var ctx = $("#contributors_chart")[0].getContext("2d")
    var chart_data = data.map(function (d) {
        return {
            y: d.count,
            x: d._id
        }
    })

    var labels = data.map(function (d) {
        return d._id
    })
    var chart = new Chart(ctx, {
        type: "bar",
        data: {
            datasets: [{
                label: "Top contributors of r/NEET",
                data: chart_data,
            }],
            labels: labels
        }
    })

    $("#contributors_chart").on('click', function (e) {
        var bar = chart.getElementAtEvent(e);

        if (!bar.length) {
            return
        }

        var name = bar[0]._model.label

        $.get("contributor?name=" + name, drawSubChart)
    })
}

function getDates(startDate, endDate) {
    var dates = [],
        currentDate = startDate,
        addDays = function (days) {
            var date = new Date(this.valueOf());
            date.setDate(date.getDate() + days);
            return date;
        };
    while (currentDate <= endDate) {
        dates.push(moment(currentDate));
        currentDate = addDays.call(currentDate, 1);
    }
    return dates;
}

function drawSubChart(data){
    var ctx = $("#sub_chart")[0].getContext("2d")
   
    var chart_data_comments = data.comments.map(function (d) {
        return {
            y: d.count,
            t: moment(d.date),
            x: moment(d.date)
        }
    })

    console.log(chart_data_comments)
    var chart_data_posts = data.posts.map(function (d) {
        return {
            y: d.count,
            t: moment(d.date),
            x: moment(d.date)
        }
    })

    post_range = getDates(chart_data_posts[0]['t'], chart_data_posts[chart_data_posts.length-1]['t'])
    comment_range = getDates(chart_data_comments[0]['t'], chart_data_comments[chart_data_comments.length - 1]['t'])

    console.log(post_range)
    filled_chart_data_posts = []

    k = 0
    for (let index = 0; index < chart_data_posts.length; index++) {
        const element = chart_data_posts[index];

        for (let j = k; j < post_range.length; j++) {
            const d = post_range[j];
            
            if(d.isBefore(element.t,'hour')){
                filled_chart_data_posts.push({
                    y:0,
                    t:d
                })
                continue
            }
            if(d.isSame(element.t,'hour')){
                filled_chart_data_posts.push({
                    y:element.y,
                    t:d
                })
                k=j
                break
            }
            if (d.isAfter(element.t, 'hour')) {
                filled_chart_data_posts.push({
                    y: 0,
                    t: d
                })
                k=j
                break
            }
        }       
    }

    filled_chart_data_comments = []

    k = 0
    for (let index = 0; index < chart_data_comments.length; index++) {
    const element = chart_data_comments[index];

        for (let j = k; j < comment_range.length; j++) {
            const d = comment_range[j];

            if (d.isBefore(element.t, 'hour')) {
                filled_chart_data_comments.push({
                    y: 0,
                    t: d
                })
                continue
            }
            if (d.isSame(element.t, 'hour')) {
                filled_chart_data_comments.push({
                    y: element.y,
                    t: d
                })
                k = j
                break
            }
            if (d.isAfter(element.t, 'hour')) {
                filled_chart_data_comments.push({
                    y: 0,
                    t: d
                })
                k = j
                break
            }
        }
    }
   
    var chart = new Chart(ctx, {
        type: "line",
        bezierCurve: false,
        data: {
            datasets: [{
                label: "Comments",
                data: filled_chart_data_posts,
                color:'rgb(0,0,255)'
            },{
                label: "Posts",
                data: filled_chart_data_comments
            }],
        },
        options: {
            scales: {
                xAxes: [{
                    type:'time',
                    distribution:'series',
                    time: {
                        unit: 'day'
                    }
                }]
            }
        }
    })
}

getContributors()