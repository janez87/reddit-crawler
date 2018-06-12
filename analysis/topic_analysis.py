from pymongo import MongoClient, DESCENDING
import json
import sys
from nltk import word_tokenize, pos_tag
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import string
import textrazor
from gensim import corpora, models
import pyLDAvis
import pyLDAvis.gensim  # don't skip this
import matplotlib.pyplot as plt


sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

stop = set(stopwords.words('english'))
exclude = set(string.punctuation)
lemma = WordNetLemmatizer()

def clean(doc):
    stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)

    pos_tagged = pos_tag(punc_free.split())

    to_consider = list(filter(lambda x: x[1] not in ['IN','CD','MD'],pos_tagged))

    to_consider = list(map(lambda x: x[0],to_consider))

    to_consider = list(filter(lambda x: x not in ['neet','im'], to_consider))

    normalized = " ".join(lemma.lemmatize(word) for word in to_consider)
    return normalized


def create_ft_distribution(dictionary, corpus):
    data = {}
   
    for i,d in enumerate(dictionary):
        df = dictionary.dfs[i]
        data[dictionary[d]] = df
    
    names = list(data.keys())
    values = list(data.values())

    fig, axs = plt.subplots(1, 3, figsize=(9, 3), sharey=True)
    axs[0].bar(names, values)
    axs[1].scatter(names, values)
    axs[2].plot(names, values)
    fig.suptitle('Categorical Plotting')
    fig.savefig("chart.pdf")
    

doc_complete = []

print("Getting the submissions")
submissions = db["submissions"].find({"subreddit_name_prefixed":"r/NEET","type":"post"})

for s in submissions:
    if s["type"] == "post":
        text = s["title"]+' '+s["selftext"]
        doc_complete.append(text)
    else:
        doc_complete.append(s["body"])

print("Cleaning the submissions")
doc_clean = [clean(doc).split() for doc in doc_complete]

print("Creating the dictionary")
dictionary = corpora.Dictionary(doc_clean)

print(len(dictionary))
print("Creating the BOW representation")
doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]

tfidf = models.TfidfModel(doc_term_matrix, id2word=dictionary)

create_ft_distribution(dictionary,doc_term_matrix)
print("Filtering low tdfidf words")
low_value = 0.1
low_value_words = []
for bow in doc_term_matrix:
    low_value_words += [id for id, value in tfidf[bow] if value < low_value]

dictionary.filter_tokens(bad_ids=low_value_words)
print(len(dictionary))
doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]

ldas = []
cvs = []

print("Creating the HDP Model")
hdp = models.HdpModel(corpus=doc_term_matrix,id2word=dictionary)
topics = hdp.print_topics()

for t in topics:
    print(t)

'''for num_topics in range(2,40,6):
    Lda = models.ldamodel.LdaModel
    print("Creating the model for",num_topics,"topics")
    ldamodel = Lda(doc_term_matrix, num_topics=num_topics, id2word=dictionary)
    coherencemodel = models.CoherenceModel(
        model=ldamodel, texts=doc_clean, dictionary=dictionary, coherence='c_v')
    cvs.append(coherencemodel.get_coherence())

x = range(2, 40, 6)
plt.plot(x, cvs)
plt.xlabel("Num Topics")
plt.ylabel("Coherence score")
plt.legend(("coherence_values"), loc='best')
plt.show()'''
