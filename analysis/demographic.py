from pymongo import MongoClient
import json
from nltk.tag.stanford import StanfordNERTagger
from nltk import word_tokenize, pos_tag
from nltk import RegexpParser
from textblob import TextBlob, Word
from textblob.taggers import PatternTagger
import csv 

import numpy as np
import textrazor
import datetime
import pytz
import sys
import re

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

authors = db["submissions"].distinct("author_name")

#authors = ["aldjfh"]

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

    return text

def count_slang(text):
    
    slangs = [
        r"\b(im|i'm)\b", 
        r"\b(id|i'd)\b",
        r"\b(i'll)\b", 
        r"\bbf|b/f\b",
        r"\bgf|g/f\b",
        r"\byoure\b",
        r"\b(dont|don't)\b",
        r"\b(didnt|didn't)\b",
        r"\b(wasnt|wasn't)\b",
        r"\b(isnt|isn't)\b",
        r"\b(arent|aren't)\b",
        r"\b(werent|weren't)\b",
        r"\b(havent|haven't)\b", 
        r"\b(couldnt|couldn't)\b",
        r"\b(hadnt|hadn't)\b",
        r"\b(wouldnt|wouldn't)\b",
        r"\bgotta\b", 
        r"\bgonna\b", 
        r"\bwanna\b", 
        r"\b(kinda|kind of)\b",
        r"\b(sorta|sort of)\b",
        r"\b(dunno|donno)\b",
        r"\b(cos|coz|cus|cuz)\b",
        r"\bfave\b",
        r"\bhubby\b",
        r"\bheres\b",
        r"\btheres\b",
        r"\bthats\b", 
        r"\bwheres\b",
        # Common acronyms, abbreviations and slang terms
        r"\birl\b",
        r"\biar\b",
        r"\btotes\b",
        # Remove fluff phrases
        r"\b(btw|by the way)\b",
        r"\b(tbh|to be honest)\b",
        r"\b(imh?o|in my( humble)? opinion)\b",
        # Default POS tagger seems to always tag "like"
        # (and sometimes "love") as a noun - this is a bandaid fix for now
        r"\bprefer\b",
        r"\b(like|love)\b",
    ]

    count = 0
    for pattern in slangs:
    
      count += len(re.findall(pattern, text))

    return count

