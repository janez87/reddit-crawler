from pymongo import MongoClient
import json
from nltk.tag.stanford import StanfordNERTagger
from nltk import word_tokenize, pos_tag
from nltk.corpus import sentiwordnet as swn
from nltk.corpus.reader.wordnet import WordNetError
import numpy as np
import textrazor
import datetime
import pytz
import sys

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

submissions = list(db["submissions"].find())

converstion_tags = {
    "NN":"n",
    "NNS":"n",
    "VERB":"v",
    "ADJ":"a",
    "JJ":"a",
    "ADV":"r",
    "VBZ":"v",
    "VB":"v",
    "VBN":"v",
    "VBG":"v",
    "VBD":"v"   
}

for s in submissions:
    text = ""

    if s["type"] == "comment":
        text=s["body"]
    else:
        text=s["title"]+" "+s["selftext"]

    token = word_tokenize(text)
    tagged = pos_tag(token)

    print(text)
    positive_score = []
    negative_score = []
    for t in tagged:
        if t[1] not in converstion_tags:
            continue

        search=t[0]+"."+converstion_tags[t[1]]+".01"

        try:
            score = swn.senti_synset(search)
            positive_score.append(score.pos_score())
            negative_score.append(score.neg_score())
        except WordNetError as e:
            pass

    print(np.average(positive_score))
    print(np.average(negative_score))

    print("Saving")
    db["submissions"].update({"_id": s["_id"]}, {
        "$set": {"p_score": positive_score,"n_score":negative_score}})
