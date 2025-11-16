# test_mongo.py
import pymongo
from pymongo.errors import PyMongoError

# Two URIs we want to test
uris = {
    "admin_auth": "mongodb://hackathon:password123@localhost:27017/?authSource=admin",
    "app_user_auth": "mongodb://hackathon:password123@localhost:27017/hackathon_db?authSource=hackathon_db"
}

print("\n==============================")
print("  MongoDB Connection Tester")
print("==============================\n")

for name, uri in uris.items():
    print(f"\nTesting {name}:\nURI = {uri}")

    try:
        # short timeout = faster failures
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)

        # try ping
        client.admin.command("ping")
        print("  ✔ Connection SUCCESS")

        # Show authenticated users (optional)
        try:
            status = client.admin.command({"connectionStatus": 1})
            users = status.get("authInfo", {}).get("authenticatedUsers", [])
            print("  ✔ Authenticated users:", users)
        except Exception as e:
            print("  (unable to fetch authenticated users)", e)

        client.close()

    except PyMongoError as e:
        print("  ✘ Connection FAILED")
        print("    Error:", repr(e))
