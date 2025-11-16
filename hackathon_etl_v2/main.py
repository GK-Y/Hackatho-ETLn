# main.py
import sys
from src.pipeline import run_pipeline

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <file> <source_id>")
        sys.exit(1)
    run_pipeline(sys.argv[1], sys.argv[2])