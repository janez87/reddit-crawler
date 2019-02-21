from pymongo import MongoClient, DESCENDING
import json
import sys
from nltk import word_tokenize, pos_tag
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer
import string
import gensim
from gensim import corpora, models, utils
import pyLDAvis
import pyLDAvis.gensim  # don't skip this
import matplotlib.pyplot as plt
import re
import textblob
import spacy


sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

stop = set(stopwords.words('english'))
lemma = WordNetLemmatizer()

def sanitize_text(text):
    """
    Returns text after removing unnecessary parts.
    
    """

    _text = " ".join([
        l for l in text.strip().split("\n") if (
            not l.strip().startswith("&gt;")
        )
    ])

    _text = _text.lower()

    substitutions = [
        (r"\[(.*?)\]\((.*?)\)", r""),   # Remove links from Markdown
        (r"[\"](.*?)[\"]", r""),    # Remove text within quotes
        (r" \'(.*?)\ '", r""),      # Remove text within quotes
        (r"\.+", r". "),        # Remove ellipses
        (r"\(.*?\)", r""),        # Remove text within round brackets
        (r"&amp;", r"&"),         # Decode HTML entities
        (r"http.?:\S+\b", r" ")     # Remove URLs
    ]
    for pattern, replacement in substitutions:
      _text = re.sub(pattern, replacement, _text, flags=re.I)
    
    return _text


def clean_up(text):

    substitutions = [
        (r"\b(ive|i've)\b", "i have"),
        (r"\b(im|i'm)\b", "i am"),
        (r"\b(id|i'd)\b", "i would"),
        (r"\b(i'll)\b", "i will"),
        (r"\bbf|b/f\b", "boyfriend"),
        (r"\bgf|g/f\b", "girlfriend"),
        (r"\byoure\b", "you are"),
        (r"\b(dont|don't)\b", "do not"),
        (r"\b(didnt|didn't)\b", "did not"),
        (r"\b(wasnt|wasn't)\b", "was not"),
        (r"\b(isnt|isn't)\b", "is not"),
        (r"\b(arent|aren't)\b", "are not"),
        (r"\b(werent|weren't)\b", "were not"),
        (r"\b(havent|haven't)\b", "have not"),
        (r"\b(couldnt|couldn't)\b", "could not"),
        (r"\b(hadnt|hadn't)\b", "had not"),
        (r"\b(wouldnt|wouldn't)\b", "would not"),
        (r"\bgotta\b", "have to"),
        (r"\bgonna\b", "going to"),
        (r"\bwanna\b", "want to"),
        (r"\b(kinda|kind of)\b", ""),
        (r"\b(sorta|sort of)\b", ""),
        (r"\b(dunno|donno)\b", "do not know"),
        (r"\b(cos|coz|cus|cuz)\b", "because"),
        (r"\bfave\b", "favorite"),
        (r"\bhubby\b", "husband"),
        (r"\bheres\b", "here is"),
        (r"\btheres\b", "there is"),
        (r"\bthats\b", "that is"),
        (r"\bwheres\b", "where is"),
        # Common acronyms, abbreviations and slang terms
        (r"\birl\b", "in real life"),
        (r"\biar\b", "in a relationship"),
        (r"\btotes\b", "totally"),
        (r",", " and "),
        # Remove fluff phrases
        (r"\b(btw|by the way)\b", ""),
        (r"\b(tbh|to be honest)\b", ""),
        (r"\b(imh?o|in my( humble)? opinion)\b", ""),
        # Default POS tagger seems to always tag "like"
        # (and sometimes "love") as a noun - this is a bandaid fix for now
        (r"\bprefer\b", ""),
        (r"\b(like|love)\b", "prefer"),
    ]

    for pattern, replacement in substitutions:
      text = re.sub(pattern, replacement, text, flags=re.I)

    text = " ".join([i for i in text.split() if i not in stop])

    return text


def lemmatization(texts, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
    """https://spacy.io/api/annotation"""
    texts_out = []
    for sent in texts:
        doc = nlp(" ".join(sent))
        texts_out.append(
            [token.lemma_ for token in doc if token.pos_ in allowed_postags])
    return texts_out

NUM_TOPICS = 10
submissions = list(db["submissions"].find({"subreddit_name_prefixed":"r/NEET"}, { "body": 1, "selftext": 1}))

doc_clean = []
print("Cleaning the submissions")
for s in submissions:
    
    text = s["body"] if "body" in s else s["selftext"]

    text = sanitize_text(text)

    text = clean_up(text)

    text = " ".join(lemma.lemmatize(word) for word in text.split())

    doc_clean.append(text.split())


# Build the bigram and trigram models
# higher threshold fewer phrases.
bigram = gensim.models.Phrases(doc_clean, min_count=5, threshold=100)
trigram = gensim.models.Phrases(bigram[doc_clean], threshold=100)

# Faster way to get a sentence clubbed as a trigram/bigram
bigram_mod = gensim.models.phrases.Phraser(bigram)
trigram_mod = gensim.models.phrases.Phraser(trigram)

print("Creating the matrix")
dictionary = corpora.Dictionary(doc_clean)

doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]

print("Performing LDA")
# Creating the object for LDA model using gensim library
Lda = models.ldamodel.LdaModel

# Running and Trainign LDA model on the document term matrix.
ldamodel = Lda(doc_term_matrix, num_topics=10, id2word=dictionary)

print("Performing LSI")
lsi_model = models.LsiModel(
    corpus=doc_term_matrix, num_topics=NUM_TOPICS, id2word=dictionary)

print("LDA Model:")

for idx in range(NUM_TOPICS):
    # Print the first 10 most representative topics
    print("Topic #%s:" % idx, ldamodel.print_topic(idx, 10))

print("=" * 20)

print("LSI Model:")

for idx in range(NUM_TOPICS):
    # Print the first 10 most representative topics
    print("Topic #%s:" % idx, lsi_model.print_topic(idx, 10))

print("=" * 20)
