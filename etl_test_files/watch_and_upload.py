# watch_and_upload.py
# Usage: python watch_and_upload.py
# Polls the folder every N seconds, and uploads new files that are stable (size unchanged across two polls).
# Conservative default: check every 3 seconds, requires size stable for 2 checks.

import time
import requests
from pathlib import Path
import sys

BASE = "http://127.0.0.1:8000"
UPLOAD_ENDPOINT = f"{BASE}/upload"
DIR = Path(__file__).resolve().parent
POLL = 3
STABLE_ROUNDS = 2

def source_id(name):
    s = Path(name).stem
    return "".join(c if c.isalnum() else "_" for c in s).lower() or f"file_{int(time.time())}"

def is_file_stable(p: Path, rounds=STABLE_ROUNDS, poll=POLL):
    last_size = -1
    for _ in range(rounds):
        try:
            size = p.stat().st_size
        except FileNotFoundError:
            return False
        if last_size == -1:
            last_size = size
        else:
            if size != last_size:
                return False
            last_size = size
        time.sleep(poll)
    return True

def upload(p: Path):
    sid = source_id(p.name)
    try:
        with open(p, "rb") as fh:
            files = {"file": (p.name, fh)}
            data = {"source_id": sid}
            r = requests.post(UPLOAD_ENDPOINT, files=files, data=data, timeout=30)
        if r.status_code == 200:
            print(f"[UPLOAD OK] {p.name} -> {sid}")
            return True
        else:
            print(f"[UPLOAD ERR] {p.name} -> {r.status_code} {r.text}")
            return False
    except Exception as e:
        print(f"[UPLOAD EXC] {p.name} -> {e}")
        return False

def main():
    print(f"Watching {DIR} for new files. Poll every {POLL}s.")
    seen = set(p.name for p in DIR.iterdir() if p.is_file())
    try:
        while True:
            current = set()
            for p in DIR.iterdir():
                if not p.is_file():
                    continue
                current.add(p.name)
                if p.name in seen:
                    continue
                print("Detected new file:", p.name)
                # Check stability
                if is_file_stable(p):
                    print("File stable, uploading:", p.name)
                    ok = upload(p)
                    if ok:
                        seen.add(p.name)
                    else:
                        print("Upload failed; will retry on next detection.")
                else:
                    print("File not yet stable; will check later.")
            # handle removed files from seen set
            removed = seen - current
            if removed:
                for r in removed:
                    seen.remove(r)
            time.sleep(POLL)
    except KeyboardInterrupt:
        print("Stopping watcher.")
        sys.exit(0)

if __name__ == "__main__":
    main()
