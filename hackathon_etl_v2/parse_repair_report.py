# parse_repair_report.py
import json
from pathlib import Path
import sys

REPORT_PATH = Path(r"C:\Hackathon\hackathon_etl_v2\repair_special_keys_report.json")

def load_report(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"ERROR: failed to read/parse report: {e}")
        sys.exit(2)

def extract_id(entry):
    # common _id representations
    for k in ("_id","id","doc_id","document_id","oid"):
        if k in entry:
            return entry[k]
    # sometimes id inside nested dict
    if isinstance(entry, dict):
        for v in entry.values():
            if isinstance(v, dict) and "_id" in v:
                return v.get("_id")
    return "<unknown-id>"

def summarize_repaired(repaired_list):
    print("=== Repaired documents ===")
    if not repaired_list:
        print("None")
        return
    for i, entry in enumerate(repaired_list, 1):
        docid = extract_id(entry)
        print(f"\n{ i }. Document id: {docid}")
        # Try to find common shapes
        #  - entry may be { "doc_id": "...", "changes": {"set": {...}, "unset": [...]} }
        #  - or { "_id": "...", "set": {...}, "unset": [...] }
        changes = entry.get("changes") if isinstance(entry, dict) else None
        set_fields = None
        unset_fields = None
        if changes:
            set_fields = changes.get("set")
            unset_fields = changes.get("unset")
        else:
            set_fields = entry.get("set") or entry.get("fields_set") or entry.get("updated_fields")
            unset_fields = entry.get("unset") or entry.get("fields_unset") or entry.get("removed_fields")
        # fallback: sometimes a 'before' and 'after' are included
        before = entry.get("before")
        after = entry.get("after")

        if set_fields:
            print("  Fields SET:")
            if isinstance(set_fields, dict):
                for k,v in set_fields.items():
                    print(f"    + {k!r}: {v!r}")
            else:
                print(f"    + {set_fields!r}")
        if unset_fields:
            print("  Fields UNSET:")
            if isinstance(unset_fields, (list,tuple)):
                for k in unset_fields:
                    print(f"    - {k!r}")
            else:
                print(f"    - {unset_fields!r}")

        if before is not None or after is not None:
            print("  Snapshot diff:")
            if before is not None:
                print("    before:", json.dumps(before, indent=4, ensure_ascii=False))
            if after is not None:
                print("    after: ", json.dumps(after, indent=4, ensure_ascii=False))

        # If report provided a 'note' or 'message'
        note = entry.get("note") or entry.get("message") or entry.get("status")
        if note:
            print(f"  Note: {note}")

def summarize_failed(failed_list):
    print("\n=== Failed documents ===")
    if not failed_list:
        print("None")
        return
    for i, entry in enumerate(failed_list, 1):
        docid = extract_id(entry) if isinstance(entry, dict) else entry
        reason = entry.get("reason") if isinstance(entry, dict) else None
        print(f"\n{ i }. Document id: {docid}")
        if reason:
            print(f"  Reason: {reason}")
        # dump raw entry for manual inspection
        print("  Raw entry:")
        print(json.dumps(entry, indent=2, ensure_ascii=False))

def main():
    report = load_report(REPORT_PATH)
    # common report shapes:
    # 1) {"repaired": [...], "failed": [...], "summary": {...}}
    # 2) [{"_id":..., "set":..., "unset":...}, ...]  -- list of repaired entries
    # 3) {"repaired_count": n, "repaired_docs": [...], ...}
    repaired = None
    failed = None

    if isinstance(report, dict):
        repaired = report.get("repaired") or report.get("repaired_docs") or report.get("fixed") or report.get("fixed_docs")
        failed = report.get("failed") or report.get("failed_docs") or report.get("errors") or []
        # fallback: sometimes report directly lists actions under "actions"
        if repaired is None and "actions" in report:
            repaired = report["actions"].get("repaired") or []
    elif isinstance(report, list):
        # assume list == repaired
        repaired = report
        failed = []
    else:
        print("Unknown report format. Raw report:")
        print(json.dumps(report, indent=2, ensure_ascii=False))
        sys.exit(3)

    # normalize
    repaired = repaired or []
    failed = failed or []

    summarize_repaired(repaired)
    summarize_failed(failed)

    print("\n=== Summary ===")
    print(f"Total repaired: {len(repaired)}")
    print(f"Total failed: {len(failed)}")

if __name__ == "__main__":
    main()
