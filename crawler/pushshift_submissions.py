from pymongo import MongoClient
import sys
sys.path.append("../")
from configuration import configuration

from psaw import PushshiftAPI

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

api = PushshiftAPI()

gen = api.search_submissions(subreddit="depression")

cache = []

for s in gen:

    to_save = s.d_
    to_save["type"] = "post"

    print(to_save)

    cache.append(to_save)

    if len(cache)>configuration.LIMIT:
        print("Saving a batch of posts")

        db["depression_push"].insert_many(cache)
        cache=[]

if len(cache)>0:
    db["depression_push"].insert_many(cache)

print("Done")