# import os
# import urllib.parse
# from pymongo import MongoClient

# MONGO_USER = os.getenv("MONGO_USER", "user1")
# MONGO_PASS = urllib.parse.quote_plus(os.getenv("MONGO_PASS", "cdac@123#"))
# MONGO_HOST = os.getenv("MONGO_HOST", "10.226.53.238")
# MONGO_DB = os.getenv("MONGO_DB", "textdata")

# mongo_uri = f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:27017/{MONGO_DB}"
# client = MongoClient(mongo_uri)

# db = client[MONGO_DB]
# scrapped_data = db["scrappedPosts"]
# sentiment_data = db["socialMediaSentiment"]

import os
import urllib.parse
from pymongo import MongoClient

MONGO_USER = os.getenv("MONGO_USER", "user1")
MONGO_PASS = urllib.parse.quote_plus(os.getenv("MONGO_PASS", "cdac012654"))
MONGO_HOST = os.getenv("MONGO_HOST", "65.1.218.101")
MONGO_DB = os.getenv("MONGO_DB", "textdata")

mongo_uri = (
    f"mongodb://{MONGO_USER}:{MONGO_PASS}@{MONGO_HOST}:27017/"
    f"?authSource={MONGO_DB}&authMechanism=SCRAM-SHA-256"
)

client = MongoClient(mongo_uri)

db = client[MONGO_DB]
scrapped_data = db["scrappedPosts"]
sentiment_data = db["socialMediaSentiment"]
