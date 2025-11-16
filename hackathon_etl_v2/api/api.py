# api/api.py  (debug-friendly - copy & paste - full file)
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from src.pipeline import run_pipeline
from src.loader import get_current_schema, db  # using your existing loader db connection
from src.config import config
import os, tempfile, traceback, json
from bson import json_util, ObjectId
from typing import Any, Dict, List
from datetime import datetime
import shutil
from pathlib import Path
from fastapi import Query

app = FastAPI()

# --- CORS middleware (development-friendly) ---
# Allow Vite dev server origins. If you prefer to allow everything in dev, set allow_origins=["*"]
origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    # add other local dev ports if needed
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
# --- end CORS middleware ---

def json_response(obj: Any) -> Response:
    text = json_util.dumps(obj)
    return Response(content=text, media_type="application/json")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    return """
    <h1>Dynamic ETL Dashboard</h1>
    <form action="/upload" enctype="multipart/form-data" method="post">
        File: <input name="file" type="file"><br>
        Source ID: <input name="source_id" value="test_source"><br>
        <input type="submit" value="Upload">
    </form>
    <hr>
    <a href="/schema?source_id=test_source">Schema</a> |
    <a href="/schema/history?source_id=test_source">History</a> |
    <a href="/records?source_id=test_source&query_id=1">Records</a>
    """

# Allowed extensions (include html)
ALLOWED_EXT = tuple(config.SUPPORTED_FILE_TYPES)

@app.post("/upload")
async def upload(file: UploadFile = File(...), source_id: str = "test_source"):
    fname = file.filename or ""
    if not any(fname.lower().endswith(e) for e in ALLOWED_EXT):
        raise HTTPException(400, "Invalid file type")
    tmp_dir = tempfile.mkdtemp()
    path = os.path.join(tmp_dir, fname)
    with open(path, "wb") as f:
        f.write(await file.read())

    # Run pipeline and capture exceptions for debugging
    try:
        run_pipeline(path, source_id)
    except Exception as e:
        tb = traceback.format_exc()
        # Return the error and traceback to the client to help debugging (dev only)
        # keep the temp file so debugging possible
        return JSONResponse(status_code=500, content={"error": str(e), "traceback": tb, "temp_path": path})

    try:
        # cleanup
        os.remove(path)
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass
    return {"status": "ok", "source_id": source_id}

@app.get("/schema")
async def get_schema(source_id: str):
    s = get_current_schema(source_id)
    if not s:
        raise HTTPException(404, "Not found")
    return json_response(s)

@app.get("/schema/history")
async def schema_history(source_id: str):
    docs = list(db[config.SCHEMA_REGISTRY_COLLECTION].find({"source_id": source_id}).sort("version", 1))
    return json_response(docs)

@app.get("/records")
async def get_records(source_id: str, query_id: int = 1, limit: int = 100, page: int = 0):
    coll_name = f"{config.DATA_COLLECTION_PREFIX}{source_id}"
    if coll_name not in db.list_collection_names():
        raise HTTPException(404, "Collection not found")
    skip = page * limit
    docs = list(db[coll_name].find().skip(skip).limit(limit))
    return json_response(docs)

@app.post("/query")
async def llm_query(source_id: str, nl_query: str):
    # dev: stub - return first 50 docs (LLM integration can happen later)
    coll_name = f"{config.DATA_COLLECTION_PREFIX}{source_id}"
    docs = []
    if coll_name in db.list_collection_names():
        docs = list(db[coll_name].find().limit(50))
    return json_response({"source_id": source_id, "nl_query": nl_query, "docs": docs})

#
# ---------------------------
# Admin / visualization endpoints added below
# ---------------------------
#

def _collection_name_for_source(source_id: str) -> str:
    return f"{config.DATA_COLLECTION_PREFIX}{source_id}"

def _schema_collection():
    return db[config.SCHEMA_REGISTRY_COLLECTION]

def _chunks_collection():
    return db[config.CHUNKS_COLLECTION]

