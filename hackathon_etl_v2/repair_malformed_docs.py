# repair_malformed_docs.py
from pymongo import MongoClient
from bson import ObjectId, json_util
import json, re, traceback

client = MongoClient("mongodb://hackathon:password123@localhost:27017/?authSource=admin")
db = client["hackathon_db"]
coll = db["data_test_source"]

def try_reconstruct_and_parse(bad_key: str, bad_val: str):
    """
    Attempt to rebuild a JSON string from a broken key and its value.
    We will try a few heuristics:
    - If key starts with '{"' and ends with no closing brace, combine with value.
    - Replace single quotes -> double quotes where reasonable.
    - Ensure balanced braces.
    Returns parsed dict or None.
    """
    # quick join
    candidate = bad_key
    # if the bad_key is actually like '{"id"' (truncated) and val contains remainder, stitch:
    if bad_key.strip().endswith('"') or bad_key.strip().endswith("'"):
        candidate = bad_key + bad_val
    else:
        candidate = bad_key + ("" if bad_val is None else (" " + bad_val))

    # cleanup common issues
    s = candidate.strip()
    # if it looks like JSON with single quotes, convert to double quotes (best-effort)
    if "'" in s and '"' not in s:
        s = s.replace("'", '"')
    # try to find first '{' and last '}' and extract
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s2 = s[start:end+1]
    else:
        s2 = s
    # try to balance braces by adding closing brace(s)
    open_braces = s2.count("{")
    close_braces = s2.count("}")
    if open_braces > close_braces:
        s2 = s2 + "}" * (open_braces - close_braces)
    try:
        return json.loads(s2)
    except Exception:
        # last attempt: remove trailing commas, control chars
        s3 = re.sub(r',\s*}', '}', s2)
        s3 = re.sub(r',\s*]', ']', s3)
        try:
            return json.loads(s3)
        except Exception:
            return None

report = []
fixed_count = 0
scanned = 0

for doc in coll.find():
    scanned += 1
    to_update = {}
    to_unset = []
    changed = False

    for k in list(doc.keys()):
        if not isinstance(k, str):
            continue
        if k.strip().startswith('{') or ('"' in k and ':' in k and k.strip().endswith('"')==False):
            val = doc.get(k)
            parsed = try_reconstruct_and_parse(k, val if isinstance(val, str) else "")
            if parsed and isinstance(parsed, dict):
                # merge parsed into doc (do not overwrite existing non-empty fields)
                for pk, pv in parsed.items():
                    if pk not in doc or doc.get(pk) in (None, "", []):
                        to_update[pk] = pv
                to_unset.append(k)
                changed = True

    if changed:
        update_ops = {}
        if to_update:
            update_ops["$set"] = to_update
        if to_unset:
            update_ops["$unset"] = {k: "" for k in to_unset}
        try:
            coll.update_one({"_id": doc["_id"]}, update_ops)
            fixed_count += 1
            report.append({
                "doc_id": str(doc["_id"]),
                "set": to_update,
                "unset": to_unset
            })
        except Exception as e:
            report.append({"doc_id": str(doc["_id"]), "error": str(e), "trace": traceback.format_exc()})

print(f"Scanned {scanned} docs, fixed {fixed_count} documents.")
with open("repair_report.json", "w", encoding="utf-8") as f:
    f.write(json_util.dumps(report, indent=2))
print("Report written to repair_report.json")
