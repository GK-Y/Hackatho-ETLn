# test_harness.py
# Simple harness to POST all test files to the running ETL API (Windows-friendly)
import requests, os, time

# Use the script's directory so the harness works no matter where it's run from
folder = os.path.dirname(os.path.abspath(__file__))

# Find files in the folder (ignore zip files and the harness itself)
files = [f for f in os.listdir(folder)
         if os.path.isfile(os.path.join(folder, f))
         and not f.endswith('.zip')
         and f != os.path.basename(__file__)]

url = "http://127.0.0.1:8000/upload"

for fname in files:
    path = os.path.join(folder, fname)
    print(f"Uploading: {fname}")
    try:
        with open(path, 'rb') as fh:
            r = requests.post(url, files={'file': (fname, fh)}, data={'source_id':'test_source'})
        print("  Status:", r.status_code)
        try:
            print("  JSON:", r.json())
        except Exception:
            print("  Response text:", r.text)
    except Exception as e:
        print("  Error uploading", fname, e)
    time.sleep(0.5)
