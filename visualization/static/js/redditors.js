

function getContributors(){

    $.get("contributors",drawContributorsChart)
}

function drawContributorsChart(data){
    var ctx = $("#contributors_chart")[0].getContext("2d")
    console.log(data)
    var chart_data = data.map(function (d) {
        return {
            y: d.count,
            x: d._id
        }
    })

    var labels = data.map(function (d) {
        return d._id
    })
    console.log(chart_data)
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
}


getContributors()