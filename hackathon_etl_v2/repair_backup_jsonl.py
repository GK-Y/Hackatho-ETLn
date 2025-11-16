# repair_backup_jsonl.py
# Conservative repair of a possibly-broken JSONL backup file.
# - Tries json.loads on each line.
# - If parsing fails, attempts to extract JSON substrings and parse them.
# - If substrings parse to dict, merges them into the resulting doc under "salvaged_json".
# - If not parseable or ambiguous, writes a doc with {"_raw_line": <original>, "salvaged_json": [...]}.
#
# Usage (from repo root with venv active):
# (venv) python repair_backup_jsonl.py "C:\Hackathon\backups\data_test_source.json" "C:\Hackathon\backups\data_test_source_repaired.jsonl"
#
import sys, json, re
from pathlib import Path

JSON_RE = re.compile(r'(\{(?:[^{}]|\{[^}]*\})*?\}|\[(?:[^\[\]]|\[[^\]]*\])*\])', re.DOTALL)

def try_load_json(s):
    try:
        return json.loads(s), None
    except Exception as e:
        return None, str(e)

def extract_json_substrings(s):
    found = []
    for m in JSON_RE.finditer(s):
        txt = m.group(1)
        parsed, err = try_load_json(txt)
        if parsed is not None:
            found.append(parsed)
    return found

def repair_line(line):
    line = line.strip()
    if not line:
        return None, "empty"
    parsed, err = try_load_json(line)
    if parsed is not None:
        return parsed, "ok"
    # fallback: try to salvage json substrings inside the line
    substrings = extract_json_substrings(line)
    if substrings:
        # if one of the substrings is a dict and seems to be the embedded object, prefer it
        obj = {}
        salv = []
        for s in substrings:
            if isinstance(s, dict):
                # merge keys into obj (if collisions, later keys win)
                obj.update(s)
            else:
                salv.append(s)
        if obj:
            # try to extract top-level fields from remaining text by naive split of top-level key:value pairs
            # but we avoid aggressive merging; just produce an object with salvaged_json
            res = {"salvaged_json": {"merged_object": obj}}
            if salv:
                res["salvaged_json"]["other"] = salv
            # also store original line for audit
            res["_raw_line"] = line
            return res, "salvaged_merged"
        else:
            # no dict found, produce salvage list
            res = {"salvaged_json": substrings, "_raw_line": line}
            return res, "salvaged_list"
    # last resort: heuristic attempt to fix malformed key-like fragments
    # Try to find a pattern like "\"{\"id\"": followed by a value ending with } and reconstruct object
    m = re.search(r'\"(\{[^"]+)\"\s*:\s*(.+)$', line)
    if m:
        # attempt crude reconstruction: join the quoted brace-start and trailing token up to last brace
        try:
            # take the part from first { to last } in the line
            start = line.find('{')
            end = line.rfind('}')
            if start != -1 and end != -1 and end > start:
                candidate = line[start:end+1]
                parsed_cand, err2 = try_load_json(candidate)
                if parsed_cand is not None:
                    res = {"salvaged_json": [parsed_cand], "_raw_line": line}
                    return res, "heuristic_braces"
        except Exception:
            pass
    # nothing salvageable by heuristics — return raw wrapper
    return {"_raw_line": line}, "raw_only"

def main(in_path, out_path):
    in_path = Path(in_path)
    out_path = Path(out_path)
    if not in_path.exists():
        print(f"Input file not found: {in_path}")
        sys.exit(2)
    stats = {"total":0, "ok":0, "salvaged_merged":0, "salvaged_list":0, "heuristic_braces":0, "raw_only":0, "empty":0}
    with in_path.open("r", encoding="utf-8", errors="replace") as inf, out_path.open("w", encoding="utf-8") as outf:
        for ln in inf:
            stats["total"] += 1
            doc, tag = None, None
            try:
                doc, tag = repair_line(ln)
            except Exception as e:
                doc = {"_raw_line": ln.strip(), "repair_error": str(e)}
                tag = "raw_only"
            if doc is None:
                stats["empty"] += 1
                continue
            # ensure it's a dict (if parsed is primitive, wrap it)
            if not isinstance(doc, dict):
                doc = {"value": doc}
            outf.write(json.dumps(doc, ensure_ascii=False) + "\n")
            stats[tag] = stats.get(tag, 0) + 1
    print("Wrote repaired JSONL to:", out_path)
    print("Stats:", json.dumps(stats, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python repair_backup_jsonl.py <input.json> <output.jsonl>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
