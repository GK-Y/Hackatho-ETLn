# src/loader.py
import pymongo
from pymongo.errors import PyMongoError
from typing import List, Dict, Any
from src.config import config
from datetime import datetime, date
from decimal import Decimal

# Create client with a short server selection timeout for faster failure detection
try:
    client = pymongo.MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=5000)
    # Early ping to give a clear error if auth/connection fails
    client.admin.command('ping')
except PyMongoError as e:
    print("Mongo connection error:", e)
    raise

db = client[config.DATABASE_NAME]

def sanitize_value(v: Any) -> Any:
    """
    Convert non-BSON-serializable python objects to BSON/JSON-friendly types.
    - datetime / date -> ISO string
    - set -> list
    - Decimal -> str
    - bytes -> decoded str
    - dict/list -> recursively sanitize
    """
    # basic types that are already safe
    if v is None or isinstance(v, (str, int, float, bool)):
        return v

    # dates and datetimes -> ISO format strings
    if isinstance(v, (datetime, date)):
        # ensure datetime has timezone if needed; we keep plain isoformat
        return v.isoformat()

    # sets -> list
    if isinstance(v, set):
        return [sanitize_value(x) for x in sorted(list(v), key=lambda x: str(x))]

    # Decimal -> string (preserve precision)
    if isinstance(v, Decimal):
        return str(v)

    # bytes -> decode best-effort
    if isinstance(v, (bytes, bytearray)):
        try:
            return v.decode("utf-8")
        except Exception:
            return v.decode("utf-8", errors="replace")

    # dict -> sanitize recursively
    if isinstance(v, dict):
        return {str(k): sanitize_value(val) for k, val in v.items()}

    # list/tuple -> sanitize elements
    if isinstance(v, (list, tuple)):
        return [sanitize_value(x) for x in v]

    # fallback: try str()
    try:
        return str(v)
    except Exception:
        return repr(v)

def sanitize_doc(doc: Any) -> Any:
    """
    Recursively sanitize a document/document-like object (dict/list/scalar).
    """
    return sanitize_value(doc)

def save_chunks(source_id: str, chunks: List[Dict[str, Any]]):
    coll = db[config.CHUNKS_COLLECTION]
    docs = [{"source_id": source_id, **c} for c in chunks]
    docs = [sanitize_doc(d) for d in docs]
    if docs:
        coll.insert_many(docs)

def save_data(source_id: str, records: List[Dict[str, Any]]):
    coll_name = f"{config.DATA_COLLECTION_PREFIX}{source_id}"
    coll = db[coll_name]
    # sanitize each record before insert
    docs = [sanitize_doc(r) for r in records] if records else []
    if docs:
        coll.insert_many(docs)

def get_current_schema(source_id: str) -> Dict[str, Any]:
    coll = db[config.SCHEMA_REGISTRY_COLLECTION]
    return coll.find_one({"source_id": source_id}, sort=[("version", -1)])

def save_schema(schema: Dict[str, Any]):
    coll = db[config.SCHEMA_REGISTRY_COLLECTION]
    doc = sanitize_doc(schema)
    coll.insert_one(doc)

def save_evolution_log(log: Dict[str, Any]):
    coll = db[config.SCHEMA_EVOLUTION_LOG_COLLECTION]
    doc = sanitize_doc(log)
    coll.insert_one(doc)
