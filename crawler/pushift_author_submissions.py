from pymongo import MongoClient
import sys
sys.path.append("../")
from configuration import configuration
import datetime as dt
from psaw import PushshiftAPI

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]
COLLECTION = "neet_covid_2"

api = PushshiftAPI()

start_epoch=int(dt.datetime(2020, 1, 1).timestamp())

end_epoch=int(dt.datetime(2020, 12, 31).timestamp())

ignore = ["AutoModerator", "[deleted]"]

queried = db[COLLECTION].distinct("author",{
	"subreddit":{
		"$ne":"NEET"
	},
	"type":"post"
})

auhtors = db[COLLECTION].distinct("author",{"author":{
    "$nin":queried+ignore
}})


for a in auhtors:
    print(a)
    gen = api.search_submissions(author=a, subreddit="!NEET", after=start_epoch, before=end_epoch)

    cache = []

    for s in gen:

        to_save = s.d_
        to_save["type"] = "post"

        cache.append(to_save)

        if len(cache)>configuration.LIMIT:
            print("Saving a batch of posts")

            db[COLLECTION].insert_many(cache)
            cache=[]

    if len(cache)>0:
        print("Saving the batch of posts")
        db[COLLECTION].insert_many(cache)

print("Done")