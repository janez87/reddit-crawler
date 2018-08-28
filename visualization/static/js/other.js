
function getPostActivity(){
    $.get('subreddits_distinct_activity?type=post',drawChart.bind(null,'post'))
}
function getCommentActivity() {
    $.get('subreddits_distinct_activity?type=comment', drawChart.bind(null, 'comment'))
}

function drawPosts(data) {
    var $postsContainer = $('.posts-container')
    var $commentsContainer = $('.comments-container')
    $postsContainer.empty()
    $commentsContainer.empty()

    data.forEach(d => {

        var text = ""
        if (d["type"] === "post") {
            text = ('<strong>' + d["title"] + '</strong>' || "") + (d["selftext_html"] || "") + '\n<a href="' + d["url"] + '" target="_blank">Original Post</a>'
            var $post = $(document.createElement("div"))
            $post.addClass('post')
            var $body = $(document.createElement("div"))
            $body.html(text)
            $body.appendTo($post)
            $post.appendTo($postsContainer)


        } else {
            text = d["body"]
            var $post = $(document.createElement("div"))
            $post.addClass('post')
            var $body = $(document.createElement("div"))
            $body.html(text)
            $body.appendTo($post)
            $post.appendTo($commentsContainer)
        }

    });
}

function drawChart(type,data){
    var ctx = $("#chart"+type)[0].getContext("2d")
    var chart_data = data.map(function (d) {
        return {
            y: d.count,
            x: d._id
        }
    })

    var labels = data.map(function(d){
        return d._id
    })
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


        var subreddit = bar[0]._model.label
        
        $.get("dbpedia_entities?subreddit="+subreddit,function (data) {
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
                name = id_array[id_array.length - 1]
                return name
            })

            entity_chart.data.datasets[0] = {
                data : chart_data,
                label: "# of entity"
                
            }

            entity_chart.data.labels = labels

            entity_chart.update()
        })

        $.get("topics?subreddit=" + subreddit, function (data) {
            var chart_data = data.map(function (d) {
                id_array = d._id.split('/')
                name = id_array[id_array.length - 1]
                return {
                    y: d.count,
                    x: name
                }
            })

            var labels = data.map(function (d) {
                id_array = d._id.split('/')
                name = id_array[id_array.length - 1]
                return name
            })

            topic_chart.data.datasets[0] = {
                data: chart_data,
                label: "# of topic"
            }

            topic_chart.data.labels = labels

            topic_chart.update()
        })
    })
}

function drawEntityChart(data) {
    var ctx = $("#entity_chart")[0].getContext("2d")
    var chart_data = data.map(function (d) {
        id_array = d._id.split('/')
        name = id_array[id_array.length - 1]
        return {
            y: d.count,
            x: name
        }
    })

    var labels = data.map(function (d) {
        id_array = d._id.split('/')
        name = id_array[id_array.length - 1]
        return name
    })
    entity_chart = new Chart(ctx, {
        type: "bar",
        data: {
            datasets: [{
                label: "Entity mentions",
                data: chart_data,
            }],
            labels: labels
        }
    })

    $("#entity_chart").on('click', function (e) {
        var bar = entity_chart.getElementAtEvent(e);

        if (!bar.length) {
            return
        }

        entity = bar[0]._model.label
        console.log(bar[0]._model.label)

        $.get("posts?other=true&dbpedia_entity=" + entity, drawPosts)
    })

}

function getEntities() {
    $.get('dbpedia_entities?other=true', drawEntityChart)
}

function drawTopicChart(data) {
    var ctx = $("#topic_chart")[0].getContext("2d")
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
        name = id_array[id_array.length - 1]
        return name
    })
    topic_chart = new Chart(ctx, {
        type: "bar",
        data: {
            datasets: [{
                label: "Topic mentions",
                data: chart_data,
            }],
            labels: labels
        }
    })

    $("#topic_chart").on('click', function (e) {
        var bar = topic_chart.getElementAtEvent(e);

        if (!bar.length) {
            return
        }

        topic = bar[0]._model.label
        console.log(bar[0]._model.label)

        $.get("posts?other=true&topic=" + topic, drawPosts)
    })
}

function getTopics() {
    $.get('topics?other=true', drawTopicChart)
}


getPostActivity()
getCommentActivity()
getEntities()
getTopics()