# C:\Hackathon\print_latest_schema.py
from pymongo import MongoClient
from src.config import config
import json, sys

try:
    client = MongoClient(config.MONGO_URI)
    db = client[config.DATABASE_NAME]
    doc = db['schema_registry'].find({"source_id":"test_source"}).sort("created_at", -1).limit(1)
    d = next(doc, None)
    print(json.dumps(d, default=str, indent=2))
except Exception as e:
    print("ERROR:", e)
    sys.exit(2)
finally:
    try:
        client.close()
    except:
        pass
