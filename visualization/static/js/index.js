
function drawChart(data){

    var ctx = $("#chart")[0].getContext("2d")

    var chart_data = data.map(function (d) { return  d.count})
    var labels = data.map(function(d) {
        return new Date(d._id.year + "-" + d._id.month + "-" + d._id.day)
    })


    var chart = new Chart(ctx,{
        type:"line",
        data:{
            datasets:[{
                data:chart_data,
            }],
             labels: labels
        }
    })
}

function getDailyPattern(){
    $.get('daily', drawDailyChart)
}
function drawDailyChart(data){
    var ctx = $("#daily_chart")[0].getContext("2d")
    console.log(data)
    var chart_data = data.map(function (d) { 
        var newHour = d._id.hour -5

        if(newHour<0){
            newHour = 24 + newHour
        }

        return {
                y:d.count,
                x:newHour
        }
    })

    chart_data = chart_data.sort(function(a,b){
        return a.x-b.x
    })
    
    console.log(chart_data)
    var chart = new Chart(ctx, {
        type: "bar",
        data: {
            datasets: [{
                data: chart_data,
            }],
            labels: [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        }
    })
}
function getSubCount(){

    $.get('submissions',drawChart)
}


getSubCount()
getDailyPattern()