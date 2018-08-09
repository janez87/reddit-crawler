# system modules
import datetime
import sys

# external modules
from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
from bson import ObjectId

# my modules
sys.path.append("../")
from configuration import configuration

app = Flask(__name__)
app.debug = True

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

# Views rendering


@app.route('/')
def index():
    return render_template('index.html', title='NEET viz')


@app.route('/other')
def other():
    return render_template('other.html', title='NEET viz')

@app.route('/redditors')
def redditors():
    return render_template("redditors.html", title='NEET viz')

# AJAX response
@app.route('/submissions')
def get_post_count():
    #start = int(request.args["start"])
    #end = int(request.args["end"])
    subreddit = None
    data = {}

    if "subreddit" in request.args:
        category = request.args["subreddit"]

    #start_date = datetime.datetime.fromtimestamp(start//1000)
    #end_date = datetime.datetime.fromtimestamp(end//1000)

    '''match = {
        "$match": {
            "created_at": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
    }'''

    match = {
        "$match": {
            "subreddit": "r/NEET"
        }
    }
    group = {
        "$group": {
            "_id": {
                "year": "$_id.year",
                "month": "$_id.month",
                "day": "$_id.day"
            },
            "count": {
                "$sum": "$count"
            }
        }

    }

    sort = {
        "$sort": {
            "_id": 1
        }
    }

    data = list(db["submissions_count"].aggregate([match, group, sort]))
    return jsonify(data)


@app.route('/daily')
def get_daily_pattern():
    #match = {
    #    "$match": {
    #        "subreddit": "r/NEET"
    #    }
    #}

    match = {
        "$match": {
            "subreddit":{
                "$ne":"r/NEET"
            }
        }
    }
    group = {
        "$group": {
            "_id": {
                "hour": "$_id.hour"
            },
            "count": {
                "$sum": "$count"
            }
        }

    }

    sort = {
        "$sort": {
            "_id.hour": -1
        }
    }

    data = list(db["submissions_count"].aggregate([match,group, sort]))
    return jsonify(data)


@app.route('/subreddits_distinct_activity')
def get_other_subreddit_distinct_count():

    submission_type = request.args["type"]

    query = [
	{
            "$match": {"type": submission_type, "subreddit": {"$ne": "r/NEET"}}
	}, {
            "$group": {
                "_id": {
                    "subreddit": "$subreddit",
                    "author": "$author_name"
                }
            }
	}, {

            "$group": {
                "_id": "$_id.subreddit",
                "count": {
                    "$sum": 1
                }
            }

	}, {

            "$sort": {
                "count": -1
            }
	},{

        "$limit":50
    }
    ]

    data = list(db["submissions_count"].aggregate(query))
    return jsonify(data)

@app.route('/subreddits_activity')
def get_other_subreddit_count():

    submission_type = request.args["type"]

    match = {
        "$match": {
            "type": submission_type,
            "subreddit_name_prefixed": {
                "$ne": "r/NEET"
            }
        }
    }

    group = {
        "$group": {
            "_id": "$subreddit_name_prefixed",
            "count": {
                "$sum": 1
            }
        }
    }

    sort = {
        "$sort": {
            "count": -1
        }
    }

    limit = {
        "$limit": 50
    }

    if "author" in request.args:
       match["$match"]["author_name"] = request.args["author"]

    data = list(db["submissions"].aggregate([match, group, sort, limit]))
    return jsonify(data)


@app.route('/dbpedia_entities')
def get_dbpedia_entities():
    query = [{
	"$match": {
            "dbpedia_entities": {
                "$exists": True
            },
            "subreddit_name_prefixed":"r/NEET"
	}
    }, {
	"$project": {
            "dbpedia_entities": 1
	}

    }, {

	"$unwind": "$dbpedia_entities"

    },{
        "$match":{
            "dbpedia_entities.similarityScore":{
                "$gte":0.7
            }
        }
    }, {

	"$project": {
            "uri": "$dbpedia_entities.URI"
	}

    }, {

	"$group": {

            "_id": "$uri",
          		"count": {
                            "$sum": 1
                        }

	}

    }, {

	"$sort": {
            "count": -1
	}
    },{

        "$limit":50
    }]

    if "other" in request.args:
        query[0]["$match"]["subreddit_name_prefixed"] = {
            "$ne":"r/NEET"
        }

    if "subreddit" in request.args:
         query[0]["$match"]["subreddit_name_prefixed"] = request.args["subreddit"]

    if "author" in request.args:
        query[0]["$match"]["author_name"] = request.args["author"]


    data = list(db["submissions"].aggregate(query))
    return jsonify(data)

@app.route('/entities')
def get_entities():
    query = [
        {
            "$match": {
                "entities": {
                    "$exists": True
                }

            }
        },
        {
            "$project": {
                "entities": 1
            }

        },
        {
            "$unwind": "$entities"
        },
        {
            "$match": {

                "entities.freebase_type.0": {"$exists": True}
            }
        },
        {
            "$project": {
                "entity": "$entities.id"
            }
        },
        {
            "$group": {
                "_id": "$entity",
                "count": {
                    "$sum": 1
                }
            }
        },
        {
            "$sort": {
                "count": -1
            }

        }, {

            "$limit": 50
        }]

    query[0]["$match"]["subreddit_name_prefixed"] = "r/NEET"

    data = list(db["submissions"].aggregate(query))
    return jsonify(data)


