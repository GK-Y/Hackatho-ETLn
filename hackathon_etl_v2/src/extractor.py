# src/extractor.py
import os
import re
from typing import List, Dict, Any
from src.config import config

def extract_text_from_file(file_path: str) -> str:
    """
    Return the main text contents of supported files.
    - .pdf -> uses PyPDF2 to extract pages' text
    - .html -> reads file and uses BeautifulSoup to extract visible text
    - .txt/.md -> plain text read
    Raises ValueError for unsupported extensions.
    """
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    if ext not in config.SUPPORTED_FILE_TYPES:
        raise ValueError(f"Unsupported file type: {ext}")

    if ext == ".pdf":
        try:
            from PyPDF2 import PdfReader
        except Exception as e:
            raise RuntimeError("PyPDF2 is required to read PDF files") from e
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    if ext == ".html":
        # lightweight HTML text extraction using BeautifulSoup
        try:
            from bs4 import BeautifulSoup
        except Exception as e:
            raise RuntimeError("beautifulsoup4 is required to read HTML files") from e
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()
        soup = BeautifulSoup(raw, "html.parser")
        # remove script/style content first
        for s in soup(["script", "style"]):
            s.decompose()
        text = soup.get_text(separator="\n")
        # compress multiple blank lines
        text = re.sub(r'\n\s*\n+', '\n\n', text).strip()
        return text

    # default: text/markdown
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        return f.read()

def detect_and_extract_chunks(text: str) -> List[Dict[str, Any]]:
    """
    Detect chunks in the given text using regex patterns defined in config.CHUNK_PATTERNS.
    Returns a sorted list of chunks: each chunk is {type, content, start, end}
    """
    chunks: List[Dict[str, Any]] = []
    # iterate through configured patterns
    for name, pattern in config.CHUNK_PATTERNS.items():
        try:
            for match in re.finditer(pattern, text, re.MULTILINE | re.DOTALL):
                chunk = {
                    "type": name,
                    "content": match.group(0).strip(),
                    "start": match.start(),
                    "end": match.end()
                }
                chunks.append(chunk)
        except re.error:
            # skip invalid pattern (shouldn't happen) and continue
            continue

    # If no chunks found, return one raw chunk for the whole text
    if not chunks:
        return [{"type": "raw", "content": text.strip(), "start": 0, "end": len(text)}]

    # sort chunks by start index to preserve order in text
    chunks = sorted(chunks, key=lambda x: x["start"])

    # merge overlapping or immediately adjacent chunks of the same type
    merged: List[Dict[str, Any]] = []
    for ch in chunks:
        if merged and ch["type"] == merged[-1]["type"] and ch["start"] <= merged[-1]["end"] + 1:
            # extend previous chunk
            merged[-1]["content"] += "\n\n" + ch["content"]
            merged[-1]["end"] = max(merged[-1]["end"], ch["end"])
        else:
            merged.append(ch)
    return merged
