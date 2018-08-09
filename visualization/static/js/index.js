
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

    var total = data.reduce(function(partial,t){
        return partial+t.count
    },0)

    var chart_data = data.map(function (d) { 
        var newHour = d._id.hour - 5

        if(newHour<0){
            newHour = 24 + newHour
        }

        return {
                y:d.count/total,
                x:newHour
        }
    })

    chart_data = chart_data.sort(function(a,b){
        return a.x-b.x
    })

    var chart = new Chart(ctx, {
        type: "bar",
        data: {
            datasets: [{
                data: chart_data,
                label: "Number of submissions"
            }],
            labels: [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        }
    })
}
function getSubCount(){

    $.get('submissions',drawChart)
}


function drawEntitiesChart(data){
    var ctx = $("#entities_chart")[0].getContext("2d")
    var chart_data = data.map(function (d) {
        id_array = d._id.split('/')
        name = id_array[id_array.length - 1]
        return {
            y: d.count,
            x: name
        }
    })

    console.log(chart_data)
    var labels = data.map(function (d) {
        id_array = d._id.split('/')
        name = id_array[id_array.length-1]
        return name
    })
    var chart = new Chart(ctx, {
        type: "bar",
        data: {
            datasets: [{
                label: "Entities mentions",
                data: chart_data,
            }],
            labels: labels
        }
    })

    $("#entities_chart").on('click', function (e) {
        var bar = chart.getElementAtEvent(e);

        if (!bar.length) {
            return
        }

        entity = bar[0]._model.label
        console.log(bar[0]._model.label)

        $.get("posts?dbpedia_entity=" + entity, drawPosts)
    })


}
function getEntities(){
    $.get('dbpedia_entities', drawEntitiesChart)

}

function drawTopicsChart(data) {
    var ctx = $("#topics_chart")[0].getContext("2d")
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
                label: "Topics mentions",
                data: chart_data,
            }],
            labels: labels
        }
    })

    $("#topics_chart").on('click', function (e) {
        var bar = chart.getElementAtEvent(e);

        if (!bar.length) {
            return
        }

        topic = bar[0]._model.label
        console.log(bar[0]._model.label)

       $.get("posts?topic="+topic,drawPosts)
    })


}

function drawPosts(data){
    var $container = $('.posts-container')

    $container.empty()
    console.log(data)
    data.forEach(d => {

        var text = ""
        if(d["type"]==="post"){
            text = (d["title"] || "") + (d["selftext_html"] || "") + '\n<a href="' + d["url"] + '" target="_blank">Original Post</a>'
        }else{
            text = d["body"]
        }
        var $post = $(document.createElement("div"))
        $post.addClass('post')
        var $body = $(document.createElement("div"))
        $body.html(text)
        $body.appendTo($post)
        $post.appendTo($container)

        console.log($post)
    });
}

function getTopics() {
    $.get('topics', drawTopicsChart)

}


function drawTermChart(data){
    var ctx = $("#terms_chart")[0].getContext("2d")
    var chart_data = data.map(function (d) {
        return {
            y: d.value,
            x: d.term
        }
    })

    console.log(chart_data)
    var labels = data.map(function (d) {
        return d.term
    })
    var chart = new Chart(ctx, {
        type: "bar",
        data: {
            datasets: [{
                label: "Term mentions",
                data: chart_data,
            }],
            labels: labels
        }
    })
}

function getTerms(){
    $.get('terms',drawTermChart)
}

getDailyPattern()
getEntities()
getTopics()
getTerms()