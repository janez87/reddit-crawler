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

for s in gen:

    to_save = s.d_
    to_save["type"] = "post"

    print(to_save)

    db["depression_push"].insert_one(to_save)


print("Done")