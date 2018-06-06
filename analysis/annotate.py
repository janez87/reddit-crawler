from pymongo import MongoClient
import json
import sys
from nltk.tag.stanford import StanfordNERTagger
from nltk import word_tokenize
import textrazor
import datetime
import pytz

sys.path.append("../")
from configuration import configuration

client = MongoClient(
    configuration.DB_HOST, configuration.DB_PORT)

db = client[configuration.DB_NAME]

submissions = list(db["submissions"].find())

for s in submissions:

    print("Adding the date")
    created_at = datetime.datetime.utcfromtimestamp(s["created_utc"])
    tz = pytz.timezone('US/Central')
    created_at = created_at.astimezone(tz)

    #need to convert the date to string to save the timezone
    create_at_str = str(created_at)

    # need to remove the last : in the timezone format
    c = create_at_str.rfind(':')
    create_at_str = create_at_str[:c]+create_at_str[c+1:]
    created_at_timezone = datetime.datetime.strptime(create_at_str,'%Y-%m-%d %H:%M:%S%z')
    print(created_at_timezone)

    print("Adding type (Comment or Post)")
    submission_type = "comment" if "body" in s else "post"
    print(submission_type)

    print("Saving")
    db["submissions"].update({"_id":s["_id"]},{"$set":{"created_at":created_at_timezone,"type":submission_type,"created_at_str":str(created_at_timezone)}})






