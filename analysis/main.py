import sys
import praw
from pymongo import MongoClient
import json

sys.path.append("../")
from configuration import configuration

def serialize(submission):
    print(submission.author)

    s_dict = {}
    for v in vars(submission):
        if(v!='_reddit' and v!='subreddit'):

            if(v=="author"):
                s_dict["author_name"] =  submission.__dict__[v].name
                s_dict["author_id"] =  submission.__dict__[v].id
            else:
                s_dict[v] = submission.__dict__[v]

    return s_dict

reddit = praw.Reddit(client_id=configuration.CLIENT_ID,
                     client_secret=configuration.CLIENT_SECRET,
                     user_agent="oauth2-sample-app by /u/janez87",
                     username=configuration.REDDIT_USER,
                     password=configuration.REDDIT_PSW)

reddit.config.store_json_result = True

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

subreddit = reddit.subreddit('neet')

print(subreddit.display_name)  # Output: redditdev


authors = []

for p in subreddit.new(limit=1000):

    if p.author is not None:
        authors.append(p.author.name)


authors = set(authors)

print("Found ", len(authors),"redditors")

for a in authors:
    print("Crawling submission by ",a)
    author_submissions = list(reddit.redditor(a).new(limit=1000))

    print("Found",len(author_submissions),"submissions")
    for s in author_submissions:
        db["submissions"].save(serialize(s))

