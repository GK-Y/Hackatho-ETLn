from pymongo import MongoClient
from bson import json_util
import re, json

client = MongoClient("mongodb://hackathon:password123@localhost:27017/?authSource=admin")
db = client["hackathon_db"]
coll = db["data_test_source"]

cursor = coll.find().limit(50)
bad = []
for doc in cursor:
    for k in doc.keys():
        if isinstance(k, str) and (k.strip().startswith('{') or ('"' in k and ":" in k)):
            bad.append(doc)
            break

print("Found", len(bad), "docs with suspicious keys (showing up to 10):")
for d in bad[:10]:
    print(json.dumps(json.loads(json_util.dumps(d)), indent=2))
