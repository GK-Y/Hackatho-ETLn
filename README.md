# Hackathon Dynamic ETL

# !! Please clone it into windows C drive !!

## Setup
1. Create venv: `python -m venv venv`
2. Run start.ps1 (Windows)
3. Access dashboard at http://localhost:8000

## Features
- Upload files via POST /upload (multipart, with source_id)
- Schema evolution on repeated uploads for same source_id
- Dashboard shows chunks, timeline, diffs
- Handles .txt, .pdf, .md with mixed JSON/CSV/HTML/KV/YAML/raw
- Low resource usage

## Demo
Upload the sample combined.txt multiple times with changes to see evolution.
