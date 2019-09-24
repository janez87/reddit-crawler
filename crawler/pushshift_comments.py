from pymongo import MongoClient
import sys
sys.path.append("../")
from configuration import configuration

from psaw import PushshiftAPI

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

api = PushshiftAPI()


comments_gen = api.search_comments(subreddit="depression")

cache = []

for s in comments_gen:

    to_save = s.d_
    to_save["type"] = "comment"


    cache.append(to_save)

    if len(cache) > configuration.LIMIT:
        print("Saving a batch of comments")
        db["depression_push"].insert_many(cache)
        cache = []

if len(cache) > 0:
    db["depression_push"].insert_many(cache)


print("Done")