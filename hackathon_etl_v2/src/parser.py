import json
import csv
from io import StringIO
from bs4 import BeautifulSoup
import yaml
from typing import Any, List, Dict

def parse_chunk(lines: List[str], detected_type: str) -> Any:
    """Parse chunk based on type. Returns structured data (list/dict)."""
    text = "\n".join(lines).strip()
    if not text:
        return None

    try:
        if detected_type == "json":
            return json.loads(text)
        elif detected_type == "yaml":
            return yaml.safe_load(text)
        elif detected_type == "csv":
            reader = csv.DictReader(StringIO(text))
            return list(reader)
        elif detected_type == "html":
            soup = BeautifulSoup(text, "html.parser")
            table = soup.find("table")
            if table:
                headers = [th.get_text().strip() for th in table.find_all("th")]
                rows = []
                for tr in table.find_all("tr"):
                    row = [td.get_text().strip() for td in tr.find_all("td")]
                    if row:
                        rows.append(dict(zip(headers, row)))
                return rows
            return text  # Fallback to text if no table
        elif detected_type == "kv":
            kv = {}
            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    kv[key.strip()] = value.strip()
            return kv
        elif detected_type == "raw_text":
            return {"text": text}  # Wrap raw text
        else:
            raise ValueError(f"Unknown type: {detected_type}")
    except Exception as e:
        print(f"Parse error for {detected_type}: {e}")
        return {"raw": text, "error": str(e)}  # Fallback