@app.route('/topics')
def get_topics():
    query = [{
        "$match": {
            "entities": {
                "$exists": True
            },
            "subreddit_name_prefixed":"r/NEET"
        }
    }, {

        "$project": {
            "topics": 1
        }

    },
        {
        "$unwind": "$topics"
    },
        {
        "$match": {
            "topics.score": {
                "$gte": 1
            }
        }
    },
        {
        "$project": {"topic": "$topics.label"}
    },
        {
        "$group": {
            "_id": "$topic",
            "count": {
                "$sum": 1
            }
        }
    },
        {
        "$sort": {
            "count": -1
        }

    }, {
        "$limit": 50
    }

    ]

    if "other" in request.args:
        query[0]["$match"]["subreddit_name_prefixed"] = {
            "$ne": "r/NEET"
        }

    if "subreddit" in request.args:
         query[0]["$match"]["subreddit_name_prefixed"] = request.args["subreddit"]

    if "author" in request.args:
        query[0]["$match"]["author_name"] = request.args["author"]

    data = list(db["submissions"].aggregate(query))
    return jsonify(data)


def clean(doc):
    from nltk import word_tokenize, pos_tag
    from nltk.corpus import stopwords
    from nltk.stem.wordnet import WordNetLemmatizer
    import string

    stop = set(stopwords.words('english'))
    exclude = set(string.punctuation)
    lemma = WordNetLemmatizer()

    stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)

    pos_tagged = pos_tag(punc_free.split())

    to_consider = list(filter(lambda x: x[1] not in [
                       'IN', 'CD', 'MD'], pos_tagged))

    to_consider = list(map(lambda x: x[0], to_consider))

    to_consider = list(filter(lambda x: x not in ['neet', 'im'], to_consider))

    normalized = " ".join(lemma.lemmatize(word) for word in to_consider)
    return normalized

@app.route("/terms")
def get_term_document_frequency():
    from gensim import corpora, models
    doc_complete = []
    print("Getting the submissions")

    query = {}

    if 'other' in request.args:
        query = {"subreddit_name_prefixed": {"$ne":"r/NEET"}}
    else: 
        query = {"subreddit_name_prefixed": "r/NEET"}


    submissions = db["submissions"].find(query)

    for s in submissions:
        if s["type"] == "post":
            text = s["title"]+' '+s["selftext"]
            doc_complete.append(text)
        else:
            doc_complete.append(s["body"])

    print("Cleaning the submissions")
    doc_clean = [clean(doc).split() for doc in doc_complete]
    dictionary = corpora.Dictionary(doc_clean)

    data = []

    for i, d in enumerate(dictionary):
        df = dictionary.dfs[i]
        data.append({
            "term":dictionary[d],
            "value": df
        })

    data = sorted(data,key=lambda x: -x["value"])    
    return jsonify(data[:100])

@app.route("/posts")
def get_post_by_topic():

    query = {}
    
    if "other" not in request.args:
        query = {
            "subreddit_name_prefixed": "r/NEET"
        }

    if "topic" in request.args:
        topic = request.args["topic"]
        query["topics"] = {
            "$elemMatch":{
                "label":topic,
                "score":1
            }
        }

    if "entity" in request.args:
        entity = request.args["entity"]
        query["entities"] = {
            "$elemMatch": {
                "id": entity
            }
        }

    if "dbpedia_entity" in request.args:
        dbpedia_entity = request.args["dbpedia_entity"]
        query["dbpedia_entities"] = {
            "$elemMatch":{
                "URI": "http://dbpedia.org/resource/"+dbpedia_entity
            }
        }

    print(query)
    posts = list(db["submissions"].find(query,{"_id":0}))

    return jsonify(posts)

@app.route("/contributors")
def get_contributors():

    query = [{
	"$match": {
            "subreddit": "r/NEET"
	}
    }, {
	"$group": {
            "_id": "$author_name",
          		"count": {
                            "$sum": "$count"
                        }
	}
    }, {

	"$sort": {
            "count": -1
	}
    }]

    users = list(db["submissions_count"].aggregate(query))

    return jsonify(users)

@app.route('/contributor')
def get_contributor():
    name = request.args["name"]

    query = [{
	"$match": {
            "subreddit": "r/NEET",
          		"author_name": name
	}
    }, {
	"$group": {
            "_id": {
                "day": "$_id.day",
                "month": "$_id.month",
            		  "year": "$_id.year",
            		  "type": "$_id.type"
            },
          		"count": {
                "$sum": "$count"
            },
            "date": {
                "$first": "$date"
            }
	}
    }, {
	"$sort": {
            "date": 1
	}
    }]

    data = list(db["submissions_count"].aggregate(query))

    comments = list(filter(lambda x: x["_id"]["type"]=="comment",data))
    posts = list(filter(lambda x: x["_id"]["type"]=="post",data))

    return jsonify({
        "comments":comments,
        "posts":posts
    })


if __name__ == '__main__':
    app.run(debug=True)
