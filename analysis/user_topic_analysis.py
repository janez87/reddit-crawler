from pymongo import MongoClient, DESCENDING
import json
import sys
from nltk import word_tokenize, pos_tag
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import string
import textrazor
from gensim import corpora, models, utils, matutils
import pyLDAvis
import pyLDAvis.gensim  # don't skip this
import matplotlib.pyplot as plt
from pprint import pprint

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]


def compute_coherence_values(dictionary, corpus, texts, limit, start=2, step=3):
    """
    Compute c_v coherence for various number of topics

    Parameters:
    ----------
    dictionary : Gensim dictionary
    corpus : Gensim corpus
    texts : List of input texts
    limit : Max num of topics

    Returns:
    -------
    model_list : List of LDA topic models
    coherence_values : Coherence values corresponding to the LDA model with respective number of topics
    """
    coherence_values = []
    model_list = []
    mallet_path = "../models/mallet-2.0.8/bin/mallet"
    for num_topics in range(start, limit, step):
        model = models.wrappers.LdaMallet(
            mallet_path, corpus=corpus, num_topics=num_topics, id2word=dictionary)
        model_list.append(model)
        coherencemodel = models.CoherenceModel(
            model=model, texts=texts, dictionary=dictionary, coherence='c_v')
        coherence_values.append(coherencemodel.get_coherence())

    return model_list, coherence_values

user_post_subreddit = list(db["submissions"].aggregate([{"$match": {"subreddit_name_prefixed": {"$ne": "r/NEET"},"type":"comment"}}, {

    "$project": {"author_name": 1, "subreddit_name_prefixed": 1}

}, {
	"$group": {
		"_id": "$author_name",
		"subreddit": {"$push": "$subreddit_name_prefixed"}
	}
},{
    "$match":{
        "subreddit.10":{"$exists":True}
    }
}]))

print(user_post_subreddit[0])
users = list(map(lambda x: x["subreddit"],user_post_subreddit))
print(len(users))
print("Creating the dictionary")
dictionary = corpora.Dictionary(users)
print(dictionary)

print("Creating the BOW representation")
corpus = [dictionary.doc2bow(doc) for doc in users]
print(len(corpus))
tfidf_model = models.TfidfModel(corpus, id2word=dictionary)

#t_corpus = tfidf_model[corpus]

#mallet_path = "../models/mallet-2.0.8/bin/mallet"
#lda_model = models.wrappers.LdaMallet(
 #   mallet_path, corpus=t_corpus, num_topics=44, id2word=dictionary)

#pprint(lda_model.show_topics(formatted=True))

# Compute Coherence Score
#coherence_model_lda = models.CoherenceModel(
#    model=lda_model, texts=users, dictionary=dictionary, coherence='c_v')
#coherence_lda = coherence_model_lda.get_coherence()
#print('Coherence Score: ', coherence_lda)

print("Creating lda models and coherence")
model_list, coherence_values = compute_coherence_values(
    dictionary=dictionary, corpus=corpus, texts=users, start=2, limit=10, step=1)

# Show graph
limit = 10
start = 2
step = 1
x = range(start, limit, step)
plt.plot(x, coherence_values)
plt.xlabel("Num Topics")
plt.ylabel("Coherence score")
plt.legend(("coherence_values"), loc='best')
plt.show()

for m, cv in zip(x, coherence_values):
    print("Num Topics =", m, " has Coherence Value of", round(cv, 4))
