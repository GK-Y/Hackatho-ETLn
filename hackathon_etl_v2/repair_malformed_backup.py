# repair_malformed_backup.py
"""
Targeted repair: fix lines where a malformed key contains '{' and its value
is a string holding the rest of an object (e.g. key='"{"id""' and value='4, "name": ... }').

Behavior:
- Reads an input JSONL file (first arg) and writes an output JSONL (second arg).
- For each document, if it contains any keys with '{' or '}' or unbalanced quotes,
  it attempts to reconstruct a JSON substring by concatenating key + ":" + value,
  wrapping in braces if needed, then json.loads() it.
- If parsing succeeds and yields a dict, the script merges parsed fields into the parent doc,
  removes the malformed key, and records the change in a report.
- If parsing doesn't succeed, the doc is left unchanged but noted in the report.
- Always writes output to a new file; original files are not overwritten.
"""
import sys, json, re
from pathlib import Path

# pattern: keys that contain braces or embedded quotes or look suspicious
SUSP_KEY_RE = re.compile(r'[\{\}]')

def try_reconstruct_from_key_value(key, val):
    """
    Attempt to create a JSON text from key + ':' + val and parse it.
    Returns parsed dict on success, else None.
    """
    if not isinstance(val, str):
        return None
    candidate = f'{json.dumps(key)}:{json.dumps(val)}'
    # candidate is now something like "\"{\"id\"\":\"4, \\\"name\\\": ... }\""
    # But simpler approach: build raw text using the raw substring pieces:
    # if key contains '{' we want to attempt to strip surrounding quotes from key and then attach ':' + val
    raw_key = key
    raw_val = val
    # Build candidate_text so that it likely becomes a JSON object: { <raw_key_without_quotes>: <raw_val> }
    # If raw_key already contains an opening brace, drop its leading quote characters for reconstruction.
    try:
        # remove leading/trailing double quotes if any (we are dealing with Python str keys)
        kk = raw_key
        # If key looks like '{"id"' (starts with '{'), then kk stays as-is
        # Build a candidate that ensures outer braces
        cand = kk + ":" + raw_val
        # Ensure it is wrapped with braces
        if not cand.strip().startswith("{"):
            cand = "{" + cand
        if not cand.strip().endswith("}"):
            cand = cand + "}"
        # Now try to parse; the cand may contain trailing commas or stray quotes; attempt a few relaxations
        for attempt in [cand,
                        cand.replace('\"\"', '"'),
                        re.sub(r',\s*}', '}', cand),  # remove trailing commas before }
                        re.sub(r'\"\s*,\s*\"', '","', cand)]:
            try:
                parsed = json.loads(attempt)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                continue
    except Exception:
        pass
    return None

def repair_file(input_path, output_path, report_path):
    input_path = Path(input_path)
    output_path = Path(output_path)
    report = {"fixed": [], "unchanged": [], "errors": []}
    total = 0
    with input_path.open("r", encoding="utf-8", errors="replace") as inf, \
         output_path.open("w", encoding="utf-8") as outf:
        for line in inf:
            total += 1
            line = line.rstrip("\n")
            if not line.strip():
                continue
            try:
                doc = json.loads(line)
            except Exception as e:
                # If the whole line isn't valid JSON (shouldn't happen in your repaired.jsonl because it parsed earlier)
                # wrap raw and continue
                report["errors"].append({"line_no": total, "reason": "not_json", "error": str(e), "line": line})
                try:
                    outf.write(json.dumps({"_raw_line": line}, ensure_ascii=False) + "\n")
                except Exception:
                    outf.write(json.dumps({"_raw_line": line[:1000]}, ensure_ascii=False) + "\n")
                continue

            changed = False
            changes = []
            # collect keys to inspect (list to avoid dict size change during loop)
            keys = list(doc.keys())
            for k in keys:
                # skip normal _id
                if k == "_id":
                    continue
                if SUSP_KEY_RE.search(k):
                    # suspicious key: try to reconstruct using this key + its value if value is string
                    val = doc.get(k)
                    parsed = try_reconstruct_from_key_value(k, val)
                    if parsed:
                        # merge parsed fields into doc, do not overwrite existing keys unless absent
                        merged = []
                        for pk, pv in parsed.items():
                            if pk not in doc:
                                doc[pk] = pv
                                merged.append(pk)
                        # remove the bad key
                        try:
                            del doc[k]
                        except KeyError:
                            pass
                        changed = True
                        changes.append({"bad_key": k, "merged_fields": merged})
            if changed:
                report["fixed"].append({"_id": str(doc.get("_id")), "changes": changes})
            else:
                report["unchanged"].append({"_id": str(doc.get("_id"))})
            # write out doc
            outf.write(json.dumps(doc, ensure_ascii=False) + "\n")
    # write report
    with open(report_path, "w", encoding="utf-8") as rf:
        json.dump({"total_lines": total, "report": report}, rf, indent=2, ensure_ascii=False)
    print("Repaired written to:", output_path)
    print("Report written to:", report_path)
    return report_path

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python repair_malformed_backup.py <input.jsonl> <output.jsonl>")
        sys.exit(1)
    inp = sys.argv[1]
    outp = sys.argv[2]
    rpt = Path(outp).with_name("repair_malformed_backup_report.json")
    repair_file(inp, outp, rpt)
