from pymongo import MongoClient, DESCENDING
import json
import sys
from nltk import word_tokenize, pos_tag
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import string
import textrazor
from gensim import corpora, models, utils
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
doc_complete = []

print("Getting the submissions")
submissions = db["submissions"].find(
    {"selftext": {"$nin": ["[rimosso]", ""]}, "type": "post"})

for s in submissions:
    if s["type"] == "post":
        text = s["title"]+' '+s["selftext"]
        doc_complete.append(utils.simple_preprocess(text))
    else:
        doc_complete.append(s["body"])
# Build the bigram and trigram models
# higher threshold fewer phrases.
bigram = models.Phrases(doc_complete, min_count=5, threshold=100)
trigram = models.Phrases(bigram[doc_complete], threshold=100)

# Faster way to get a sentence clubbed as a trigram/bigram
bigram_mod = models.phrases.Phraser(bigram)
trigram_mod = models.phrases.Phraser(trigram)


def make_bigrams(texts):
    return bigram_mod[texts] 


def make_trigrams(texts):
    return [trigram_mod[bigram_mod[doc]] for doc in texts]

def clean(doc):
    stop_free = [i for i in doc if i not in stop]

    punc_free = [ch for ch in stop_free if ch not in exclude]

    data_words_bigrams = make_bigrams(punc_free)

    pos_tagged = pos_tag(data_words_bigrams)

    to_consider = list(filter(lambda x: x[1] not in [
                       'IN', 'CD', 'MD', 'FW', 'SYM'], pos_tagged))

    to_consider = list(map(lambda x: x[0],to_consider))

    to_consider = list(filter(lambda x: x not in [
                       'neet', 'im', 'irl', "すうふん", "ddfghdhfghfgh", "sᴜᴘᴇʀ_ᴅᴏɴɢ", "scho", "test", "testtest"], to_consider))

    normalized = [lemma.lemmatize(word) for word in to_consider]
    return normalized

    
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

print("Cleaning the submissions")
doc_clean = [clean(doc) for doc in doc_complete]

print(doc_complete[0])
print(doc_clean[0])

print("Creating the dictionary")
dictionary = corpora.Dictionary(doc_clean)

print(len(dictionary))
print("Creating the BOW representation")
corpus = [dictionary.doc2bow(doc) for doc in doc_clean]

#lda_model = models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, num_topics=15, random_state=100,
#                                     update_every=1, chunksize=250, passes=10, alpha='auto', per_word_topics=True)

#doc_lda = lda_model[corpus]
#print(lda_model.print_topics())

'''tfidf_model = models.TfidfModel(corpus, id2word=dictionary)

t_corpus = tfidf_model[corpus]
print("Creating lda models and coherence")
model_list, coherence_values = compute_coherence_values(
    dictionary=dictionary, corpus=corpus, texts=doc_clean, start=18, limit=28, step=1)

# Show graph
limit = 28
start = 18
step = 1
x = range(start, limit, step)
plt.plot(x, coherence_values)
plt.xlabel("Num Topics")
plt.ylabel("Coherence score")
plt.legend(("coherence_values"), loc='best')
plt.show()'''

mallet_path = "../models/mallet-2.0.8/bin/mallet"
model = models.wrappers.LdaMallet(
    mallet_path, corpus=corpus, num_topics=22, id2word=dictionary)
doc_lda = model[corpus]
print(model.show_topics())


'''
lda_model = models.ldamodel.LdaModel(corpus=corpus, id2word=dictionary, num_topics=10, random_state=100,
                                            update_every=1, chunksize=250, passes=10, alpha='auto', per_word_topics=True)

doc_lda = lda_model[corpus]
print(lda_model.print_topics())

# Compute Perplexity
# a measure of how good the model is. lower the better.
print('\nPerplexity: ', lda_model.log_perplexity(corpus))

# Compute Coherence Score
coherence_model_lda = models.CoherenceModel(
    model=lda_model, texts=doc_clean, dictionary=dictionary, coherence='c_v')
coherence_lda = coherence_model_lda.get_coherence()
print('\nCoherence Score: ', coherence_lda)

tfidf_model = models.TfidfModel(corpus, id2word=dictionary)

lda_model = models.ldamodel.LdaModel(tfidf_model[corpus], id2word=dictionary, num_topics=10, random_state=100,
                                            update_every=1, chunksize=250, passes=10, alpha='auto', per_word_topics=True)

doc_lda = lda_model[corpus]
print(lda_model.print_topics())

# Compute Perplexity
# a measure of how good the model is. lower the better.
print('\nPerplexity: ', lda_model.log_perplexity(corpus))

# Compute Coherence Score
coherence_model_lda = models.CoherenceModel(
    model=lda_model, texts=doc_clean, dictionary=dictionary, coherence='c_v')
coherence_lda = coherence_model_lda.get_coherence()
print('\nCoherence Score: ', coherence_lda)
'''
