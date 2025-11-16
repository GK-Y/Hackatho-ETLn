import json
from pymongo import MongoClient
from bson import json_util

"""
Targeted repair for documents with malformed JSON-like keys.
This script:
  1. Finds keys that look like broken JSON fragments.
  2. Attempts to reconstruct valid key-value pairs.
  3. Unsets the malformed keys and sets the cleaned fields.
  4. Writes a full repair report.
"""

client = MongoClient("mongodb://hackathon:password123@localhost:27017/?authSource=admin")
db = client["hackathon_db"]
coll = db["data_test_source"]

def looks_like_broken_json_key(k: str) -> bool:
    """
    Heuristic: suspicious keys usually start with {, ", or contain : without being normal field names.
    """
    if not isinstance(k, str):
        return False
    if k.strip().startswith("{"):
        return True
    if k.strip().startswith("\""):
        return True
    if ":" in k and not k.isidentifier():
        return True
    if k.count("\"") >= 2:
        return True
    return False

def attempt_repair_key(k: str):
    """
    Try to convert a malformed key like:
        "{\"id\": 4, \"name\": \"Dave\"}"
    into a dict: { "id": 4, "name": "Dave" }.
    Returns None if cannot parse.
    """
    try:
        txt = k.strip()
        if not txt.startswith("{"):
            txt = "{" + txt
        if not txt.endswith("}"):
            txt = txt + "}"

        # attempt JSON load
        d = json.loads(txt)
        if isinstance(d, dict):
            return d
    except:
        return None
    return None

repaired = []
failed = []

cursor = coll.find({})
for doc in cursor:
    malformed_keys = [k for k in doc.keys() if looks_like_broken_json_key(k) and k != "_id"]
    if not malformed_keys:
        continue

    updates = {"$unset": {}, "$set": {}}
    doc_failed = False

    for bad_key in malformed_keys:
        repaired_obj = attempt_repair_key(bad_key)
        if repaired_obj:
            # merge fields
            for kk, vv in repaired_obj.items():
                updates["$set"][kk] = vv
            updates["$unset"][bad_key] = ""
        else:
            doc_failed = True
            updates["$unset"][bad_key] = ""

    try:
        coll.update_one({"_id": doc["_id"]}, updates)
        repaired.append({"_id": str(doc["_id"]), "updates": updates})
    except Exception as e:
        failed.append({"_id": str(doc["_id"]), "error": str(e)})

# write report
report = {
    "repaired_count": len(repaired),
    "failed_count": len(failed),
    "repaired": repaired,
    "failed": failed
}

with open("repair_special_keys_report.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(report, indent=2))

print(f"Repaired {len(repaired)} docs. Failed {len(failed)} docs. Report saved to repair_special_keys_report.json.")
