# src/pipeline.py
from src.extractor import extract_text_from_file, detect_and_extract_chunks
from src.loader import save_chunks, get_current_schema, save_schema, save_evolution_log, save_data
from src.schema import SchemaInferer, SchemaEvolver
import json, csv, io, yaml
from typing import List, Dict, Any
from datetime import datetime
from bs4 import BeautifulSoup

def parse_chunk(chunk: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Parse a detected chunk into a list of record dicts.
    Handles json, csv, kv, yaml (multiple docs), html (simple table).
    If parsing yields no structured records, return a single raw-text record
    so the content is preserved.
    """
    content, ctype = chunk["content"], chunk["type"]
    records: List[Dict[str, Any]] = []

    try:
        if ctype == "json":
            data = json.loads(content)
            records = [data] if isinstance(data, dict) else (data or [])
        elif ctype == "csv":
            reader = csv.DictReader(io.StringIO(content))
            records = list(reader)
        elif ctype == "kv":
            rec = {}
            for line in content.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    rec[k.strip()] = v.strip()
            records = [rec] if rec else []
        elif ctype == "yaml":
            # Support multiple YAML documents separated by '---'
            docs = list(yaml.safe_load_all(content))
            for d in docs:
                if d is None:
                    continue
                if isinstance(d, dict):
                    records.append(d)
                elif isinstance(d, list):
                    for item in d:
                        if isinstance(item, dict):
                            records.append(item)
                        else:
                            records.append({"value": item})
                else:
                    records.append({"value": d})
        elif ctype == "html":
            soup = BeautifulSoup(content, "html.parser")
            rows = soup.find_all("tr")
            if rows:
                # find headers if present
                headers = []
                first = rows[0]
                ths = first.find_all("th")
                if ths:
                    headers = [th.get_text().strip() for th in ths]
                    data_rows = rows[1:]
                else:
                    # no header row; infer columns
                    first_tds = first.find_all(["td", "th"])
                    col_count = len(first_tds)
                    headers = [f"col_{i}" for i in range(col_count)]
                    data_rows = rows
                for row in data_rows:
                    cells = [td.get_text().strip() for td in row.find_all(["td", "th"])]
                    if len(cells) < len(headers):
                        cells += [""] * (len(headers) - len(cells))
                    records.append(dict(zip(headers, cells)))
    except yaml.YAMLError as e:
        # YAML parsing often fails for arbitrary text fragments; keep a concise warning
        print(f"Parse warning (yaml): {e}")
    except json.JSONDecodeError as e:
        print(f"Parse warning (json): {e}")
    except Exception as e:
        # general parse warning (keep short)
        print(f"Parse warning ({ctype}): {e}")

    # If no structured records were found, preserve the raw chunk as a single record
    if not records:
        snippet = content.strip()
        # Keep snippet reasonably sized
        if len(snippet) > 1000:
            snippet = snippet[:1000] + "..."
        records = [{"_raw": snippet, "_chunk_type": ctype}]

    return records

def run_pipeline(file_path: str, source_id: str):
    """
    Full pipeline run: extract text, detect chunks, parse chunks, infer schema,
    save chunks/records and schema/evolution logs.
    """
    print(f"Pipeline: {file_path} to {source_id}")
    text = extract_text_from_file(file_path)
    chunks = detect_and_extract_chunks(text)
    save_chunks(source_id, chunks)

    all_records: List[Dict[str, Any]] = []
    for chunk in chunks:
        parsed = parse_chunk(chunk)
        # normalize simple non-dict records and ensure dict shape
        for rec in parsed:
            if isinstance(rec, dict):
                all_records.append(rec)
            else:
                all_records.append({"value": rec})

    schema_guess = SchemaInferer.infer(all_records)
    current = get_current_schema(source_id)

    if current:
        new_schema, diff = SchemaEvolver.evolve(current, schema_guess, source_id)
        log = {
            "source_id": source_id,
            "from_version": current.get("version"),
            "to_version": new_schema["version"],
            "diff": diff,
            "timestamp": new_schema["generated_at"]
        }
        save_evolution_log(log)
    else:
        new_schema = {
            "schema_id": "schema_v1",
            "source_id": source_id,
            "version": 1,
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "compatible_dbs": ["mongodb", "postgresql"],
            "fields": schema_guess["fields"],
            "primary_key_candidates": schema_guess.get("primary_key_candidates", []),
            "migration_notes": None
        }

    save_schema(new_schema)
    save_data(source_id, all_records)
    print(f"Saved {len(all_records)} records, schema v{new_schema['version']}")
