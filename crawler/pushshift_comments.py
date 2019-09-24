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

for s in comments_gen:

    to_save = s.d_
    to_save["type"] = "comment"

    print(to_save)

    db["depression_push"].insert_one(to_save)


print("Done")