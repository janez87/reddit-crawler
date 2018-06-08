from pymongo import MongoClient
import json
import sys
import gensim
from nltk import word_tokenize

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

'''submission = db["submissions"].find()

corpus = []

print("Creating the corpus")

for s in submission:
    if s["type"] == "post":
        text = s["title"]+' '+s["selftext"]
        corpus.append(gensim.utils.simple_preprocess(text))
    else:
        corpus.append(gensim.utils.simple_preprocess(s["body"]))


print("Training the model")
model = gensim.models.Word2Vec(corpus)

print("Saving the model")
model.save("neet_word_embedding.bin")

print("Done")'''

model = gensim.models.Word2Vec.load('neet_word_embedding.bin')

w = model.most_similar(positive=['library'])

print(w)