def _schema_history_collection():
    return db[config.SCHEMA_EVOLUTION_LOG_COLLECTION]

@app.get("/sources")
async def api_get_sources():
    """
    Returns list of sources with record_count, last_ingest, schema_version, chunks count.
    """
    try:
        # derive distinct source_ids from schema_registry
        coll = _schema_collection()
        source_ids = coll.distinct("source_id")
        out = []
        for sid in source_ids:
            last_doc = coll.find({"source_id": sid}).sort("created_at", -1).limit(1)
            last_doc = next(last_doc, None)
            schema_version = last_doc.get("version") if last_doc else None
            last_ingest = last_doc.get("created_at") if last_doc else None
            data_coll = _collection_name_for_source(sid)
            record_count = int(db[data_coll].estimated_document_count()) if data_coll in db.list_collection_names() else 0
            chunk_count = int(_chunks_collection().count_documents({"source_id": sid}))
            out.append({
                "source_id": sid,
                "last_ingest": str(last_ingest) if last_ingest else None,
                "record_count": record_count,
                "schema_version": schema_version,
                "chunks": chunk_count
            })
        return JSONResponse(content=out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/visualize/summary")
async def api_visualize_summary(source_id: str):
    """
    Returns a compact summary used by the frontend:
      - chunk_types: [{type, count}, ...]
      - top_fields: [{field, count}, ...]
      - schema_history: [{version_label, field_count, created_at}, ...]
      - top_tokens: [{token, count}, ...]  (optional collection visual_tokens_<source_id>)
    """
    try:
        # chunk type distribution
        chunks_coll = _chunks_collection()
        pipeline = [
            {"$match": {"source_id": source_id}},
            {"$group": {"_id": "$type", "count": {"$sum": 1}}},
            {"$project": {"type": "$_id", "count": 1, "_id": 0}}
        ]
        chunk_types = list(chunks_coll.aggregate(pipeline))

        # top fields: try latest schema first
        schema_coll = _schema_collection()
        latest_cursor = schema_coll.find({"source_id": source_id}).sort("created_at", -1).limit(1)
        latest = next(latest_cursor, None)
        top_fields = []
        if latest and latest.get("fields"):
            fields = latest.get("fields")
            # fields might be dict {field: {presence: N, type: 'string', example: ...}}
            for k, v in fields.items():
                if isinstance(v, dict):
                    cnt = v.get("presence") or v.get("count") or 1
                else:
                    cnt = 1
                top_fields.append({"field": k, "count": int(cnt)})
            top_fields = sorted(top_fields, key=lambda x: -x["count"])[:30]
        else:
            # fallback: sample documents and count keys
            data_coll = _collection_name_for_source(source_id)
            if data_coll in db.list_collection_names():
                sample_cursor = db[data_coll].aggregate([{"$sample": {"size": 300}}])
                counts = {}
                for d in sample_cursor:
                    for k in d.keys():
                        counts[k] = counts.get(k, 0) + 1
                top_fields = [{"field": k, "count": v} for k, v in sorted(counts.items(), key=lambda x: -x[1])[:30]]

        # schema history (versions)
        hist = []
        for doc in schema_coll.find({"source_id": source_id}).sort("created_at", 1):
            hist.append({
                "version_label": f"v{doc.get('version')}",
                "field_count": len(doc.get("fields", {})) if doc.get("fields") else 0,
                "created_at": str(doc.get("created_at"))
            })

        # top tokens (optional precomputed collection named visual_tokens_<source_id>)
        token_coll_name = f"visual_tokens_{source_id}"
        top_tokens = []
        if token_coll_name in db.list_collection_names():
            top_tokens = list(db[token_coll_name].find().sort("count", -1).limit(200))
        # normalize types for JSON
        return JSONResponse(content={
            "chunk_types": chunk_types,
            "top_fields": top_fields,
            "schema_history": hist,
            "top_tokens": top_tokens
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/backup")
async def api_backup(source_id: str, background_tasks: BackgroundTasks = None):
    """
    Returns a safe mongodump command string for the given source_id and (optionally) starts a background dump.
    By default this returns the command to run on the host -- safer than executing directly inside the container.
    """
    try:
        coll = _collection_name_for_source(source_id)
        if coll not in db.list_collection_names():
            raise HTTPException(status_code=404, detail="Source collection not found")

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backups_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "backups"))
        os.makedirs(backups_dir, exist_ok=True)
        outpath = os.path.join(backups_dir, f"{source_id}_backup_{timestamp}.gz")

        # Build mongodump command string using config.MONGO_URI and config.DATABASE_NAME
        # This returns a command that the user can run locally (PowerShell friendly).
        cmd = f'mongodump --uri="{config.MONGO_URI}" --db={config.DATABASE_NAME} --collection={coll} --archive="{outpath}" --gzip'

        # Optionally: if environment allows, we could run mongodump here. For safety we don't by default.
        # If you want to run it from the server, uncomment below (not recommended for local dev demo).
        # import subprocess
        # proc = subprocess.Popen(cmd, shell=True)
        # background_tasks.add_task(proc.wait)

        return JSONResponse(content={"command": cmd, "backup_path_suggested": outpath, "started_background": False})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Use config.TEST_FILES_DIR if present, otherwise fallback to default path
TEST_FILES_DIR = getattr(config, "TEST_FILES_DIR", None) or r"C:\Hackathon\etl_test_files"

@app.get("/test-files")
async def api_list_test_files():
    """
    Lists files in the test files directory for the frontend dropdown.
    Returns [{name, size, mtime}, ...]
    """
    try:
        base = Path(TEST_FILES_DIR)
        if not base.exists() or not base.is_dir():
            return JSONResponse(content=[])
        out = []
        for p in sorted(base.iterdir(), key=lambda x: x.name):
            if p.is_file():
                out.append({"name": p.name, "size": p.stat().st_size, "mtime": p.stat().st_mtime})
        return JSONResponse(content=out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/process-file")
async def api_process_file(filename: str = Query(..., description="Filename within the test files dir"), background_tasks: BackgroundTasks = None):
    """
    Trigger server-side processing of a file that already exists in TEST_FILES_DIR.
    This does not accept arbitrary paths — it's limited to TEST_FILES_DIR children.
    Returns {status: started, source_id, message}
    """
    try:
        base = Path(TEST_FILES_DIR).resolve()
        target = (base / filename).resolve()
        # Prevent path traversal: target must be inside base
        if not str(target).startswith(str(base)):
            raise HTTPException(status_code=400, detail="Invalid filename")
        if not target.exists() or not target.is_file():
            raise HTTPException(status_code=404, detail="File not found")
        # Derive source_id from filename stem
        source_id = "".join(c if c.isalnum() else "_" for c in target.stem).lower() or f"file_{int(datetime.utcnow().timestamp())}"
        # Run pipeline in background so we return immediately
        background_tasks.add_task(run_pipeline, str(target), source_id)
        return JSONResponse(content={"status": "started", "source_id": source_id, "filename": filename})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/dataset")
async def api_delete_dataset(source_id: str, confirm: int = 0):
    """
    Safe delete: moves data_<source_id> to quarantine_{source_id}_{ts}.
    Requires confirm=1 to run. User must run backup first.
    """
    if confirm != 1:
        raise HTTPException(status_code=400, detail="Deletion requires confirm=1 and a prior backup.")

    try:
        src = _collection_name_for_source(source_id)
        if src not in db.list_collection_names():
            raise HTTPException(status_code=404, detail="Source collection not found")
        ts = int(datetime.utcnow().timestamp())
        tgt = f"quarantine_{source_id}_{ts}"
        # renameCollection is atomic in MongoDB
        db[src].rename(tgt)
        return JSONResponse(content={"status": "ok", "moved_to": tgt})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
