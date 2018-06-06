#system modules
import datetime
import sys

#external modules
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
        "$match":{
            "subreddit":"r/NEET"
        }
    }
    group = {
        "$group":{
            "_id":{
                "year":"$_id.year",
                "month":"$_id.month",
                "day":"$_id.day"
            },
            "count": {
                "$sum": "$count"
            }
        }
    
    }

    sort = {
       "$sort":{
           "_id":1
       }
    }

    data = list(db["submissions_count"].aggregate([match,group,sort]))
    return jsonify(data)

@app.route('/daily')
def get_daily_pattern():
    match = {
        "$match": {
            "subreddit": "r/NEET"
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
        "$sort":{
            "_id.hour":-1
        }
    }

    data = list(db["submissions_count"].aggregate([match,group,sort]))
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
        "$sort":{
            "count":-1
        }
    }

    limit = {
        "$limit":50
    }

    data = list(db["submissions"].aggregate([match, group, sort,limit]))
    return jsonify(data)



if __name__ == '__main__':
    app.run(debug=True)
