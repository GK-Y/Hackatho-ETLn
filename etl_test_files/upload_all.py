# upload_all.py
# Usage: python upload_all.py
# Posts every file in the current directory to http://127.0.0.1:8000/upload
# Sends multipart 'file' and form field 'source_id' (filename without extension)
# Retries up to 3 times on transient errors.

import os
import requests
import time
from pathlib import Path

BASE = "http://127.0.0.1:8000"
UPLOAD_ENDPOINT = f"{BASE}/upload"
DIR = Path(__file__).resolve().parent
RETRIES = 3
SLEEP_BETWEEN = 1.5  # seconds

def make_source_id(filename: str) -> str:
    # Basic normalize: remove spaces, lowercase, replace non-alnum with _
    name = Path(filename).stem
    safe = "".join(c if c.isalnum() else "_" for c in name).lower()
    # ensure not empty
    return safe or f"file_{int(time.time())}"

def upload_file(path: Path):
    sid = make_source_id(path.name)
    for attempt in range(1, RETRIES + 1):
        try:
            with open(path, "rb") as fh:
                files = {"file": (path.name, fh)}
                data = {"source_id": sid}
                resp = requests.post(UPLOAD_ENDPOINT, files=files, data=data, timeout=30)
            if resp.status_code == 200:
                try:
                    j = resp.json()
                except Exception:
                    j = {"raw": resp.text}
                print(f"[OK] {path.name} -> source_id={sid} | response: {j}")
                return True, j
            else:
                print(f"[ERR] {path.name} attempt {attempt} -> status {resp.status_code} {resp.text}")
        except requests.exceptions.RequestException as e:
            print(f"[ERR] {path.name} attempt {attempt} -> network error: {e}")
        if attempt < RETRIES:
            time.sleep(SLEEP_BETWEEN * attempt)
    return False, None

def main():
    print("Uploading files from", DIR)
    files = sorted([p for p in DIR.iterdir() if p.is_file()])
    if not files:
        print("No files found in folder.")
        return

    summary = {"ok": [], "failed": []}
    for p in files:
        print("Uploading:", p.name)
        ok, res = upload_file(p)
        if ok:
            summary["ok"].append({"file": p.name, "source_id": make_source_id(p.name), "resp": res})
        else:
            summary["failed"].append(p.name)

    print("\n=== Upload Summary ===")
    print("Succeeded:", len(summary["ok"]))
    for s in summary["ok"]:
        print(" -", s["file"], "->", s["source_id"])
    if summary["failed"]:
        print("Failed:", len(summary["failed"]))
        for f in summary["failed"]:
            print(" -", f)
    else:
        print("All files uploaded successfully.")

if __name__ == "__main__":
    main()
