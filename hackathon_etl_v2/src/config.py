# src/config.py
from typing import List, Dict

class Config:
    # allow html as an input type for scraped pages
    SUPPORTED_FILE_TYPES: List[str] = [".txt", ".pdf", ".md", ".html"]
    CHUNK_PATTERNS: Dict[str, str] = {
        "json": r"\{.*?\}(?=\s*\{|$|\n\n)",
        "html": r"<[^>]+>.*?</[^>]+>",
        "csv": r"^[^,\n]+(,[^,\n]+)+$",
        "kv": r"^([^:]+):\s*(.+)$",
        "yaml": r"^\s*[a-zA-Z0-9_]+:\s*.+$"
    }

    # Dev-friendly default (root/admin)
    MONGO_URI = "mongodb://hackathon:password123@localhost:27017/?authSource=admin"

    DATABASE_NAME = "hackathon_db"
    CHUNKS_COLLECTION = "chunks"
    SCHEMA_REGISTRY_COLLECTION = "schema_registry"
    SCHEMA_EVOLUTION_LOG_COLLECTION = "schema_evolution_log"
    DATA_COLLECTION_PREFIX = "data_"

config = Config()
