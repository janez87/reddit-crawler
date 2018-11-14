from pymongo import MongoClient, DESCENDING
import json
import sys
from nltk.tag.stanford import StanfordNERTagger
from nltk import word_tokenize
import spotlight

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

submissions = list(db["submissions"].find({"dbpedia_entities": {
                   "$exists": False}, 
                   }
                ))



for i in range(0,len(submissions)):

    if "body" in submissions[i]:
        # The submission is a comment
        text = submissions[i]["body"]
    else:
        # The sumbission is a post
        text = submissions[i]["title"] + " " + submissions[i]["selftext"]

    try:

        print("Analyzing text...")
        print(text)

        annotations = spotlight.annotate('http:/localhost:2222/annotate',text,confidence=0.4,support=20)

        print("Saving")
        db["submissions"].update({"_id":submissions[i]["_id"]},{"$set":{"dbpedia_entities":annotations}})

        
    except Exception as e:
        print(e)
        continue


print("Done")