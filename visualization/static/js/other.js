
function getPostActivity(){
    $.get('subreddits_activity?type=post',drawChart.bind(null,'post'))
}
function getCommentActivity() {
    $.get('subreddits_activity?type=comment', drawChart.bind(null, 'comment'))
}

function drawChart(type,data){
    var ctx = $("#chart"+type)[0].getContext("2d")
    console.log(data)
    var chart_data = data.map(function (d) {
        return {
            y: d.count,
            x: d._id
        }
    })

    var labels = data.map(function(d){
        return d._id
    })
    console.log(chart_data)
    var chart = new Chart(ctx, {
        type: "bar",
        data: {
            datasets: [{
                label:"# of "+type,
                data: chart_data,
            }],
            labels:labels
        }
    })


    $("#chart"+type).on('click',function(e) {    
        var bar = chart.getElementAtEvent(e);

        if(!bar.length){
            return
        }


        console.log(bar[0]._model.label)

        var url = "https://www.reddit.com/" + bar[0]._model.label
        window.open(url)
    })
}


getPostActivity()
getCommentActivity()