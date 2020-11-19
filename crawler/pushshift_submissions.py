from pymongo import MongoClient
import sys
sys.path.append("../")
from configuration import configuration
import datetime as dt
from psaw import PushshiftAPI

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

api = PushshiftAPI()

start_epoch=int(dt.datetime(2019, 1, 1).timestamp())

end_epoch=int(dt.datetime(2019, 12, 31).timestamp())


gen = api.search_submissions(subreddit="NEET", after=start_epoch, before=end_epoch)

cache = []

for s in gen:

    to_save = s.d_
    to_save["type"] = "post"

    cache.append(to_save)

    if len(cache)>configuration.LIMIT:
        print("Saving a batch of posts")

        db["neet_pre_covid"].insert_many(cache)
        cache=[]

if len(cache)>0:
    db["neet_pre_covid"].insert_many(cache)

print("Done")