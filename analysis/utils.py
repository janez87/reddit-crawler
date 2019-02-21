import sys
from pymongo import MongoClient
import csv

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

project = {
    "title":1,
    "selftext":1,
    "subreddit_name_prefixed":1,
    "id":1,
    "author_name":1,
    "num_comments":1,
    "score":1,
    "created_utc":1,
    "permalink":1
}

project_comment = {
    "author_name":1,
    "id":1,
    "parent_id":1,
    "subreddit_name_prefixed":1,
    "body":1,
    "created_utc":1,
    "score":1,
    "controversiality":1,
    "permalink":1
}
submissions = list(db["submissions"].find({"type":"comment"},project_comment))


for s in submissions:
    s["body"] = s["body"].replace("\n", " ")
    s["parent_id"] = s["parent_id"].split("_")[1]


with open("comments.csv","w") as csvfile:
    writer = csv.writer(csvfile)

    #writer.writerow(["title","selftext","subreddit_name_prefixed","id","author_name","num_comments","score","created_utc","permalink"])
    writer.writerow(["id","parent_id","created_utc","body","author_name","permalink","score","controversiality","subreddit_name_prefixed"])
    for s in submissions:
        #writer.writerow([s["title"], s["selftext"],s["subreddit_name_prefixed"],s["id"],s["author_name"],s["num_comments"],s["score"],s["created_utc"],s["permalink"]])
        writer.writerow([s["id"],s["parent_id"],s["created_utc"],s["body"],s["author_name"],s["permalink"],s["score"],s["controversiality"],s["subreddit_name_prefixed"]])

print("done")