def parse_csv(file):

    rows = []
    with open(file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for r in csv_reader:
            rows.append(r)
    
    return rows

def create_chunker():
  # Should _N include conjunctions?
  grammar = r"""
    
     #I am 20, I turn 20..
    AGE:
      {<PRP><VBP><CD>}

    AGE2:
      {<IN><DT>(<CD><NNS><JJ>)?(<NN>|<JJ><NN>)}

    # adverb* verb adverb* 
    # - really think, strongly suggest, look intensely
    _VP:  
      {<RB.*>*<V.*>+<RB.*>*}

    # determiner adjective noun(s)
    # - a beautiful house, the strongest fighter
    _N0:
      {(<DT>*<JJ.*>*<NN.*>+<JJ.*>*(?!<POS>))*}
    _N:
      {<_N0>+}   

    # noun to/in noun 
    # - newcomer to physics, big fan of Queen, newbie in gaming
    _N_PREP_N:
      {<_N>((<TO>|<IN>)<_N>)+}

    # my adjective noun(s) 
    # - my awesome phone
    POSS:
      {<PRP\$><_N>}

    # I verb in* adjective* noun
    # - I am a great chef, I like cute animals
    # - I work in beautiful* New York, I live in the suburbs
    ACT1:
      {<PRP><_VP><IN>*<_N>}

    # Above + to/in noun
    # - I am a fan of Jaymay, I have trouble with flannel
    ACT2:
      {<PRP><_VP><IN>*<_N_PREP_N>}

    CONTEXT:
      {<PRP><_VP><RB>}
  """

  return RegexpParser(grammar)


pattern_tagger = PatternTagger()
chunker = create_chunker()


def parse_author(author, male_subreddits, female_subreddits, health_subreddits, sub_categories,health_terms,drug_terms):
    print(author)
    submissions = list(db["submissions"].find({"author_name":author},{"body":1,"selftext":1,"subreddit_name_prefixed":1,"type":1}))

    gender = []
    age = []
    education = []
    dropped = []
    slang_count = 0
    slang_per_sub = 0
    male = []
    female = []
    health_issues = []
    medication = []
    health_s = []
    submissions_topics = {}
    comment_topics = {}
    context = []
    
    for s in submissions:

        #if s["type"]=="comment":
        #    continue
        if s["type"] == "post":
            if s["subreddit_name_prefixed"] in male_subreddits:
                male.append(s["subreddit_name_prefixed"])
            if s["subreddit_name_prefixed"] in female_subreddits:
                female.append(s["subreddit_name_prefixed"])
            if s["subreddit_name_prefixed"] in health_subreddits:
                health_s.append(s["subreddit_name_prefixed"])
        
        c = None

        if s["subreddit_name_prefixed"] in sub_categories:
            c = sub_categories[s["subreddit_name_prefixed"]]

        #for c in categories:
        if c:
            if s["type"] == "comment":
                if c in comment_topics:
                    comment_topics[c] +=1
                else:
                    comment_topics[c] = 1
            else:
                if c in submissions_topics:
                    submissions_topics[c] += 1
                else:
                    submissions_topics[c] = 1

        text = s["body"] if "body" in s else s["selftext"]

        text = sanitize_text(text)
        
        count = count_slang(text)

        if count > 0:
            slang_per_sub+=1
            slang_count+=count

        text = clean_up(text)

        blob = TextBlob(text, pos_tagger=pattern_tagger)
        blob.correct()
        for sentence in blob.sentences:
            if not sentence.tags or not re.search(r"\b(i|my)\b", str(sentence), re.I):
                continue
            tree = chunker.parse(sentence.tags)

            for subtree in  tree.subtrees():   

                labels = []
                instances = {}
                age_label = get_age(subtree)
                if len(age_label)>0:
                    age.extend(age_label)
                    labels.append("AGE")
                    instances["age"] = age_label

                gender_label = get_gender(subtree)
                if len(gender_label) > 0:
                    gender.extend(gender_label)
                    labels.append("GENDER")
                    instances["gender"] = gender_label
                

                ed, drop = get_education(subtree)
                if len(ed) > 0:
                    education.extend(ed)
                    labels.append("EDUCATION")
                    instances["education"] = ed

                if len(drop) > 0:
                    dropped.extend(drop)
                    labels.append("EDUCATION_DROPPED")
                    instances["dropped"] = drop
               

                med, health = get_health(subtree,health_terms,drug_terms)

                if len(health) > 0:
                    health_issues.extend(health)
                    labels.append("HEALTH")
                    instances["health_issue"] = health

                if len(med) > 0:
                    medication.extend(med)
                    labels.append("MEDICATION")
                    instances["medication"] = med
                
                con = get_context(subtree)
                
                if len(con) > 0:
                    context.extend(con)
                    labels.append("CONTEXT")
                    instances["context"] = con

                if len(labels)>0:
                    phrase = " ".join([w.lower() for w, t in subtree.leaves()])
                    save_labeled_sentence(phrase, labels, author, instances,text)

            #for subtree in tree.subtrees(filter=lambda t: t.label() in ['AGE']):
                #phrase = [(w.lower(), t) for w, t in subtree.leaves()]
                #phrase_type = subtree.label()
                #print(phrase_type)
                #print(phrase)
    
    print(slang_count)
    print(slang_per_sub)

    return gender, male,female, age, education, dropped, slang_count, slang_per_sub,medication,health_issues,health_s,submissions_topics,comment_topics,context

def save_labeled_sentence(sentence,labels,author,instance,text):
    to_save = {
        "sentence":sentence,
        "labels":labels,
        "author":author,
        "instance":instance,
        "text":text
    }

    db["sentences_2"].save(to_save)
        
def get_age(subtree):

    ages = []

    if subtree.label() in ["ACT1", "ACT2","AGE"]:
        phrase = [(w.lower(), t) for w, t in subtree.leaves()]

        if len(phrase)< 2:
            return ages

        if phrase[0] != ("i","PRP") or phrase[1] != ("am","VBP"):
            return []

        age = phrase[2][0]

        if not age.isdigit():
            return []


        ages.append(age)

    return ages
    

def normalize_gender(word):
   
    if re.match(r"\b(girl|woman|female|lady|she)\b", word):
      return "female"
    elif re.match(r"\b(guy|man|male|he|dude|neckbeard|brat)\b", word):
      return "male"
    elif re.match(r"(trans|trangirl|transman|tgirl|transwoman)\b", word):
        return "trans"
    else:
      return None

def get_gender(subtree):

    genders = []

    if subtree.label() in ["ACT1", "ACT2"]:

        phrase = [(w.lower(), t) for w, t in subtree.leaves()]
        
        if len(phrase) < 2:
            return []

        if phrase[0] != ("i", "PRP") or phrase[1] != ("am", "VBP") or phrase[2] != ("a","DT"):
            return []
        
        gender_indicators = list(filter(lambda x: x[1]=="NN" or x[1]=="NNS",phrase))
        gender_indicators = list(
            map(lambda x: normalize_gender(x[0]), gender_indicators))
        gender_indicators = list(filter(lambda x: x is not None ,gender_indicators))

        genders = gender_indicators
    
    return genders

def get_education(subtree):

    educations_attained = []
    educations_dropped = []
    
    phrase = [(w.lower(), t) for w, t in subtree.leaves()]

    if len(phrase) < 2:
        return [],[]

    if phrase[0] == ("i", "PRP") and phrase[1][0] in ["graduated"]:
        gradudated = list(
            filter(lambda x: x[1] in ["JJ", "NN", "NNS"], phrase))
        educations_attained = gradudated
    elif phrase[0] == ("i", "PRP") and phrase[1][0] in ["dropped"]:
        dropped = list(
            filter(lambda x: x[1] in ["JJ","NN","NNS"], phrase))
        educations_dropped = dropped
    elif phrase[0] == ("i", "PRP") and re.match(r"(have|got|obtained)\b", phrase[1][0]):
        gained = list(
            filter(lambda x: re.match(r"degree|diploma",x[0]), phrase))
        educations_attained = gained
    elif phrase[0] == ("i", "PRP") and re.match(r"need\b", phrase[1][0]):
        dropped = list(
            filter(lambda x: re.match(r"degree|diploma", x[0]), phrase))
        educations_dropped = dropped
    else:

        phrase = [w.lower() for w, t in subtree.leaves()]

        if "diploma" in phrase:
            print(phrase)

        return [],[]
               
    educations_attained = list(map(lambda x: x[0],educations_attained))
    educations_dropped = list(map(lambda x: x[0], educations_dropped))

    return educations_attained, educations_dropped

def get_health(subtree,health_terms,drug_terms):

    medication = []
    issues = []

    if subtree.label() in ["ACT1","ACT2"]:
        phrase = [(w.lower(), t) for w, t in subtree.leaves()]

        if len(phrase)==0:
            return [],[]
        if phrase[0] == ("i", "PRP") and (phrase[1] == ("am", "VBP") or phrase[1] == ("have", "VBP")):
            issue = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS"] and x[0] in health_terms, phrase))
            issues = issue
        elif phrase[0] == ("i", "PRP") and phrase[1] == ("am", "VBP") and phrase[2][0]=="struggling":
            issue = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS"], phrase))
            issues = issue
        elif phrase[0] == ("i", "PRP") and phrase[1] == ("suffer", "VB"):
            issue = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS"], phrase))
            issues = issue
        elif phrase[0] == ("i", "PRP") and phrase[1][0] == "was" and phrase[2][0] == "diagnosed":
            issue = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS"], phrase))
            issues = issue
        elif phrase[0] == ("i", "PRP") and phrase[1][0] == "was" and phrase[2][0] == "put":
            med = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS"], phrase))
            medication = med
        elif (phrase[0] == ("i", "PRP") and phrase[1][0] == "am" and (phrase[2][0] == "taking" or phrase[2][0] == "using")) or (phrase[0] == ("i", "PRP") and phrase[1][0] == "take"):
            med = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS"] and x[0] in drug_terms, phrase))
            medication = med
        else:
            return [],[]
        
        medication = list(map(lambda x: x[0], medication))
        issues = list(map(lambda x: x[0], issues))
        

    return medication,issues

def get_context(subtree):

    context = []

    if subtree.label() in ["ACT1", "ACT2","CONTEXT"]:
        phrase = [(w.lower(), t) for w, t in subtree.leaves()]

        if len(phrase) == 0:
            return []
        if phrase[0] == ("i", "PRP") and phrase[1][0] == "live":
            print(phrase)
            context_term = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS","ADV","RB"], phrase))

            context = list(map(lambda x: x[0], context_term))
            print(context)
        if phrase[0] == ("i", "PRP") and phrase[1][0] == "am" and phrase[1][0] == "living":
            print(phrase)
            context_term = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS", "ADV", "RB"], phrase))

            context = list(map(lambda x: x[0], context_term))
            print(context)
    else:
         phrase = [(w.lower(), t) for w, t in subtree.leaves()]
         if len(phrase) < 3:
            return []
         if phrase[0] == ("i", "PRP") and phrase[1][0] == "live":
            print(phrase)
            context_term = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS", "ADV", "RB"], phrase))

            context = list(map(lambda x: x[0], context_term))
            print(context)
         if phrase[0] == ("i", "PRP") and phrase[1][0] == "am" and phrase[1][0] == "living":
            print(phrase)
            context_term = list(
                filter(lambda x: x[1] in ["JJ", "NN", "NNS", "ADV", "RB"], phrase))

            context = list(map(lambda x: x[0], context_term))
            print(context)

    return context

total = len(authors)
with_gender = 0
with_age = 0
with_education = 0
with_both = 0

subreddits = parse_csv("subreddits.csv")
health_terms = list(map(lambda x: x[0].lower(),parse_csv("health.csv"))) 
drug_terms = list(map(lambda x: x[0].lower(), parse_csv("drugs.csv")))

male_subreddits = []
female_subreddits = []

health_subreddits = []

sub_categories = {}

for s in subreddits:
    if s[-1] == "Female":
        female_subreddits.append("r/"+s[0])
    if s[-1] == "Male":
        male_subreddits.append("r/"+s[0])

    if s[-2] == "health_issue":
        health_subreddits.append("r/"+s[0])

    if s[1]=="Gaming":
        sub_categories["r/"+s[0]] = "Gaming"
    else:
        sub_categories["r/"+s[0]] = s[3]


for a in authors:
    gender, male_count, female_count, age, educations_attained, educations_dropped, slang_count, slang_per_sub, medication, health,health_s, submissions_topics, comment_topics, context = parse_author(
        a, male_subreddits, female_subreddits, health_subreddits,sub_categories,health_terms,drug_terms)

    print(gender, age, "education:",educations_attained, "dropped out",educations_dropped,"health",health,"medication",medication,"health subreddit",health_s)
    db["author_demographic_1"].update_one({"name": a}, {"$set":{
        "name": a,
        "gender": gender,
        "male_subreddits":male_count,
        "female_subreddits":female_count,
        "health_subreddit":health_s,
        "age": age,
        "education": educations_attained,
        "education_dropped": educations_dropped,
        "slang_count": slang_count,
        "slang_per_sub": slang_per_sub,
        "health":health,
        "medication":medication,
        "submission_topics":submissions_topics,
        "comments_topics":comment_topics,
        "context":context
    }},upsert=True)

    '''db["author_demographic"].save({
        "name":a,
        "gender":gender,
        "age":age,
        "education": educations_attained,
        "education_dropped":educations_dropped,
        "slang_count":slang_count,
        "slang_per_sub":slang_count
    })'''

    if len(gender)>0:
        with_gender+=1
    if len(age)>0:
        with_age+=1
    if len(educations_attained) or len(educations_dropped)>0:
        with_education+=1
    if len(age) > 0 and len(gender) > 0 and (len(educations_attained) or len(educations_dropped)):
        with_both+=1

print(total)
print(with_age)
print(with_gender)
print(with_education)
print(with_both)
