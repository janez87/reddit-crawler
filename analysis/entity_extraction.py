from pymongo import MongoClient, DESCENDING
import json
import sys
from nltk.tag.stanford import StanfordNERTagger
from nltk import word_tokenize
import textrazor

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

submissions = list(db["submissions"].find({"entities": {
                   "$exists": False}, 
                   "type": "comment", 
                   "subreddit_name_prefixed": "r/NEET"
                   }
                ).sort("created_at",DESCENDING).limit(500))

textrazor.api_key = configuration.API_KEY

client = textrazor.TextRazor(extractors=["entities", "topics"])

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
        response = client.analyze(text)

        print("Entities found")
        entities = []
        for entity in response.entities():
            print(entity.id, entity.relevance_score, entity.confidence_score, entity.freebase_types)
            entities.append({
                "id":entity.id,
                "relevance_score":entity.relevance_score,
                "confidence_score":entity.confidence_score,
                "freebase_type": entity.freebase_types,
                "dbpedia_type": entity.dbpedia_types,
                "matched_positions": entity.matched_positions,
                "matched_words": entity.matched_words,
                "matched_text": entity.matched_text,
                "data": entity.data
            })
        
        print("Topics found")
        topics = []
        for topic in response.topics():
            print(topic.label, topic.score,
                topic.wikipedia_link, topic.wikidata_id)
            topics.append({
                "label":topic.label,
                "score":topic.score,
                "wikipedia_link": topic.wikipedia_link,
                "wikidata_id":topic.wikidata_id
            })

        print("Saving the results")
        db["submissions"].update({"_id": submissions[i]["_id"]},{"$set":{"entities": entities, "topics": topics}})
        print("==========================================================")
    except textrazor.TextRazorAnalysisException as e:
        print(e)
        continue

